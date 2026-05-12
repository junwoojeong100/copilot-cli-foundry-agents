# 모듈 2: MCP 서버 연결

## 🎯 학습 목표

이 모듈을 완료하면 다음을 할 수 있습니다:

- **MCP(Model Context Protocol)**의 핵심 개념을 이해한다
- 간단한 MCP 서버를 직접 구현하고 실행한다
- Azure AI Foundry Agent에 MCP 서버를 연결하여 외부 도구를 사용한다

---

## 📖 MCP(Model Context Protocol) 핵심 개념

### MCP란 무엇인가?

MCP(Model Context Protocol)는 AI 모델이 외부 도구, 데이터 소스, 서비스와 **표준화된 방식**으로 통신할 수 있게 해주는 개방형 프로토콜입니다.

> 💡 **"AI의 USB-C"** — USB-C가 다양한 기기를 하나의 표준 커넥터로 연결하듯, MCP는 다양한 AI 도구를 하나의 표준 프로토콜로 연결합니다.

### 핵심 특징

| 특징 | 설명 |
|------|------|
| **JSON-RPC 2.0 기반** | 표준화된 요청/응답 형식으로 통신합니다 |
| **도구 자동 발견** | 클라이언트가 서버에 연결하면 사용 가능한 도구 목록을 자동으로 발견합니다 |
| **전송 독립적** | stdio, HTTP(SSE), WebSocket 등 다양한 전송 방식을 지원합니다 |
| **양방향 통신** | 클라이언트와 서버가 양방향으로 메시지를 주고받습니다 |

### MCP 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    AI Application                       │
│  (Azure AI Foundry Agent / GitHub Copilot / Claude)     │
└──────────────────────┬──────────────────────────────────┘
                       │  MCP Protocol (JSON-RPC 2.0)
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  MCP Server  │ │  MCP Server  │ │  MCP Server  │
│   (날씨)     │ │  (데이터베이스)│ │   (검색)     │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       ▼                ▼                ▼
  [Weather API]    [Database]     [Search Engine]
```

### MCP 통신 흐름

```
클라이언트 (Agent)              MCP 서버 (Weather)
      │                              │
      │──── initialize ──────────────▶│  1. 연결 초기화
      │◀─── capabilities ────────────│  2. 서버 기능 응답
      │                              │
      │──── tools/list ──────────────▶│  3. 도구 목록 요청
      │◀─── [get_weather, ...] ──────│  4. 사용 가능한 도구 반환
      │                              │
      │──── tools/call ──────────────▶│  5. 도구 실행 요청
      │     {name: "get_weather",     │     (get_weather 호출)
      │      args: {city: "서울"}}    │
      │◀─── result ──────────────────│  6. 실행 결과 반환
      │     "서울: 맑음, 22°C"        │
      │                              │
```

---

## 🔧 사전 준비

### 1. 필수 패키지 설치

```bash
# 프로젝트 루트에서 실행
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트의 `.env` 파일에 다음 값이 설정되어 있어야 합니다:

```env
PROJECT_ENDPOINT=https://<your-project>.services.ai.azure.com/api/projects/<project-name>
MODEL_DEPLOYMENT_NAME=gpt-4o

# 실습 2에서 사용 (Azure OpenAI 직접 연결)
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

### 3. Azure 인증

```bash
# Azure CLI로 로그인
az login
```

---

## 🧪 실습 1: 간단한 MCP 서버 구현

### 파일: `mcp_server/weather_server.py`

이 실습에서는 날씨 정보를 제공하는 간단한 MCP 서버를 구현합니다.

#### 주요 구성 요소

1. **FastMCP 서버 생성**: `mcp` 라이브러리의 `FastMCP`를 사용하여 서버 인스턴스를 생성합니다
2. **도구(Tool) 정의**: `@mcp.tool()` 데코레이터로 AI가 호출할 수 있는 함수를 등록합니다
3. **서버 실행**: stdio 전송 방식으로 서버를 시작합니다

#### 핵심 코드 설명

```python
from mcp.server.fastmcp import FastMCP

