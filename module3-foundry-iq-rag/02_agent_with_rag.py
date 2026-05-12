"""
모듈 3 - 실습 2: Foundry IQ 지식 베이스를 활용한 RAG 에이전트

이 스크립트는 Azure AI Foundry의 에이전트를 생성하고,
Foundry IQ 지식 베이스를 MCP 도구로 연결하여 RAG를 수행합니다.

에이전트는 사용자의 질문에 대해:
1. 자동으로 지식 베이스를 검색합니다 (Agentic RAG)
2. 검색 결과를 바탕으로 답변을 생성합니다
3. 출처 인용(Citations)을 포함하여 응답합니다

사전 준비:
- 01_create_knowledge_base.py를 실행하여 설정을 확인했는지 확인
- .env 파일에 필요한 환경 변수가 설정되어 있는지 확인
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .env 파일 로드 (상위 디렉토리에서 찾기)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_config() -> dict:
    """환경 변수에서 설정값을 로드합니다."""
    required_vars = {
        "PROJECT_ENDPOINT": "Azure AI Foundry 프로젝트 엔드포인트",
        "SEARCH_SERVICE_ENDPOINT": "Azure AI Search 서비스 엔드포인트",
        "KNOWLEDGE_BASE_NAME": "지식 베이스 이름",
        "PROJECT_CONNECTION_NAME": "AI Search 연결 이름",
        "MODEL_DEPLOYMENT_NAME": "모델 배포 이름 (예: gpt-4o)",
    }

    config = {}
    missing = []

    for var, description in required_vars.items():
        value = os.environ.get(var)
        if not value:
            missing.append(f"  - {var}: {description}")
        else:
            config[var] = value

    if missing:
        print("❌ 다음 환경 변수가 설정되지 않았습니다:")
        print("\n".join(missing))
        print("\n프로젝트 루트의 .env 파일에 해당 변수를 추가해 주세요.")
        sys.exit(1)

    return config


def main():
    """RAG 에이전트를 생성하고 실행합니다."""

    # --- 1단계: 설정 로드 ---
    print("=" * 60)
    print("🤖 Foundry IQ RAG 에이전트")
    print("=" * 60)
    print("\n📌 1단계: 설정 로드 중...")

    config = get_config()

    project_endpoint = config["PROJECT_ENDPOINT"]
    search_service_endpoint = config["SEARCH_SERVICE_ENDPOINT"].rstrip("/")
    knowledge_base_name = config["KNOWLEDGE_BASE_NAME"]
    project_connection_name = config["PROJECT_CONNECTION_NAME"]
    model_deployment_name = config["MODEL_DEPLOYMENT_NAME"]

    print(f"   프로젝트 엔드포인트: {project_endpoint}")
    print(f"   모델 배포:          {model_deployment_name}")
    print(f"   지식 베이스:        {knowledge_base_name}")

    # --- 2단계: MCP 엔드포인트 구성 ---
    # Foundry IQ 지식 베이스의 MCP 엔드포인트 URL을 구성합니다.
    # 형식: {search_endpoint}/knowledgebases/{name}/mcp?api-version=2025-11-01-preview
    print("\n📌 2단계: MCP 엔드포인트 구성 중...")

    mcp_endpoint = (
        f"{search_service_endpoint}/knowledgebases"
        f"/{knowledge_base_name}/mcp"
        f"?api-version=2025-11-01-preview"
    )
    print(f"   MCP 엔드포인트: {mcp_endpoint}")

    # --- 3단계: 에이전트 클라이언트 생성 ---
    print("\n📌 3단계: 에이전트 클라이언트 생성 중...")

    try:
        from azure.ai.agents import AgentsClient
        from azure.identity import DefaultAzureCredential
    except ImportError:
        print("❌ 필요한 패키지가 설치되지 않았습니다.")
        print("   pip install azure-ai-agents azure-identity 를 실행해 주세요.")
        sys.exit(1)

    # DefaultAzureCredential로 인증 (az login 필요)
    credential = DefaultAzureCredential()
    client = AgentsClient(
        endpoint=project_endpoint,
        credential=credential,
    )
    print("   ✅ 에이전트 클라이언트가 생성되었습니다.")

    # --- 4단계: MCP 도구 설정 ---
    # Foundry IQ 지식 베이스를 MCP 도구로 연결합니다.
    # azure.ai.agents SDK(1.x)에는 MCP 도구 클래스가 없으므로
    # REST API 페이로드와 동일한 dict 형식으로 직접 정의합니다.
    # - server_label: 도구의 식별 라벨
    # - server_url: 지식 베이스의 MCP 엔드포인트
    # - require_approval: "never"로 설정하면 에이전트가 자동으로 검색 수행
    # - allowed_tools: 사용 가능한 MCP 도구 목록 제한
    # - project_connection_id: AI Foundry에서 설정한 AI Search 연결 이름
    print("\n📌 4단계: MCP 도구 설정 중...")

    mcp_tool = {
        "type": "mcp",
        "server_label": "knowledge-base",
        "server_url": mcp_endpoint,
        "require_approval": "never",
        "allowed_tools": ["knowledge_base_retrieve"],
        "project_connection_id": project_connection_name,
    }
    print("   ✅ MCP 도구가 설정되었습니다.")

    # --- 5단계: 에이전트 생성 ---
    # 에이전트에게 반드시 지식 베이스를 사용하고 출처를 인용하도록 지시합니다.
    print("\n📌 5단계: RAG 에이전트 생성 중...")

    instructions = (
        "You are a helpful assistant that must use the knowledge base "
        "to answer all questions.\n"
        "Every answer must provide annotations using: "
        "【message_idx:search_idx†source_name】\n"
        'If you cannot find the answer, respond with "해당 정보를 찾을 수 없습니다."'
    )

    agent = client.create_agent(
        model=model_deployment_name,
        name="smarttech-rag-agent",
        instructions=instructions,
        tools=[mcp_tool],
    )
    print(f"   ✅ 에이전트가 생성되었습니다. (ID: {agent.id})")

    # --- 6단계: 대화 스레드 생성 및 질문 전송 ---
    print("\n📌 6단계: 대화 스레드 생성 및 질문 전송 중...")

    thread = client.threads.create()
    print(f"   ✅ 스레드가 생성되었습니다. (ID: {thread.id})")

    # 스마트테크 회사에 대한 샘플 질문들
    sample_questions = [
        "스마트워치 프로의 가격과 주요 기능을 알려주세요.",
        "제품 교환 및 환불 정책은 어떻게 되나요?",
        "스마트밴드 라이트와 스마트워치 프로의 차이점은 무엇인가요?",
    ]

    for i, question in enumerate(sample_questions, 1):
        print(f"\n{'─' * 60}")
        print(f"💬 질문 {i}: {question}")
        print("─" * 60)

        # 사용자 메시지 추가
        message = client.messages.create(
            thread_id=thread.id,
            role="user",
            content=question,
        )

        # 에이전트 실행 및 완료 대기
        # process_run은 에이전트를 실행하고 완료될 때까지 기다립니다
        run = client.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id,
        )

        # 실행 상태 확인
        if run.status == "failed":
            print(f"   ❌ 실행 실패: {run.last_error}")
            continue

        # --- 7단계: 응답 처리 ---
        # 에이전트의 응답에서 텍스트와 인용 정보를 추출합니다
        messages = client.messages.list(thread_id=thread.id)

        # 가장 최근의 어시스턴트 메시지를 찾습니다
        for msg in messages:
            if msg.role == "assistant":
                print(f"\n🤖 답변:")
                for content_block in msg.content:
                    if hasattr(content_block, "text"):
                        print(f"   {content_block.text.value}")

                        # 인용 정보 출력
                        if hasattr(content_block.text, "annotations") and content_block.text.annotations:
                            print(f"\n   📎 인용 출처:")
                            for annotation in content_block.text.annotations:
                                print(f"      - {annotation.text}")
                break  # 가장 최근 메시지만 출력

    # --- 8단계: 리소스 정리 ---
    # 사용이 끝난 에이전트와 스레드를 삭제합니다
    print(f"\n{'=' * 60}")
    print("🧹 리소스 정리 중...")

    try:
        client.threads.delete(thread_id=thread.id)
        print(f"   ✅ 스레드 삭제 완료 (ID: {thread.id})")
    except Exception as e:
        print(f"   ⚠️  스레드 삭제 실패: {e}")

    try:
        client.delete_agent(agent_id=agent.id)
        print(f"   ✅ 에이전트 삭제 완료 (ID: {agent.id})")
    except Exception as e:
        print(f"   ⚠️  에이전트 삭제 실패: {e}")

    print(f"\n{'=' * 60}")
    print("✅ RAG 에이전트 실습이 완료되었습니다!")
    print("=" * 60)


if __name__ == "__main__":
    main()
