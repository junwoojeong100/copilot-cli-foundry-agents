"""
실습 4: 커스텀 그래프 워크플로우
그래프 기반으로 노드(에이전트)와 엣지(연결)를 직접 정의하여
조건부 라우팅이 포함된 콘텐츠 제작 파이프라인을 구축합니다.

워크플로우:
  [주제 분석] → 기술 주제? → [기술 작가] → [편집자] → [최종 출력]
                일반 주제? → [일반 작가] → [편집자] → [최종 출력]
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# 상위 디렉토리의 .env 파일 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from agent_framework import Agent
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.workflows import WorkflowGraph, Node, Edge
from azure.identity import AzureCliCredential


async def create_agents(client: AzureOpenAIResponsesClient) -> dict:
    """파이프라인에 필요한 에이전트들을 생성합니다"""

    agents = {}

    # 주제 분석 에이전트 - 입력 주제의 카테고리를 판별합니다
    agents["topic_analyzer"] = client.as_agent(
        name="주제_분석",
        instructions=(
            "당신은 콘텐츠 주제 분석 전문가입니다. "
            "주어진 주제를 분석하여 '기술' 또는 '일반' 카테고리로 분류합니다.\n"
            "판단 기준:\n"
            "- 기술: 프로그래밍, 클라우드, AI/ML, DevOps, 보안, 데이터베이스 등\n"
            "- 일반: 비즈니스, 마케팅, 라이프스타일, 교육 등\n\n"
            "반드시 첫 줄에 '카테고리: 기술' 또는 '카테고리: 일반'으로 시작하고, "
            "그 다음에 주제 분석 요약을 작성합니다. 한국어로 답변합니다."
        ),
    )

    # 기술 작가 에이전트 - 기술 주제에 특화된 글을 작성합니다
    agents["tech_writer"] = client.as_agent(
        name="기술_작가",
        instructions=(
            "당신은 기술 콘텐츠 전문 작가입니다. "
            "기술 주제에 대해 정확하고 깊이 있는 글을 작성합니다. "
            "코드 예제, 아키텍처 다이어그램 설명, 모범 사례를 포함합니다. "
            "전문 용어를 사용하되 이해하기 쉽게 설명합니다. "
            "한국어로 작성합니다."
        ),
    )

    # 일반 작가 에이전트 - 일반 주제에 대해 읽기 쉬운 글을 작성합니다
    agents["general_writer"] = client.as_agent(
        name="일반_작가",
        instructions=(
            "당신은 일반 콘텐츠 작가입니다. "
            "일반 주제에 대해 대중이 이해하기 쉬운 글을 작성합니다. "
            "스토리텔링 기법을 활용하고, 실생활 예시를 포함합니다. "
            "전문 용어 사용을 최소화하고 누구나 읽을 수 있도록 작성합니다. "
            "한국어로 작성합니다."
        ),
    )

    # 편집자 에이전트 - 작성된 글을 검토하고 개선합니다
    agents["editor"] = client.as_agent(
        name="편집자",
        instructions=(
            "당신은 시니어 편집자입니다. "
            "이전 작가가 작성한 초안을 검토하고 개선합니다.\n"
            "검토 항목: 논리적 흐름, 문법, 가독성, 정확성\n"
            "개선된 최종 버전을 출력합니다. "
            "한국어로 작성합니다."
        ),
    )

    return agents


def route_by_category(analysis_result: str) -> str:
    """주제 분석 결과에서 카테고리를 추출하여 라우팅 경로를 결정합니다"""
    if "기술" in analysis_result.split("\n")[0]:
        return "tech_writer"
    return "general_writer"


async def main():
    """커스텀 그래프 워크플로우를 구성하고 실행하는 메인 함수"""

    print("=== 커스텀 그래프 워크플로우 실행 ===\n")

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

    # ── 2단계: 에이전트 생성 ──
    agents = await create_agents(client)

    # ── 3단계: 워크플로우 그래프 정의 ──
    # 노드와 엣지로 파이프라인을 구성합니다
    workflow = WorkflowGraph()

    # 노드 등록 - 각 에이전트를 그래프의 노드로 추가합니다
    workflow.add_node(Node(id="analyze", agent=agents["topic_analyzer"]))
    workflow.add_node(Node(id="tech_writer", agent=agents["tech_writer"]))
    workflow.add_node(Node(id="general_writer", agent=agents["general_writer"]))
    workflow.add_node(Node(id="editor", agent=agents["editor"]))

    # 엣지 등록 - 노드 간 데이터 흐름을 정의합니다
    # 주제 분석 → 조건부 라우팅 (기술 작가 또는 일반 작가)
    workflow.add_edge(Edge(
        source="analyze",
        target="tech_writer",
        condition=lambda state: route_by_category(state["result"]) == "tech_writer",
    ))
    workflow.add_edge(Edge(
        source="analyze",
        target="general_writer",
        condition=lambda state: route_by_category(state["result"]) == "general_writer",
    ))

    # 작가 → 편집자 (두 작가 모두 편집자로 연결)
    workflow.add_edge(Edge(source="tech_writer", target="editor"))
    workflow.add_edge(Edge(source="general_writer", target="editor"))

    # 시작 노드 설정
    workflow.set_entry_point("analyze")

    # ── 4단계: 워크플로우 실행 ──
    input_topic = "Kubernetes 클러스터 최적화 전략"
    print(f"입력 주제: {input_topic}\n")
    print("=" * 50)

    try:
        # 워크플로우에 초기 상태를 전달하고 실행합니다
        result = await workflow.run(
            input=input_topic,
            state={"topic": input_topic},
        )

        # ── 5단계: 단계별 결과 출력 ──
        print("\n[1단계] 주제 분석 완료")
        if hasattr(result, "steps"):
            for i, step in enumerate(result.steps, 1):
                print(f"\n--- 단계 {i}: {step.node_id} ---")
                print(step.output[:200] + "..." if len(step.output) > 200 else step.output)

        # 최종 결과 출력
        print("\n" + "=" * 50)
        print("\n=== 최종 콘텐츠 ===\n")
        print(result)

    except Exception as e:
        print(f"워크플로우 실행 중 오류 발생: {e}")
        sys.exit(1)

    print("\n=== 실행 완료 ===")


if __name__ == "__main__":
    asyncio.run(main())
