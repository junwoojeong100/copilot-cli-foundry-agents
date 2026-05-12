# Microsoft Agentic AI 기초 실습: Foundry Agent SDK, MCP, Foundry IQ, Microsoft Agent Framework

> 🤖 **이 프로젝트는 [GitHub Copilot CLI](https://docs.github.com/copilot/concepts/agents/about-copilot-cli)로 생성되었습니다.**
> 프로젝트 구조 설계, 4개 모듈의 실습 가이드 문서, Python 코드, 아키텍처 다이어그램까지
> 전체 코드베이스가 터미널에서 Copilot CLI와의 대화를 통해 만들어졌습니다.

Microsoft의 최신 AI Agent 기술 스택을 단계별로 학습하는 실습 가이드입니다.

---

## 🛠️ GitHub Copilot CLI란?

<table>
<tr>
<td width="120" align="center">

```
  ___
 / o \  ←  GitHub
 \_-_/     Copilot
  / \      CLI
```

</td>
<td>

**GitHub Copilot CLI**는 GitHub Copilot의 에이전트 코딩 능력을 **터미널에서 직접** 사용할 수 있게 해주는 AI 도구입니다.

```bash
# 설치
brew install copilot-cli    # macOS
winget install GitHub.Copilot  # Windows

# 실행
copilot
```

</td>
</tr>
</table>

### ✨ Copilot CLI의 핵심 장점

| 장점 | 설명 |
|------|------|
| **🖥️ 터미널 네이티브** | IDE를 벗어나지 않고 터미널에서 직접 AI와 협업. 컨텍스트 전환 없이 코드 작성, 디버깅, 리팩터링 |
| **🤖 에이전트 코딩** | 단순 자동완성이 아닌, 복잡한 태스크를 **계획→실행→검증**하는 에이전틱 워크플로우 |
| **🔌 MCP 확장성** | GitHub MCP 서버가 기본 내장되어 있고, 커스텀 MCP 서버를 추가하여 기능 확장 가능 |
| **🐙 GitHub 통합** | 이슈, PR, 리포지토리를 자연어로 탐색 — `#이슈번호`로 이슈 참조, `/pr`로 PR 관리 |
| **⚡ 병렬 실행** | Fleet 모드로 여러 서브 에이전트를 동시에 실행하여 대규모 작업을 빠르게 처리 |
| **🛡️ 안전한 실행** | 모든 명령을 실행 전에 미리보기 — 명시적 승인 없이는 아무 작업도 실행되지 않음 |

### 📖 이 프로젝트가 만들어진 과정

이 실습 가이드는 다음과 같은 Copilot CLI 워크플로우로 제작되었습니다:

```
1️⃣  /plan 모드로 실습 가이드 구조 설계
    └─ 4개 모듈 구성, 파일 구조, 의존성 정의

2️⃣  Fleet 모드로 4개 모듈을 병렬 생성
    ├─ 🔄 모듈 1: Agent SDK v2 (서브에이전트 A)
    ├─ 🔄 모듈 2: MCP 서버    (서브에이전트 B)
    ├─ 🔄 모듈 3: Foundry IQ  (서브에이전트 C)
    └─ 🔄 모듈 4: Agent Framework (서브에이전트 D)

3️⃣  아키텍처 문서 자동 생성 + 구문 검증

4️⃣  Git 커밋 & GitHub 리포지토리 생성/푸시
```

> **결과**: 22개 파일, 3,200+ 줄의 코드와 문서를 하나의 세션에서 완성했습니다.

### 🚀 Copilot CLI 시작하기

```bash
# 설치 (macOS/Linux)
curl -fsSL https://gh.io/copilot-install | bash

# 또는 Homebrew
brew install copilot-cli

# 설치 (Windows)
winget install GitHub.Copilot

# 실행
copilot

# 유용한 슬래시 커맨드
/plan        # 구현 계획 수립
/fleet       # 병렬 서브에이전트 실행
/model       # AI 모델 선택 (Claude Sonnet, GPT-5 등)
/diff        # 변경사항 리뷰
/pr          # PR 생성/관리
/research    # 딥 리서치 실행
```

자세한 내용은 [GitHub Copilot CLI 공식 문서](https://docs.github.com/copilot/concepts/agents/about-copilot-cli)를 참고하세요.

---

## 🎯 학습 목표

| 모듈 | 주제 | 핵심 기술 |
|------|------|-----------|
| **모듈 0** | [Azure 리소스 사전 준비](./module0-setup/) | `az CLI` 자동화 스크립트 (Foundry, 모델 배포, AI Search, 연결) |
| **모듈 1** | [Agent SDK v2 기본](./module1-agent-sdk/) | `azure-ai-agents`, Agent/Thread/Run |
| **모듈 2** | [MCP 서버 연결](./module2-mcp-server/) | MCP 프로토콜, stdio 클라이언트 + Azure OpenAI Function Calling |
| **모듈 3** | [Foundry IQ RAG](./module3-foundry-iq-rag/) | 지식 베이스, Agentic RAG |
| **모듈 4** | [Agent Framework 워크플로우](./module4-agent-framework/) | Handoff, GroupChat, 그래프 워크플로우 |

## 📋 사전 준비

### 필수 요구 사항
- **Python 3.10+**
- **Azure 구독** (Azure AI Foundry 프로젝트 생성 완료)
- **Azure CLI 2.81.0+** — `az login` 완료, 모듈 0 자동화 스크립트가 이 버전 이상의 Foundry 명령을 사용합니다 (`az upgrade --yes`로 최신화 권장)
- **Azure AI Foundry 프로젝트** (모델 배포 완료, 예: `gpt-4o`)

### 환경 설정

```bash
# 1. 리포지토리 클론
git clone <이 리포지토리 URL>
cd copilot-cli-foundry-agents

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

**옵션 A — 자동화 (권장):** [모듈 0 setup.sh](./module0-setup/) 실행

```bash
cd module0-setup
chmod +x setup.sh
WRITE_ENV=1 ./setup.sh   # 리소스 생성 + 루트 .env 자동 기록
```

**옵션 B — 수동:**

1. [Azure AI Foundry 포털](https://ai.azure.com)에서 프로젝트 생성
2. **프로젝트 엔드포인트** 확인 (예: `https://<resource>.services.ai.azure.com/api/projects/<project>`)
3. GPT-4o 모델 배포
4. AI Search 서비스 생성 및 프로젝트에 연결 (모듈 3용)
5. 프로젝트 엔드포인트와 모델 배포 이름을 `.env`에 기록

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
│  │ Agent  │  │ Handoff  │  │ GroupChat │  │ 순차    │ │
│  │ 정의   │  │ 워크플로우│  │ 워크플로우│  │ 워크플로우│ │
│  └────────┘  └──────────┘  └───────────┘  └──────────┘ │
└──────────────────────────────────────────────────────────┘
```

## 📂 프로젝트 구조

```
├── README.md                          # 이 파일
├── .env.example                       # 환경변수 템플릿
├── requirements.txt                   # 공통 의존성
├── module0-setup/                    # 모듈 0: Azure 리소스 사전 준비 (az CLI)
├── module1-agent-sdk/                 # 모듈 1: Agent SDK v2
├── module2-mcp-server/               # 모듈 2: MCP 서버 연결
├── module3-foundry-iq-rag/           # 모듈 3: Foundry IQ RAG
├── module4-agent-framework/          # 모듈 4: Agent Framework
└── docs/                             # 아키텍처 문서
```

## 🚀 모듈별 실습 순서

**모듈 0 (사전 준비) → 모듈 1 → 모듈 2 → 모듈 3 → 모듈 4** 순서를 권장합니다.
모듈 0은 한 번만 실행하면 됩니다 (실습이 끝나면 `cleanup.sh`로 정리).
각 학습 모듈은 독립적으로 실행할 수 있지만, 이전 모듈의 개념을 이해하면 더 효과적입니다.

## 📚 참고 자료

### GitHub Copilot CLI
- [GitHub Copilot CLI 공식 문서](https://docs.github.com/copilot/concepts/agents/about-copilot-cli)
- [GitHub Copilot CLI 리포지토리](https://github.com/githubnext/copilot-cli)

### Microsoft AI Agent 기술 스택
- [Azure AI Foundry 공식 문서](https://learn.microsoft.com/en-us/azure/foundry/)
- [Azure AI Projects SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme)
- [MCP 프로토콜 명세](https://modelcontextprotocol.io/)
- [Microsoft Agent Framework GitHub](https://github.com/microsoft/agent-framework)
- [Foundry IQ 소개](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/foundry-iq-unlocking-ubiquitous-knowledge-for-agents/4470812)