# MCP 서버 인스턴스 생성
mcp = FastMCP("weather")

# 도구 등록 - AI가 이 함수를 자동으로 발견하고 호출할 수 있습니다
@mcp.tool()
def get_weather(city: str) -> str:
    """도시의 현재 날씨를 조회합니다."""
    return f"{city}: 맑음, 22°C"
```

#### 실행 방법

```bash
# MCP 서버 직접 실행 (stdio 모드)
python mcp_server/weather_server.py
```

### 파일: `01_mcp_server_basic.py`

MCP 서버를 프로그래밍 방식으로 시작하고 클라이언트로 테스트하는 스크립트입니다.

#### 실행 방법

```bash
cd module2-mcp-server
python 01_mcp_server_basic.py
```

#### 예상 출력

```
🔧 MCP 서버 기본 테스트
============================================================

📡 MCP 서버에 연결 중...
✅ 서버 연결 성공!

📋 사용 가능한 도구 목록:
  - get_weather: 도시의 현재 날씨를 조회합니다.
  - get_forecast: 도시의 날씨 예보를 조회합니다.

🌤️ 도구 호출 테스트: get_weather("서울")
📍 결과: 서울의 현재 날씨: 맑음, 22°C, 습도 45%

📅 도구 호출 테스트: get_forecast("부산", days=5)
📍 결과: ...

✅ MCP 서버 기본 테스트 완료!
```

---

## 🧪 실습 2: Azure OpenAI + MCP 서버를 결합한 AI 에이전트

### 파일: `02_agent_with_mcp.py`

이 실습에서는 **Azure OpenAI Function Calling**과 **로컬 MCP 서버(stdio)**를 결합하여 AI 에이전트를 구현합니다. 스크립트가 직접 MCP 서버 프로세스를 자식으로 띄우기 때문에 **별도 터미널에서 서버를 미리 실행할 필요가 없습니다**.

> 💡 Azure AI Foundry Agent Service의 **hosted MCP** 기능(`MCPTool`)은 모듈 3에서 다룹니다. 이 모듈은 “MCP 프로토콜을 직접 소비하는 클라이언트 + LLM 함수 호출 루프” 패턴을 학습합니다.

#### 워크플로우

```
┌──────────────────────────────────────────────┐
│  02_agent_with_mcp.py                         │
│                                               │
│   ┌───────────────────────────────────────┐  │
│   │ 1) StdioServerParameters로 서버 spawn  │  │
│   │ 2) MCP 도구 목록 자동 발견              │  │
│   │ 3) MCP → OpenAI tool schema로 변환     │  │
│   │ 4) Azure OpenAI chat.completions 호출  │  │
│   │ 5) tool_calls 발생 시 MCP에 위임 → 응답 │  │
│   │    이 흐름을 도구 호출이 끝날 때까지 반복 │  │
│   └───────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

#### 핵심 코드 설명

```python
# 1) 자식 프로세스로 MCP 서버 실행 준비 (별도 터미널 불필요)
server_params = StdioServerParameters(
    command=sys.executable,
    args=["mcp_server/weather_server.py"],
)

# 2) 세션 열기 → 도구 자동 발견
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools_result = await session.list_tools()

        # 3) MCP 도구 정의를 OpenAI Function Calling 스키마로 변환
        openai_tools = mcp_tools_to_openai(tools_result.tools)

        # 4) Azure OpenAI (Entra ID 토큰) 호출
        response = openai_client.chat.completions.create(
            model=MODEL_DEPLOYMENT_NAME,
            messages=messages,
            tools=openai_tools,
        )

        # 5) tool_calls가 있으면 MCP에 위임하고 결과를 다시 모델에 전달
        while response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                mcp_result = await session.call_tool(
                    tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments),
                )
                # 결과를 messages에 append 후 재호출 (생략)
```

#### 실행 방법

```bash
# 별도의 서버 실행 단계가 필요 없습니다.
cd module2-mcp-server
python 02_agent_with_mcp.py
```

