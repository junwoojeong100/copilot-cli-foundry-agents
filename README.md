# Microsoft AI Agent 실습 가이드

Microsoft의 최신 AI Agent 기술 스택을 단계별로 학습하는 실습 가이드입니다.

## 🎯 학습 목표

| 모듈 | 주제 | 핵심 기술 |
|------|------|-----------|
| **모듈 1** | [Agent SDK v2 기본](./module1-agent-sdk/) | `azure-ai-projects`, Agent/Thread/Run |
| **모듈 2** | [MCP 서버 연결](./module2-mcp-server/) | MCP 프로토콜, `MCPTool` |
| **모듈 3** | [Foundry IQ RAG](./module3-foundry-iq-rag/) | 지식 베이스, Agentic RAG |
| **모듈 4** | [Agent Framework 워크플로우](./module4-agent-framework/) | Handoff, GroupChat, 그래프 워크플로우 |

## 📋 사전 준비

### 필수 요구 사항
- **Python 3.10+**
- **Azure 구독** (Azure AI Foundry 프로젝트 생성 완료)
- **Azure CLI** (`az login` 인증 완료)
- **Azure AI Foundry 프로젝트** (모델 배포 완료, 예: `gpt-4o`)

### 환경 설정

```bash
# 1. 리포지토리 클론
git clone <이 리포지토리 URL>
cd copilot-cli-microsoft-agent-framework

# 2. 가상 환경 생성
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 실제 값 입력
```

### Azure AI Foundry 프로젝트 설정

1. [Azure AI Foundry 포털](https://ai.azure.com)에서 프로젝트 생성
2. **프로젝트 엔드포인트** 확인 (예: `https://<resource>.ai.azure.com/api/projects/<project>`)
3. GPT-4o 모델 배포
4. 프로젝트 엔드포인트와 모델 배포 이름을 `.env`에 기록

## 🏗️ 전체 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                   Azure AI Foundry                        │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ Agent SDK v2 │  │  Foundry IQ  │  │  Model 배포     │ │
│  │ (모듈 1, 2) │  │  (모듈 3)    │  │  (GPT-4o 등)   │ │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘ │
│         │                │                    │          │
│         ▼                ▼                    ▼          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │            Agent Service (에이전트 런타임)            │ │
│  └──────────────────────┬──────────────────────────────┘ │
│                         │                                │
│  ┌──────────────────────▼──────────────────────────────┐ │
│  │          MCP 프로토콜 (도구 연결 레이어)              │ │
│  └──────────────────────┬──────────────────────────────┘ │
└─────────────────────────┼────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ MCP 서버   │  │ 외부 API   │  │ 지식 베이스 │
   │ (모듈 2)   │  │            │  │ (모듈 3)   │
   └────────────┘  └────────────┘  └────────────┘

┌──────────────────────────────────────────────────────────┐
│           Microsoft Agent Framework (모듈 4)              │
│  ┌────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
│  │ Agent  │  │ Handoff  │  │ GroupChat │  │ 그래프    │ │
│  │ 정의   │  │ 워크플로우│  │ 워크플로우│  │ 워크플로우│ │
│  └────────┘  └──────────┘  └───────────┘  └──────────┘ │
└──────────────────────────────────────────────────────────┘
```

## 📂 프로젝트 구조

```
├── README.md                          # 이 파일
├── .env.example                       # 환경변수 템플릿
├── requirements.txt                   # 공통 의존성
├── module1-agent-sdk/                 # 모듈 1: Agent SDK v2
├── module2-mcp-server/               # 모듈 2: MCP 서버 연결
├── module3-foundry-iq-rag/           # 모듈 3: Foundry IQ RAG
├── module4-agent-framework/          # 모듈 4: Agent Framework
└── docs/                             # 아키텍처 문서
```

## 🚀 모듈별 실습 순서

**모듈 1 → 모듈 2 → 모듈 3 → 모듈 4** 순서를 권장합니다.
각 모듈은 독립적으로 실행할 수 있지만, 이전 모듈의 개념을 이해하면 더 효과적입니다.

## 📚 참고 자료

- [Azure AI Foundry 공식 문서](https://learn.microsoft.com/en-us/azure/foundry/)
- [Azure AI Projects SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme)
- [MCP 프로토콜 명세](https://modelcontextprotocol.io/)
- [Microsoft Agent Framework GitHub](https://github.com/microsoft/agent-framework)
- [Foundry IQ 소개](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/foundry-iq-unlocking-ubiquitous-knowledge-for-agents/4470812)
