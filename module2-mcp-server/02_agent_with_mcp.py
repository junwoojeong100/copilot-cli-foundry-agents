"""
실습 2: MCP 도구를 사용하는 Foundry Agent

Azure AI Foundry Agent에 MCP 서버를 연결하여
AI가 날씨 도구를 사용할 수 있도록 합니다.
"""

import os
import time

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MCPTool, MessageRole
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# ============================================================
# 환경 변수 로드 (상위 디렉토리의 .env 파일)
# ============================================================
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# 필수 환경 변수 확인
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o")

if not PROJECT_ENDPOINT:
    raise ValueError(
        "PROJECT_ENDPOINT 환경 변수가 설정되지 않았습니다. "
        "상위 디렉토리의 .env 파일을 확인하세요."
    )


def main():
    """MCP 도구를 사용하는 Foundry Agent를 생성하고 실행합니다."""

    print("🤖 MCP 도구를 사용하는 Foundry Agent")
    print("=" * 60)

    # ============================================================
    # 1단계: Azure AI Project 클라이언트 생성
    # DefaultAzureCredential은 az login, 환경 변수, 관리 ID 등
    # 다양한 인증 방법을 자동으로 시도합니다.
    # ============================================================
    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )
    print("✅ Azure AI Project 클라이언트 생성 완료")

    # ============================================================
    # 2단계: MCP 도구 설정
    # MCPTool로 MCP 서버의 위치를 지정합니다.
    # server_label: Agent가 이 도구를 식별하는 이름
    # server_url: MCP 서버의 HTTP 엔드포인트 URL
    #
    # ⚠️ 주의: 이 스크립트를 실행하기 전에 MCP 서버가
    #    http://localhost:8080/mcp 에서 실행 중이어야 합니다.
    # ============================================================
    print("\n🔧 MCP 도구 설정 중...")
    mcp_tool = MCPTool(
        server_label="weather",
        server_url="http://localhost:8080/mcp",
    )
    print("  📡 MCP 서버 연결: http://localhost:8080/mcp")

    agent = None
    thread = None

    try:
        # ============================================================
        # 3단계: Agent 생성
        # MCP 도구를 포함하여 Agent를 생성합니다.
        # Agent는 사용자의 질문에 따라 MCP 서버의 도구를 자동으로 호출합니다.
        # ============================================================
        agent = project.agents.create_agent(
            model=MODEL_DEPLOYMENT_NAME,
            name="날씨-에이전트",
            instructions=(
                "당신은 날씨 정보를 제공하는 도움이 되는 어시스턴트입니다. "
                "MCP 서버의 날씨 도구를 활용하여 사용자의 날씨 관련 질문에 "
                "정확하고 친절하게 답변하세요. 한국어로 응답하세요."
            ),
            tools=[mcp_tool],
        )
        print(f"🤖 Agent 생성 완료: {agent.id}")

        # ============================================================
        # 4단계: 대화 스레드 생성 및 메시지 전송
        # 스레드는 Agent와의 대화 컨텍스트를 유지합니다.
        # ============================================================
        thread = project.agents.threads.create()
        print(f"💬 스레드 생성 완료: {thread.id}")

        # 사용자 메시지 전송
        user_message = "서울의 현재 날씨를 알려주세요"
        project.agents.messages.create(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=user_message,
        )
        print(f'\n💬 메시지 전송: "{user_message}"')

        # ============================================================
        # 5단계: Agent 실행 및 완료 대기
        # run을 생성하면 Agent가 메시지를 처리하고,
        # 필요하면 MCP 도구를 호출하여 답변을 생성합니다.
        # ============================================================
        print("⏳ Agent 실행 중...")
        run = project.agents.runs.create(
            thread_id=thread.id,
            agent_id=agent.id,
        )

        # 실행 완료 대기 (폴링 방식)
        while run.status in ("queued", "in_progress", "requires_action"):
            time.sleep(1)
            run = project.agents.runs.get(
                thread_id=thread.id,
                run_id=run.id,
            )

        # 실행 결과 확인
        if run.status == "failed":
            print(f"❌ Agent 실행 실패: {run.last_error}")
            return

        print(f"✅ Agent 실행 완료 (상태: {run.status})")

        # ============================================================
        # 6단계: Agent 응답 확인
        # 스레드의 메시지 목록에서 Agent의 응답을 가져옵니다.
        # ============================================================
        messages = project.agents.messages.list(thread_id=thread.id)

        print("\n📨 Agent 응답:")
        # 가장 최근 어시스턴트 메시지를 찾아 출력합니다
        for msg in messages.data:
            if msg.role == MessageRole.AGENT:
                for content_block in msg.content:
                    if hasattr(content_block, "text"):
                        print(content_block.text.value)
                break

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n💡 확인 사항:")
        print("  1. MCP 서버가 실행 중인지 확인하세요")
        print("  2. PROJECT_ENDPOINT가 올바른지 확인하세요")
        print("  3. az login으로 Azure에 인증했는지 확인하세요")
        raise

    finally:
        # ============================================================
        # 7단계: 리소스 정리
        # 사용이 끝난 Agent를 삭제하여 리소스를 정리합니다.
        # ============================================================
        print("\n🧹 리소스 정리 중...")
        if agent:
            project.agents.delete_agent(agent.id)
            print(f"  ✅ Agent 삭제 완료: {agent.id}")
        print("🧹 리소스 정리 완료")


# ============================================================
# 메인 실행 블록
# ============================================================
if __name__ == "__main__":
    main()