> `weather_server.py`를 직접 실행하려면 모듈 2 첫 번째 실습(`01_mcp_server_basic.py`)을 사용하세요. 두 스크립트 모두 스스로 stdio 서버 프로세스를 띄우므로, **수동으로 weather_server.py를 띄울 필요는 없습니다**.

#### 필수 환경 변수

이 실습은 Azure OpenAI 엔드포인트를 직접 호출하므로 다음이 필요합니다(모듈 0 `setup.sh`가 자동 기록).

```env
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o          # 또는 MODEL_DEPLOYMENT_NAME으로 대체 가능
```

#### 예상 출력

```
🤖 MCP 도구를 사용하는 AI 에이전트
============================================================

📡 MCP 서버에 연결 중...
✅ MCP 서버 연결 성공!
📋 MCP에서 발견된 도구: get_weather, get_forecast
✅ Azure OpenAI 클라이언트 생성 완료

💬 사용자 질문: "서울과 부산의 날씨를 비교해주세요"
⏳ AI 에이전트 실행 중...

  🔧 도구 호출: get_weather({'city': '서울'})
  📍 결과: 서울의 현재 날씨: 맑음, 22°C, 습도 45%
  🔧 도구 호출: get_weather({'city': '부산'})
  📍 결과: 부산의 현재 날씨: 구름 많음, 25°C, 습도 60%

📨 에이전트 응답:
서울은 22°C, 맑음이고 부산은 25°C, 구름 많음입니다. ...

✅ MCP 에이전트 실습 완료!
```

---

## 🏗️ MCP 서버 아키텍처 다이어그램

```
┌───────────────────────────────────────────────────────────────┐
│                     이 모듈의 구조                              │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐        ┌─────────────────────────────┐  │
│  │ 01_mcp_server   │        │   02_agent_with_mcp.py      │  │
│  │ _basic.py       │        │                             │  │
│  │                 │        │   Azure OpenAI + MCP Client  │  │
│  │  MCP Client     │        │   (Function Calling)        │  │
│  └────────┬────────┘        └──────────────┬──────────────┘  │
│           │                                │                  │
│           │  stdio                         │  stdio            │
│           │                                │                  │
│           ▼                                ▼                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              mcp_server/weather_server.py               │  │
│  │                                                         │  │
│  │   FastMCP("weather")                                    │  │
│  │   ├── get_weather(city) → 현재 날씨 정보               │  │
│  │   └── get_forecast(city, days) → 날씨 예보             │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 📝 핵심 정리

| 개념 | 설명 |
|------|------|
| **MCP** | AI 모델과 외부 도구를 연결하는 표준 프로토콜 |
| **FastMCP** | Python으로 MCP 서버를 쉽게 만들 수 있는 라이브러리 |
| **@mcp.tool()** | 함수를 MCP 도구로 등록하는 데코레이터 |
| **stdio 전송** | 표준 입출력을 통한 MCP 통신 방식 (로컬 개발용) |
| **HTTP(SSE) 전송** | HTTP를 통한 MCP 통신 방식 (원격 서버용) |
| **`StdioServerParameters` / `stdio_client`** | MCP 서버를 자식 프로세스로 실행하고 stdio로 연결하는 Python MCP SDK API |
| **MCP → OpenAI 스키마 변환** | `tool.inputSchema`를 OpenAI Function Calling 형식으로 매핑하여 LLM에 노출 |

### MCP의 장점

1. **표준화**: 어떤 AI 플랫폼에서든 동일한 도구를 재사용할 수 있습니다
2. **자동 발견**: 도구 목록과 스키마를 서버가 자동으로 제공합니다
3. **확장성**: 새로운 도구를 서버에 추가하면 클라이언트가 자동으로 인식합니다
4. **분리**: 도구 구현과 AI 모델이 독립적으로 개발/배포됩니다

---

## ➡️ 다음 단계

MCP 서버 연결을 마스터했다면, 다음 모듈로 진행하세요:

👉 [모듈 3: Foundry IQ & RAG 통합](../module3-foundry-iq-rag/README.md) — Azure AI Foundry의 지식 기반 검색(RAG)을 Agent에 통합하는 방법을 학습합니다.
