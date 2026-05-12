"""
실습 2: MCP 도구를 사용하는 AI 에이전트

MCP 서버(날씨)를 로컬 서브프로세스(stdio)로 실행하고,
Azure OpenAI 모델에 MCP 도구를 연결하여
AI가 도구를 자율적으로 호출하도록 합니다.

이 스크립트는 MCP 클라이언트와 Azure OpenAI의 Function Calling을
조합하여 "AI 에이전트 + 외부 도구" 패턴을 시연합니다.
"""

import asyncio
import json
import os
import sys

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AzureOpenAI

# ============================================================
# 환경 변수 로드 (상위 디렉토리의 .env 파일)
# ============================================================
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# 필수 환경 변수 확인
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv(
    "MODEL_DEPLOYMENT_NAME", "gpt-4o"
)

if not AZURE_OPENAI_ENDPOINT:
    print(
        "오류: AZURE_OPENAI_ENDPOINT 환경 변수가 설정되지 않았습니다.\n"
        "상위 디렉토리의 .env 파일에 Azure OpenAI 엔드포인트를 추가하세요.\n"
        "예: AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/"
    )
    sys.exit(1)


def mcp_tools_to_openai(tools) -> list[dict]:
    """MCP 도구 목록을 OpenAI Function Calling 형식으로 변환합니다."""
    openai_tools = []
    for tool in tools:
        openai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
        )
    return openai_tools


async def run_agent_with_mcp():
    """MCP 서버에 연결하고, AI 에이전트가 도구를 사용하여 답변하도록 합니다."""

    print("🤖 MCP 도구를 사용하는 AI 에이전트")
    print("=" * 60)

    # ============================================================
    # 1단계: MCP 서버를 자식 프로세스로 실행 준비
    # StdioServerParameters로 서버 실행 명령을 지정합니다.
    # ============================================================
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[
            os.path.join(
                os.path.dirname(__file__), "mcp_server", "weather_server.py"
            )
        ],
    )

    print("\n📡 MCP 서버에 연결 중...")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("✅ MCP 서버 연결 성공!")

            # ============================================================
            # 2단계: MCP 도구를 자동 발견하고 OpenAI 형식으로 변환
            # MCP의 핵심: 서버가 제공하는 도구를 클라이언트가 자동으로 발견합니다.
            # ============================================================
            tools_result = await session.list_tools()
            openai_tools = mcp_tools_to_openai(tools_result.tools)
            print(
                f"📋 MCP에서 발견된 도구: "
                f"{', '.join(t.name for t in tools_result.tools)}"
            )

            # ============================================================
            # 3단계: Azure OpenAI 클라이언트 생성
            # DefaultAzureCredential으로 Entra ID 토큰을 발급받아 인증합니다.
            # ============================================================
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            openai_client = AzureOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                azure_ad_token_provider=token_provider,
                api_version="2024-12-01-preview",
            )
            print("✅ Azure OpenAI 클라이언트 생성 완료")

            # ============================================================
            # 4단계: 사용자 질문 전송 + Function Calling 루프
            # 모델이 도구 호출을 요청하면 MCP 서버로 전달하고,
            # 결과를 다시 모델에 보내는 루프를 반복합니다.
            # ============================================================
            user_question = "서울과 부산의 날씨를 비교해주세요"
            print(f'\n💬 사용자 질문: "{user_question}"')
            print("⏳ AI 에이전트 실행 중...\n")

            messages = [
                {
                    "role": "system",
                    "content": (
                        "당신은 날씨 정보를 제공하는 도움이 되는 어시스턴트입니다. "
                        "MCP 서버의 날씨 도구를 활용하여 정확하고 친절하게 답변하세요. "
                        "한국어로 응답하세요."
                    ),
                },
                {"role": "user", "content": user_question},
            ]

            response = openai_client.chat.completions.create(
                model=MODEL_DEPLOYMENT_NAME,
                messages=messages,
                tools=openai_tools,
            )

            # Function Calling 루프: 모델이 도구 호출을 요청하는 동안 반복
            while response.choices[0].message.tool_calls:
                assistant_msg = response.choices[0].message
                messages.append(assistant_msg)

                for tool_call in assistant_msg.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    print(f"  🔧 도구 호출: {func_name}({func_args})")

                    # MCP 서버에 도구 실행 요청
                    mcp_result = await session.call_tool(
                        func_name, arguments=func_args
                    )
                    tool_output = mcp_result.content[0].text
                    print(f"  📍 결과: {tool_output}")

                    # 도구 결과를 대화에 추가
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_output,
                        }
                    )

                # 도구 결과를 포함하여 모델에 다시 요청
                response = openai_client.chat.completions.create(
                    model=MODEL_DEPLOYMENT_NAME,
                    messages=messages,
                    tools=openai_tools,
                )

            # ============================================================
            # 5단계: 최종 응답 출력
            # ============================================================
            final_answer = response.choices[0].message.content
            print(f"\n📨 에이전트 응답:\n{final_answer}")

    print("\n✅ MCP 에이전트 실습 완료!")


# ============================================================
# 메인 실행 블록
# ============================================================
if __name__ == "__main__":
    asyncio.run(run_agent_with_mcp())
