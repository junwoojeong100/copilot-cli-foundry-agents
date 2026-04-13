"""
실습 1: MCP 서버 기본 테스트

이 스크립트는 MCP 서버를 프로그래밍 방식으로 실행하고,
클라이언트를 통해 도구 목록 조회 및 도구 호출을 테스트합니다.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ============================================================
# 환경 변수 로드 (상위 디렉토리의 .env 파일)
# ============================================================
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


async def run_mcp_test():
    """MCP 서버에 연결하여 기본 기능을 테스트합니다."""

    print("🔧 MCP 서버 기본 테스트")
    print("=" * 60)

    # ============================================================
    # 1단계: MCP 서버 프로세스 설정
    # StdioServerParameters로 서버 실행 명령을 지정합니다.
    # stdio 전송 방식은 서버를 자식 프로세스로 실행하고
    # 표준 입출력으로 통신합니다.
    # ============================================================
    server_params = StdioServerParameters(
        command=sys.executable,  # 현재 Python 인터프리터 사용
        args=[os.path.join(os.path.dirname(__file__), "mcp_server", "weather_server.py")],
    )

    print("\n📡 MCP 서버에 연결 중...")

    try:
        # ============================================================
        # 2단계: 서버에 연결하고 세션 시작
        # stdio_client가 서버 프로세스를 시작하고 통신 채널을 엽니다.
        # ClientSession으로 MCP 프로토콜 세션을 초기화합니다.
        # ============================================================
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # 세션 초기화 — 서버와 capabilities를 교환합니다
                await session.initialize()
                print("✅ 서버 연결 성공!")

                # ============================================================
                # 3단계: 사용 가능한 도구 목록 조회
                # list_tools()로 서버가 제공하는 모든 도구를 자동 발견합니다.
                # 이것이 MCP의 핵심 기능인 '도구 자동 발견'입니다.
                # ============================================================
                tools_result = await session.list_tools()
                print(f"\n📋 사용 가능한 도구 목록 ({len(tools_result.tools)}개):")
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")

                # ============================================================
                # 4단계: get_weather 도구 호출 테스트
                # call_tool()로 특정 도구를 실행하고 결과를 받습니다.
                # ============================================================
                print('\n🌤️ 도구 호출 테스트: get_weather("서울")')
                weather_result = await session.call_tool(
                    "get_weather",
                    arguments={"city": "서울"},
                )
                # 결과에서 텍스트 콘텐츠를 추출합니다
                for content in weather_result.content:
                    print(f"📍 결과: {content.text}")

                # ============================================================
                # 5단계: get_forecast 도구 호출 테스트
                # days 매개변수를 포함하여 5일 예보를 요청합니다.
                # ============================================================
                print('\n📅 도구 호출 테스트: get_forecast("부산", days=5)')
                forecast_result = await session.call_tool(
                    "get_forecast",
                    arguments={"city": "부산", "days": 5},
                )
                for content in forecast_result.content:
                    print(f"📍 결과:\n{content.text}")

                # ============================================================
                # 6단계: 등록되지 않은 도시 테스트
                # 기본값이 반환되는지 확인합니다.
                # ============================================================
                print('\n🏙️ 도구 호출 테스트: get_weather("뉴욕")')
                unknown_result = await session.call_tool(
                    "get_weather",
                    arguments={"city": "뉴욕"},
                )
                for content in unknown_result.content:
                    print(f"📍 결과: {content.text}")

        print("\n✅ MCP 서버 기본 테스트 완료!")

    except FileNotFoundError:
        print("❌ 오류: MCP 서버 파일을 찾을 수 없습니다.")
        print("   mcp_server/weather_server.py 파일이 존재하는지 확인하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise


# ============================================================
# 메인 실행 블록
# ============================================================
if __name__ == "__main__":
    asyncio.run(run_mcp_test())
