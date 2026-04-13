"""
실습 2: Handoff 워크플로우
접수 에이전트가 사용자 요청을 분석한 뒤, 적절한 전문가 에이전트에게 작업을 위임합니다.
고객 지원 시나리오를 Handoff 패턴으로 구현합니다.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# 상위 디렉토리의 .env 파일 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from agent_framework import Agent
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.orchestrations import HandoffBuilder
from azure.identity import AzureCliCredential


async def main():
    """Handoff 워크플로우를 구성하고 실행하는 메인 함수"""

    print("=== Handoff 워크플로우 실행 ===\n")

    # ── 1단계: Azure OpenAI 클라이언트 설정 ──
    project_endpoint = os.getenv("PROJECT_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("MODEL_DEPLOYMENT", "gpt-4o")

    if not project_endpoint:
        print("오류: PROJECT_ENDPOINT 또는 AZURE_OPENAI_ENDPOINT 환경 변수를 설정해주세요.")
        sys.exit(1)

    credential = AzureCliCredential()
    client = AzureOpenAIResponsesClient(
        azure_credential=credential,
        project_endpoint=project_endpoint,
        deployment_name=deployment_name,
    )

    # ── 2단계: 전문가 에이전트 생성 ──
    # 각 에이전트는 특정 도메인에 특화된 지시사항을 가집니다

    # 기술 지원 전문가 에이전트
    tech_support_agent = client.as_agent(
        name="기술_지원",
        instructions=(
            "당신은 기술 지원 전문가입니다. "
            "소프트웨어 설치, 오류 해결, 시스템 설정 등 기술적인 문제를 해결합니다. "
            "단계별로 명확하게 안내하며, 필요시 추가 정보를 요청합니다. "
            "한국어로 답변합니다."
        ),
    )

    # 결제 지원 전문가 에이전트
    billing_agent = client.as_agent(
        name="결제_지원",
        instructions=(
            "당신은 결제 지원 전문가입니다. "
            "결제 오류, 환불 요청, 구독 관리, 청구서 문의 등 결제 관련 문제를 처리합니다. "
            "고객의 결제 문제를 신속하고 정확하게 해결합니다. "
            "한국어로 답변합니다."
        ),
    )

    # 접수 담당 에이전트 (Triage) - 사용자 요청을 분류하고 라우팅합니다
    triage_agent = client.as_agent(
        name="접수_담당",
        instructions=(
            "당신은 고객 지원 접수 담당자입니다. "
            "사용자의 요청을 분석하여 적절한 전문가에게 연결합니다.\n"
            "- 기술적인 문제 (설치, 오류, 설정 등) → 기술_지원 에이전트에게 handoff\n"
            "- 결제 관련 문제 (결제 오류, 환불, 구독 등) → 결제_지원 에이전트에게 handoff\n"
            "먼저 사용자에게 간단히 어떤 전문가에게 연결하는지 안내한 후 handoff합니다."
        ),
    )

    # ── 3단계: Handoff 워크플로우 구성 ──
    # HandoffBuilder를 사용하여 에이전트 간 위임 규칙을 정의합니다
    handoff = (
        HandoffBuilder()
        .add_agent(triage_agent)
        .add_agent(tech_support_agent)
        .add_agent(billing_agent)
        .set_entry_agent(triage_agent)  # 시작 에이전트 지정
        .build()
    )

    # ── 4단계: 워크플로우 실행 ──
    # 사용자 요청을 Handoff 워크플로우에 전달합니다
    user_query = "결제 오류가 발생했습니다. 카드 결제가 계속 실패하고 있어요."
    print(f"사용자 요청: {user_query}\n")
    print("-" * 50)

    try:
        result = await handoff.run(user_query)

        # ── 5단계: 결과 출력 ──
        # Handoff 흐름과 최종 응답을 표시합니다
        print("\n[최종 응답]")
        print(result)

    except Exception as e:
        print(f"워크플로우 실행 중 오류 발생: {e}")
        sys.exit(1)

    print("\n=== 실행 완료 ===")


if __name__ == "__main__":
    asyncio.run(main())
