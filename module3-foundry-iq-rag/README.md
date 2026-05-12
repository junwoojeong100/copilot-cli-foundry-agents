# 모듈 3: Foundry IQ를 활용한 RAG

## 🎯 학습 목표

이 모듈을 완료하면 다음을 수행할 수 있습니다:

1. **Foundry IQ**의 핵심 개념과 기존 RAG와의 차이점을 이해합니다.
2. Azure AI Foundry 포털에서 **지식 베이스(Knowledge Base)**를 생성합니다.
3. **MCP(Model Context Protocol)** 기반으로 에이전트에 지식 베이스를 연결합니다.
4. **출처 인용(Citations)**이 포함된 RAG 에이전트를 구현합니다.

---

## 📚 Foundry IQ 핵심 개념

### 지식 베이스 (Knowledge Base)

Foundry IQ의 지식 베이스는 문서를 업로드하면 자동으로 **청킹(Chunking)**, **임베딩(Embedding)**, **인덱싱(Indexing)**을 처리하는 관리형 RAG 서비스입니다. 별도의 파이프라인 구축 없이 포털에서 클릭 몇 번으로 검색 가능한 지식 베이스를 만들 수 있습니다.

### Agentic RAG

기존 RAG는 개발자가 검색 로직을 직접 구현해야 하지만, Foundry IQ는 **에이전트가 자율적으로 지식 베이스를 검색**합니다. MCP 도구를 통해 에이전트가 필요할 때 스스로 검색을 수행하므로, 검색 타이밍과 쿼리 구성을 자동으로 최적화합니다.

### 하이브리드 검색 (Hybrid Search)

Foundry IQ는 **키워드 검색**과 **벡터(의미론적) 검색**을 결합한 하이브리드 검색을 기본 제공합니다:

- **키워드 검색**: 정확한 용어 매칭 (예: 제품명, 코드)
- **벡터 검색**: 의미적 유사성 기반 검색 (예: "반품하고 싶어요" → "환불 정책")
- **시맨틱 랭킹**: 검색 결과를 문맥 기반으로 재순위화

### 출처 인용 (Citations)

Foundry IQ는 응답에 **출처 인용을 자동으로 포함**합니다. 형식은 다음과 같습니다:

```
【message_idx:search_idx†source_name】
```

이를 통해 사용자는 답변의 근거를 확인하고, 환각(Hallucination)을 방지할 수 있습니다.

---

## ⚖️ 기존 RAG vs Foundry IQ 비교

| 항목 | 기존 RAG (직접 구축) | Foundry IQ |
|------|---------------------|------------|
| **문서 처리** | 청킹/임베딩 파이프라인 직접 구축 | 포털에서 자동 처리 |
| **벡터 저장소** | Pinecone, Weaviate 등 별도 관리 | Azure AI Search 자동 관리 |
| **검색 방식** | 단일 방식 (키워드 또는 벡터) | 하이브리드 + 시맨틱 랭킹 기본 제공 |
| **에이전트 연결** | 검색 로직 직접 코딩 | MCP 도구로 자동 연결 |
| **출처 인용** | 직접 구현 필요 | 자동 인용 제공 |
| **청킹 최적화** | 수동 튜닝 필요 | 자동 최적화 |
| **유지보수** | 파이프라인 모니터링/관리 필요 | 관리형 서비스 |
| **초기 설정 시간** | 수 일 ~ 수 주 | 수 분 |

---

## 🔧 사전 준비

### 필수 Azure 리소스

1. **Azure AI Foundry 프로젝트** (모듈 1에서 생성)
2. **Azure AI Search 리소스** — Foundry IQ 지식 베이스의 백엔드로 사용됩니다.
3. **모델 배포** — GPT-4o 또는 GPT-4o-mini 배포 (모듈 1에서 완료)

### Azure AI Search 리소스 생성

Azure AI Search가 아직 없다면:

