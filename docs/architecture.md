# 전체 아키텍처

이 문서는 실습 가이드에서 다루는 Microsoft AI Agent 기술 스택의 전체 아키텍처를 설명합니다.

## 기술 스택 관계도

```mermaid
graph TB
    subgraph User["👤 사용자 / 클라이언트"]
        APP[애플리케이션 코드<br/>Python]
    end

    subgraph Foundry["☁️ Azure AI Foundry"]
        direction TB
        PROJECT[AI Foundry 프로젝트]
        AGENT_SERVICE[Agent Service<br/>에이전트 런타임]
        MODEL[모델 배포<br/>GPT-4o 등]
        
        PROJECT --> AGENT_SERVICE
        PROJECT --> MODEL
        AGENT_SERVICE --> MODEL
    end

    subgraph SDK["📦 Azure AI Projects SDK v2 (모듈 1)"]
        CLIENT[AIProjectClient]
        AGENT_API[agents.create_agent<br/>threads / messages / runs]
        CLIENT --> AGENT_API
    end

    subgraph MCP_Layer["🔌 MCP 프로토콜 (모듈 2)"]
        MCP_TOOL[MCPTool 클래스]
        MCP_SERVER[MCP 서버<br/>외부 도구/API]
        MCP_TOOL <-->|JSON-RPC| MCP_SERVER
    end

    subgraph IQ["🧠 Foundry IQ (모듈 3)"]
        KB[지식 베이스<br/>Knowledge Base]
        SEARCH[Azure AI Search<br/>하이브리드 검색]
        MCP_KB[MCP 엔드포인트<br/>knowledge_base_retrieve]
        KB --> SEARCH
        SEARCH --> MCP_KB
    end

    subgraph MAF["🔄 Microsoft Agent Framework (모듈 4)"]
        direction TB
        AF_AGENT[Agent 정의]
        HANDOFF[Handoff 워크플로우<br/>에이전트 간 위임]
        GROUPCHAT[GroupChat 워크플로우<br/>협업 토론]
        GRAPH[그래프 워크플로우<br/>조건부 라우팅]
        
        AF_AGENT --> HANDOFF
        AF_AGENT --> GROUPCHAT
        AF_AGENT --> GRAPH
    end

    APP --> CLIENT
    APP --> AF_AGENT
    AGENT_API --> AGENT_SERVICE
    AGENT_SERVICE --> MCP_TOOL
    AGENT_SERVICE --> MCP_KB
    MAF -->|Azure OpenAI| MODEL

    style User fill:#e1f5fe
    style Foundry fill:#fff3e0
    style SDK fill:#e8f5e9
    style MCP_Layer fill:#f3e5f5
    style IQ fill:#fce4ec
    style MAF fill:#e0f2f1
```

## 모듈별 데이터 흐름

### 모듈 1: Agent SDK v2 기본 흐름

```mermaid
sequenceDiagram
    participant U as 사용자
    participant C as AIProjectClient
    participant A as Agent Service
    participant M as 모델 (GPT-4o)

    U->>C: agents.create_agent()
    C->>A: 에이전트 생성
    U->>C: threads.create()
    C->>A: 스레드 생성
    U->>C: messages.create("질문")
    C->>A: 메시지 추가
    U->>C: runs.create_and_process()
    C->>A: 실행 시작
    A->>M: 프롬프트 전송
    M-->>A: 응답 생성
    A-->>C: 실행 완료
    C-->>U: 응답 메시지
```

### 모듈 2: MCP 서버 연결 흐름

```mermaid
sequenceDiagram
    participant U as 사용자
    participant A as Agent Service
    participant M as 모델
    participant MCP as MCP 서버

    U->>A: "서울 날씨 알려줘"
    A->>M: 프롬프트 + 도구 목록
    M-->>A: 도구 호출 결정
    A->>MCP: get_weather("서울")
    MCP-->>A: {"온도": "15°C", ...}
    A->>M: 도구 결과 전달
    M-->>A: 자연어 응답 생성
    A-->>U: "서울의 현재 날씨는..."
```

### 모듈 3: Foundry IQ RAG 흐름

```mermaid
sequenceDiagram
    participant U as 사용자
    participant A as Agent Service
    participant M as 모델
    participant IQ as Foundry IQ
    participant S as AI Search

    U->>A: "제품 가격이 얼마인가요?"
    A->>M: 프롬프트 + KB 도구
    M-->>A: knowledge_base_retrieve 호출
    A->>IQ: MCP 엔드포인트 호출
    IQ->>S: 하이브리드 검색
    S-->>IQ: 관련 문서 + 메타데이터
    IQ-->>A: 검색 결과 + 출처
    A->>M: 문서 컨텍스트 전달
    M-->>A: 출처 포함 응답 생성
    A-->>U: "가격은 ... 【출처】"
```

### 모듈 4: Agent Framework 워크플로우 패턴

```mermaid
graph LR
    subgraph Handoff["Handoff 패턴"]
        T[접수] -->|기술 문의| TS[기술 지원]
        T -->|결제 문의| B[결제 지원]
    end

    subgraph GroupChat["GroupChat 패턴"]
        P[기획자] <--> D[개발자]
        D <--> DS[디자이너]
        DS <--> P
    end

    subgraph Graph["그래프 워크플로우"]
        AN[분석] -->|기술| TW[기술 작가]
        AN -->|일반| GW[일반 작가]
        TW --> ED[편집자]
        GW --> ED
    end

    style Handoff fill:#e8f5e9
    style GroupChat fill:#e1f5fe
    style Graph fill:#fff3e0
```

## 기술 스택 요약

| 계층 | 기술 | 패키지 | 역할 |
|------|------|--------|------|
| **SDK** | Azure AI Projects SDK v2 | `azure-ai-projects>=2.0.0` | Foundry 에이전트 생성/관리 |
| **인증** | Azure Identity | `azure-identity` | DefaultAzureCredential |
| **도구 연결** | MCP (Model Context Protocol) | `mcp[cli]` | 외부 도구/API 연결 표준 |
| **지식 검색** | Foundry IQ + AI Search | 포털 설정 | Agentic RAG |
| **워크플로우** | Microsoft Agent Framework | `agent-framework` | 멀티에이전트 오케스트레이션 |
| **모델** | Azure OpenAI | `openai` | GPT-4o 등 LLM |
