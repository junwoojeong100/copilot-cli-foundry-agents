"""
실습 1: 기본 에이전트 생성 및 대화
Azure AI Foundry Agent SDK v2를 사용하여 가장 기본적인 에이전트를 생성하고 대화합니다.
"""

import os
from pathlib import Path

from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# 상위 디렉토리의 .env 파일에서 환경 변수 로드
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def main():
    # 환경 변수에서 프로젝트 엔드포인트와 모델 배포 이름 가져오기
    endpoint = os.environ["PROJECT_ENDPOINT"]
    model = os.environ["MODEL_DEPLOYMENT_NAME"]

    # Azure 기본 자격 증명으로 AgentsClient 생성
    client = AgentsClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )

    agent = None
    try:
        # 1단계: 에이전트 생성 - 모델, 이름, 지침을 지정합니다
        agent = client.create_agent(
            model=model,
            name="hello-agent",
            instructions=(
                "당신은 친절한 AI 도우미입니다. "
                "사용자의 질문에 한국어로 명확하고 간결하게 답변하세요."
            ),
        )
        print(f"에이전트 생성 완료: {agent.id}")

        # 2단계: 대화 스레드 생성 - 에이전트와의 대화 세션을 시작합니다
        thread = client.threads.create()
        print(f"스레드 생성 완료: {thread.id}")

        # 3단계: 사용자 메시지 추가 - 스레드에 사용자의 질문을 추가합니다
        client.messages.create(
            thread_id=thread.id,
            role="user",
            content="안녕하세요! Azure AI Foundry Agent SDK가 무엇인지 간단히 설명해주세요.",
        )
        print("메시지 추가 완료")

        # 4단계: Run 생성 및 실행 - 에이전트가 메시지를 처리하도록 합니다
        # create_and_process()는 Run이 완료될 때까지 자동으로 폴링합니다
        run = client.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id,
        )
        print(f"Run 실행 완료 - 상태: {run.status}")

        # Run 실패 시 오류 정보 출력
        if run.status != "completed":
            print(f"Run 실패: {run.last_error}")
            return

        # 5단계: 응답 메시지 조회 - 스레드의 모든 메시지를 가져옵니다
        messages = list(client.messages.list(thread_id=thread.id))
        print("\n=== 에이전트 응답 ===")

        # 메시지를 역순으로 순회하여 최신 에이전트 응답 출력
        for msg in reversed(messages):
            if msg.role == "assistant":
                for content_block in msg.content:
                    if hasattr(content_block, "text"):
                        print(f"[{msg.role}]: {content_block.text.value}")

    finally:
        # 6단계: 정리 - 생성한 에이전트를 삭제합니다
        if agent is not None:
            client.delete_agent(agent.id)
            print("\n에이전트 삭제 완료")


if __name__ == "__main__":
    main()
