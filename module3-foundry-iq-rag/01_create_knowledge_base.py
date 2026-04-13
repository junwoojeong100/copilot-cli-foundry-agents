"""
모듈 3 - 실습 1: Foundry IQ 지식 베이스 생성 및 확인

이 스크립트는 Azure AI Foundry 포털에서 생성한 지식 베이스가
올바르게 설정되었는지 확인합니다.

지식 베이스 생성은 Azure AI Foundry 포털에서 수행하는 것이 가장 간편합니다.

=== 포털에서 지식 베이스 생성하는 방법 ===
1. https://ai.azure.com 에 로그인합니다.
2. 프로젝트를 선택합니다.
3. 왼쪽 메뉴에서 "지식 베이스(Knowledge Bases)"를 클릭합니다.
4. "+ 새 지식 베이스"를 클릭합니다.
5. 이름: "smarttech-kb", 설명: "스마트테크 제품 FAQ" 입력
6. 연결된 AI Search 리소스를 선택합니다.
7. "만들기"를 클릭합니다.
8. 생성 후 "파일 업로드"를 클릭하여 sample_data/sample_docs.md를 업로드합니다.
9. 자동으로 청킹 및 인덱싱이 진행됩니다 (1~5분 소요).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .env 파일 로드 (상위 디렉토리에서 찾기)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def check_environment_variables() -> dict:
    """필수 환경 변수가 설정되어 있는지 확인합니다."""
    required_vars = {
        "SEARCH_SERVICE_ENDPOINT": "Azure AI Search 서비스 엔드포인트",
        "KNOWLEDGE_BASE_NAME": "지식 베이스 이름",
        "PROJECT_CONNECTION_NAME": "AI Search 연결 이름",
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


def build_mcp_endpoint(search_endpoint: str, knowledge_base_name: str) -> str:
    """
    지식 베이스의 MCP 엔드포인트 URL을 구성합니다.

    MCP 엔드포인트 형식:
    {search_service_endpoint}/knowledgebases/{knowledge_base_name}/mcp?api-version=2025-11-01-preview
    """
    # 엔드포인트 URL 끝의 슬래시 제거
    search_endpoint = search_endpoint.rstrip("/")

    mcp_endpoint = (
        f"{search_endpoint}/knowledgebases"
        f"/{knowledge_base_name}/mcp"
        f"?api-version=2025-11-01-preview"
    )
    return mcp_endpoint


def verify_search_service(search_endpoint: str) -> bool:
    """
    Azure AI Search 서비스에 연결할 수 있는지 확인합니다.
    Azure SDK를 사용하여 인덱스 목록을 조회합니다.
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.search.documents.indexes import SearchIndexClient

        # DefaultAzureCredential로 인증 (az login 필요)
        credential = DefaultAzureCredential()
        index_client = SearchIndexClient(
            endpoint=search_endpoint,
            credential=credential,
        )

        # 인덱스 목록 조회
        print("\n📋 Azure AI Search 인덱스 목록:")
        indexes = list(index_client.list_index_names())

        if indexes:
            for idx_name in indexes:
                print(f"  ✅ {idx_name}")
        else:
            print("  ⚠️  인덱스가 아직 없습니다.")
            print("     포털에서 지식 베이스를 생성하고 문서를 업로드하면 인덱스가 자동 생성됩니다.")

        return True

    except ImportError:
        print("\n⚠️  azure-search-documents 패키지가 설치되지 않았습니다.")
        print("   pip install azure-search-documents azure-identity 를 실행해 주세요.")
        return False

    except Exception as e:
        print(f"\n❌ AI Search 서비스 연결 실패: {e}")
        print("   다음을 확인해 주세요:")
        print("   1. SEARCH_SERVICE_ENDPOINT가 올바른지 확인")
        print("   2. 'az login'으로 Azure에 로그인했는지 확인")
        print("   3. AI Search 리소스에 접근 권한이 있는지 확인")
        return False


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🔍 Foundry IQ 지식 베이스 확인 도구")
    print("=" * 60)

    # 1단계: 환경 변수 확인
    print("\n📌 1단계: 환경 변수 확인")
    config = check_environment_variables()
    print("✅ 모든 환경 변수가 설정되어 있습니다.")

    search_endpoint = config["SEARCH_SERVICE_ENDPOINT"]
    knowledge_base_name = config["KNOWLEDGE_BASE_NAME"]
    connection_name = config["PROJECT_CONNECTION_NAME"]

    print(f"\n   Search 엔드포인트: {search_endpoint}")
    print(f"   지식 베이스 이름:  {knowledge_base_name}")
    print(f"   연결 이름:        {connection_name}")

    # 2단계: MCP 엔드포인트 구성
    print("\n📌 2단계: MCP 엔드포인트 구성")
    mcp_endpoint = build_mcp_endpoint(search_endpoint, knowledge_base_name)
    print(f"   MCP 엔드포인트: {mcp_endpoint}")

    # 3단계: AI Search 서비스 연결 확인
    print("\n📌 3단계: Azure AI Search 서비스 연결 확인")
    verify_search_service(search_endpoint)

    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 설정 요약")
    print("=" * 60)
    print(f"  지식 베이스 이름: {knowledge_base_name}")
    print(f"  MCP 엔드포인트:  {mcp_endpoint}")
    print(f"  연결 이름:       {connection_name}")
    print()
    print("다음 단계:")
    print("  1. 위 MCP 엔드포인트를 02_agent_with_rag.py에서 사용합니다.")
    print("  2. python 02_agent_with_rag.py 를 실행하여 RAG 에이전트를 테스트합니다.")
    print("=" * 60)


if __name__ == "__main__":
    main()
