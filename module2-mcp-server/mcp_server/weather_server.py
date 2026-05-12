"""
MCP 날씨 서버

FastMCP를 사용하여 날씨 정보를 제공하는 간단한 MCP 서버입니다.
AI 에이전트가 이 서버에 연결하면 날씨 관련 도구를 자동으로 발견하고 사용할 수 있습니다.
"""

import sys

from mcp.server.fastmcp import FastMCP

# ============================================================
# MCP 서버 인스턴스 생성
# "weather"는 서버 이름으로, 클라이언트가 서버를 식별하는 데 사용됩니다.
# ============================================================
mcp = FastMCP("weather")


# ============================================================
# 도구 1: 현재 날씨 조회
# @mcp.tool() 데코레이터로 함수를 MCP 도구로 등록합니다.
# 함수의 docstring은 도구 설명으로 사용되어 AI가 언제 이 도구를
# 사용해야 하는지 판단하는 데 도움을 줍니다.
# ============================================================
@mcp.tool()
def get_weather(city: str) -> str:
    """도시의 현재 날씨를 조회합니다.

    Args:
        city: 날씨를 조회할 도시 이름 (예: "서울", "부산", "제주")
    """
    # 실제 서비스에서는 외부 날씨 API를 호출합니다.
    # 여기서는 학습 목적으로 모의(mock) 데이터를 반환합니다.
    weather_data = {
        "서울": {"condition": "맑음", "temp": 22, "humidity": 45},
        "부산": {"condition": "구름 많음", "temp": 25, "humidity": 60},
        "제주": {"condition": "흐림", "temp": 20, "humidity": 70},
        "인천": {"condition": "맑음", "temp": 21, "humidity": 50},
        "대전": {"condition": "비", "temp": 18, "humidity": 80},
    }

    # 등록된 도시가 아니면 기본값을 반환합니다
    data = weather_data.get(city, {"condition": "맑음", "temp": 20, "humidity": 55})

    return (
        f"{city}의 현재 날씨: {data['condition']}, "
        f"{data['temp']}°C, 습도 {data['humidity']}%"
    )


# ============================================================
# 도구 2: 날씨 예보 조회
# 여러 날의 예보를 반환하는 도구입니다.
# 기본값(days=3)이 있는 매개변수는 선택적으로 사용할 수 있습니다.
# ============================================================
@mcp.tool()
def get_forecast(city: str, days: int = 3) -> str:
    """도시의 날씨 예보를 조회합니다.

    Args:
        city: 예보를 조회할 도시 이름
        days: 예보 일수 (기본값: 3, 최대: 7)
    """
    # 예보 일수를 1~7일로 제한합니다
    days = max(1, min(days, 7))

    # 모의(mock) 예보 데이터 생성
    conditions = ["맑음", "구름 조금", "구름 많음", "흐림", "비", "맑음", "맑음"]
    temps = [22, 24, 21, 19, 17, 23, 25]

    forecast_lines = [f"📅 {city}의 {days}일간 날씨 예보:"]
    for i in range(days):
        forecast_lines.append(
            f"  {i + 1}일차: {conditions[i % len(conditions)]}, "
            f"{temps[i % len(temps)]}°C"
        )

    return "\n".join(forecast_lines)


# ============================================================
# 서버 실행
# stdio 전송 방식으로 서버를 시작합니다.
# stdio는 로컬 개발에 적합하며, 표준 입출력을 통해 통신합니다.
#
# ⚠️ stdio 모드에서는 stdout이 JSON-RPC 채널로 사용되므로
# 사람이 읽을 로그/메시지는 반드시 stderr로 출력해야 합니다.
# (stdout에 한 줄이라도 비-JSON이 섞이면 클라이언트가 파싱 실패합니다)
# ============================================================
if __name__ == "__main__":
    print("🌤️ MCP 날씨 서버를 시작합니다...", file=sys.stderr)
    mcp.run(transport="stdio")
