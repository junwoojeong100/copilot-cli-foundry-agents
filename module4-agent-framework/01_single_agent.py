"""
실습 1: 단일 에이전트 기본
Microsoft Agent Framework를 사용한 가장 기본적인 에이전트 실행 예제입니다.
Azure OpenAI와 연동하여 단일 에이전트가 사용자 질문에 응답합니다.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# 상위 디렉토리의 .env 파일 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from agent_framework import Agent
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential


async def main():
    """단일 에이전트를 생성하고 실행하는 메인 함수"""

    print("=== 단일 에이전트 실행 ===\n")

    # ── 1단계: Azure OpenAI 클라이언트 설정 ──
    # 환경 변수에서 엔드포인트와 배포 이름을 가져옵니다
    project_endpoint = os.getenv("PROJECT_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("MODEL_DEPLOYMENT", "gpt-4o")

    if not project_endpoint:
        print("오류: PROJECT_ENDPOINT 또는 AZURE_OPENAI_ENDPOINT 환경 변수를 설정해주세요.")
        sys.exit(1)

    # Azure CLI 인증 정보를 사용하여 클라이언트 생성
    credential = AzureCliCredential()
    client = AzureOpenAIResponsesClient(
        azure_credential=credential,
        project_endpoint=project_endpoint,
        deployment_name=deployment_name,
    )

    # ── 2단계: 에이전트 생성 ──
    # 에이전트에게 역할과 지시사항을 부여합니다
    agent = client.as_agent(
        name="기술_어시스턴트",
        instructions=(
            "당신은 Microsoft 기술 전문 어시스턴트입니다. "
            "사용자의 기술 질문에 대해 정확하고 이해하기 쉽게 한국어로 답변합니다. "
            "답변은 간결하면서도 핵심을 포함해야 합니다."
        ),
    )

    # ── 3단계: 에이전트 실행 ──
    # 질문을 전달하고 에이전트의 응답을 받습니다
    question = "Microsoft Agent Framework가 무엇인가요?"
    print(f"질문: {question}\n")

    try:
        result = await agent.run(question)

        # ── 4단계: 결과 출력 ──
        print("에이전트 응답:")
        print(result)

    except Exception as e:
        print(f"에이전트 실행 중 오류 발생: {e}")
        sys.exit(1)

    print("\n=== 실행 완료 ===")


if __name__ == "__main__":
    asyncio.run(main())
