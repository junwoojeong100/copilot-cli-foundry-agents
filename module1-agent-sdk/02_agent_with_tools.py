"""
실습 2: Code Interpreter 도구 사용
Code Interpreter를 활성화하여 에이전트가 Python 코드를 실행하고 계산을 수행하도록 합니다.
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# 상위 디렉토리의 .env 파일에서 환경 변수 로드
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def main():
    endpoint = os.environ["PROJECT_ENDPOINT"]
    model = os.environ["MODEL_DEPLOYMENT_NAME"]

    project = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )

    agent = None
    try:
        # 1단계: Code Interpreter 도구가 활성화된 에이전트 생성
        agent = project.agents.create_agent(
            model=model,
            name="code-interpreter-agent",
            instructions=(
                "당신은 데이터 분석과 수학 계산을 도와주는 AI 도우미입니다. "
                "사용자의 요청에 따라 Python 코드를 작성하고 실행하여 결과를 제공하세요. "
                "한국어로 답변하세요."
            ),
            tools=[{"type": "code_interpreter"}],
        )
        print(f"에이전트 생성 완료 (Code Interpreter 활성화): {agent.id}")

        # 2단계: 대화 스레드 생성
        thread = project.agents.threads.create()
        print(f"스레드 생성 완료: {thread.id}")

        # 3단계: 계산 요청 메시지 추가
        project.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=(
                "피보나치 수열의 처음 20개 항을 계산하고, "
                "각 항의 값을 리스트로 보여주세요. "
                "또한 황금비(피보나치 수열의 인접 항의 비율)가 어떻게 수렴하는지 설명해주세요."
            ),
        )
        print("메시지 추가 완료")

        # 4단계: Run 생성 및 실행
        run = project.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id,
        )
        print(f"Run 실행 완료 - 상태: {run.status}")

        if run.status != "completed":
            print(f"Run 실패: {run.last_error}")
            return

        # 5단계: 에이전트 응답 출력
        messages = project.agents.messages.list(thread_id=thread.id)
        print("\n=== 에이전트 응답 ===")

        for msg in reversed(messages.data):
            if msg.role == "assistant":
                for content_block in msg.content:
                    if hasattr(content_block, "text"):
                        print(f"[{msg.role}]: {content_block.text.value}")

        # 6단계: Run Steps 확인 - 에이전트가 수행한 단계와 도구 호출 내역을 조회합니다
        print("\n=== Run Steps ===")
        run_steps = project.agents.run_steps.list(thread_id=thread.id, run_id=run.id)

        for i, step in enumerate(reversed(run_steps.data), 1):
            step_type = step.type
            detail = ""

            # 도구 호출 단계인 경우 도구 유형 표시
            if step_type == "tool_calls" and step.step_details.tool_calls:
                tool_types = [tc.type for tc in step.step_details.tool_calls]
                detail = f" - {', '.join(tool_types)}"

            print(f"Step {i}: {step_type}{detail}")

    finally:
        # 7단계: 정리
        if agent is not None:
            project.agents.delete_agent(agent.id)
            print("\n에이전트 삭제 완료")


if __name__ == "__main__":
    main()