1. [Azure Portal](https://portal.azure.com)에서 **"AI Search"** 검색
2. **"만들기"** 클릭
3. 다음을 설정:
   - **리소스 그룹**: AI Foundry 프로젝트와 동일한 그룹
   - **서비스 이름**: 고유한 이름 (예: `my-ai-search-001`)
   - **위치**: AI Foundry 프로젝트와 동일한 리전
   - **가격 계층**: Basic (실습용)
4. **"검토 + 만들기"** → **"만들기"** 클릭

### Foundry IQ 활성화

1. [Azure AI Foundry 포털](https://ai.azure.com)로 이동
2. 프로젝트 선택
3. 왼쪽 메뉴에서 **"지식 베이스"** 또는 **"Knowledge Bases"** 클릭
4. AI Search 리소스가 연결되지 않았다면 연결 설정

### Python 환경 설정

```bash
# 프로젝트 루트에서 실행
pip install -r requirements.txt
```

### 환경 변수 설정

프로젝트 루트의 `.env` 파일에 다음을 추가하세요:

```env
PROJECT_ENDPOINT=https://<your-resource>.services.ai.azure.com/api/projects/<project-name>
SEARCH_SERVICE_ENDPOINT=https://<your-search-service>.search.windows.net
KNOWLEDGE_BASE_NAME=smarttech-kb
PROJECT_CONNECTION_NAME=<your-search-connection-name>
MODEL_DEPLOYMENT_NAME=gpt-4o
```

> 💡 `PROJECT_CONNECTION_NAME`은 AI Foundry 포털 → 프로젝트 설정 → 연결된 리소스에서 AI Search 연결 이름을 확인할 수 있습니다.

---

## 🧪 실습 1: 지식 베이스 생성

### Azure AI Foundry 포털에서 생성

지식 베이스는 **Azure AI Foundry 포털**에서 생성하는 것이 가장 간편합니다.

#### 단계별 가이드

1. [Azure AI Foundry 포털](https://ai.azure.com)에 로그인
2. 프로젝트를 선택합니다
3. 왼쪽 메뉴에서 **"지식 베이스(Knowledge Bases)"** 클릭
4. **"+ 새 지식 베이스"** 클릭
5. 다음을 설정합니다:
   - **이름**: `smarttech-kb`
   - **설명**: "스마트테크 제품 FAQ 지식 베이스"
   - **연결된 AI Search**: 위에서 생성한 AI Search 선택
6. **"만들기"** 클릭
7. 생성이 완료되면 **"파일 업로드"** 클릭
8. `sample_data/sample_docs.md` 파일을 업로드합니다
9. 업로드 후 자동으로 청킹 및 인덱싱이 시작됩니다 (1~5분 소요)

### 프로그래밍 방식으로 확인

`01_create_knowledge_base.py` 스크립트를 실행하여 지식 베이스가 올바르게 생성되었는지 확인합니다:

```bash
cd module3-foundry-iq-rag
python 01_create_knowledge_base.py
```

이 스크립트는:
- 환경 변수를 로드합니다
- AI Search 서비스에 연결하여 인덱스 존재 여부를 확인합니다
- 지식 베이스의 MCP 엔드포인트 URL을 구성하고 출력합니다

📖 자세한 코드 설명은 [01_create_knowledge_base.py](./01_create_knowledge_base.py)를 참조하세요.

---

## 🧪 실습 2: RAG 에이전트 구현

### 개요

이 실습에서는 Foundry IQ 지식 베이스에 **MCP 도구**로 연결된 에이전트를 만듭니다. 에이전트는 사용자의 질문을 받으면 자동으로 지식 베이스를 검색하고, 출처 인용과 함께 답변합니다.

### 실행

```bash
cd module3-foundry-iq-rag
python 02_agent_with_rag.py
```

### 코드 핵심 포인트

#### 1. MCP 엔드포인트 구성

```python
mcp_endpoint = (
    f"{search_service_endpoint}/knowledgebases"
    f"/{knowledge_base_name}/mcp"
    f"?api-version=2025-11-01-preview"
)
```

Foundry IQ는 MCP(Model Context Protocol)를 통해 에이전트가 지식 베이스에 접근합니다. 이 URL이 에이전트의 검색 도구 엔드포인트가 됩니다.

#### 2. MCPTool 설정

```python
mcp_tool = MCPTool(
    server_label="knowledge-base",
    server_url=mcp_endpoint,
    require_approval="never",
    allowed_tools=["knowledge_base_retrieve"],
    project_connection_id=project_connection_name,
)
```

- `server_label`: 도구의 식별 라벨
- `require_approval`: `"never"`로 설정하면 에이전트가 자동으로 검색 수행
- `allowed_tools`: 사용 가능한 MCP 도구 목록 제한
- `project_connection_id`: AI Search 연결 이름

#### 3. 에이전트 지시사항

에이전트에게 **반드시 지식 베이스를 사용하고, 출처를 인용**하도록 지시합니다:

```python
instructions = """
You are a helpful assistant that must use the knowledge base to answer all questions.
Every answer must provide annotations using: 【message_idx:search_idx†source_name】
If you cannot find the answer, respond with "해당 정보를 찾을 수 없습니다."
"""
```

📖 전체 코드는 [02_agent_with_rag.py](./02_agent_with_rag.py)를 참조하세요.

---

## 🏗️ Foundry IQ 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 (User)                              │
│                 "스마트워치 가격이 얼마예요?"                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Azure AI Foundry Agent                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  GPT-4o 모델 + 시스템 지시사항                         │    │
│  │  "지식 베이스를 사용하여 답변하고 출처를 인용하세요"       │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │ MCP Tool 호출                      │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  MCPTool (knowledge_base_retrieve)                   │    │
│  │  server_url: .../knowledgebases/{name}/mcp           │    │
│  └──────────────────────┬──────────────────────────────┘    │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Foundry IQ Knowledge Base                        │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐     │
│  │  문서 청킹     │  │  벡터 임베딩   │  │  시맨틱 랭킹   │     │
│  │  (Chunking)   │  │  (Embedding)  │  │  (Ranking)    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬────────┘     │
│         └──────────────────┼─────────────────┘              │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Azure AI Search (하이브리드 검색)             │    │
│  │       키워드 + 벡터 + 시맨틱 랭킹 결합                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    응답 (Response)                            │
│  "스마트워치 프로의 가격은 349,000원입니다.                     │
│   【0:0†sample_docs.md】"                                    │
└─────────────────────────────────────────────────────────────┘
```

### 데이터 흐름 요약

1. **사용자**가 질문을 입력합니다
2. **에이전트**가 질문을 분석하고, MCP 도구를 호출할지 결정합니다
3. **MCPTool**이 Foundry IQ 지식 베이스에 검색 요청을 보냅니다
4. **Foundry IQ**가 하이브리드 검색 + 시맨틱 랭킹으로 관련 문서 청크를 반환합니다
5. **에이전트**가 검색 결과를 바탕으로 답변을 생성하고, **출처 인용**을 포함합니다

---

## 📝 핵심 정리

| 개념 | 설명 |
|------|------|
| **Foundry IQ** | Azure AI Foundry의 관리형 RAG 서비스 |
| **지식 베이스** | 문서를 업로드하면 자동으로 검색 가능한 인덱스 생성 |
| **MCP 도구** | 에이전트가 지식 베이스에 접근하는 표준 프로토콜 |
| **하이브리드 검색** | 키워드 + 벡터 검색을 결합한 방식 |
| **출처 인용** | 답변의 근거가 되는 문서를 자동으로 표시 |
| **Agentic RAG** | 에이전트가 자율적으로 검색 타이밍/쿼리를 결정 |

### 기억할 점

- ✅ 지식 베이스는 **포털에서 생성**하는 것이 가장 간편합니다
- ✅ MCP 엔드포인트 형식: `{search_endpoint}/knowledgebases/{name}/mcp?api-version=2025-11-01-preview`
- ✅ `require_approval="never"`로 설정하면 에이전트가 자동 검색합니다
- ✅ 출처 인용 형식: `【message_idx:search_idx†source_name】`
- ✅ 환각 방지를 위해 "찾을 수 없을 때" 안내 문구를 지시사항에 포함하세요

---

## ➡️ 다음 단계

지식 베이스와 RAG 에이전트를 구현했으니, 이제 여러 에이전트를 조합하는 방법을 알아보겠습니다.

👉 [모듈 4: 에이전트 프레임워크와 멀티 에이전트](../module4-agent-framework/README.md)

모듈 4에서는:
- 여러 에이전트를 연결하는 **에이전트 프레임워크** 활용법
- **Semantic Kernel** / **AutoGen** 기반 멀티 에이전트 시스템 구현
- 에이전트 간 **핸드오프(Handoff)** 패턴
- 실제 업무 시나리오에 적용하는 방법

을 학습합니다.
