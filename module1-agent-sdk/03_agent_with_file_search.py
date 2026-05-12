"""
실습 3: File Search 도구 사용
벡터 스토어에 문서를 업로드하고, File Search를 활용하여 문서 기반 Q&A를 수행합니다.
"""

import os
from pathlib import Path

from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# 상위 디렉토리의 .env 파일에서 환경 변수 로드
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# 샘플 문서 내용 - 실습용 한국어 텍스트
SAMPLE_DOCUMENT = """# Azure AI Foundry 개요

## Azure AI Foundry란?
Azure AI Foundry는 Microsoft의 통합 AI 개발 플랫폼입니다.
개발자와 데이터 과학자가 AI 애플리케이션을 빌드, 테스트, 배포할 수 있는 환경을 제공합니다.

## 주요 기능
1. **모델 카탈로그**: OpenAI, Meta, Mistral 등 다양한 AI 모델을 선택하여 사용할 수 있습니다.
2. **프롬프트 플로우**: 시각적 도구를 사용하여 LLM 기반 워크플로우를 설계할 수 있습니다.
3. **에이전트 서비스**: Agent SDK를 통해 도구 사용이 가능한 AI 에이전트를 만들 수 있습니다.
4. **평가 도구**: AI 모델의 성능, 안전성, 품질을 평가할 수 있는 기본 제공 도구가 있습니다.
5. **안전 기능**: 콘텐츠 필터링, 그라운딩 감지 등 AI 안전 기능이 내장되어 있습니다.

## Agent SDK v2
Agent SDK v2는 Azure AI Foundry의 에이전트 서비스를 위한 Python SDK입니다.
주요 특징:
- Agent, Thread, Message, Run 기반의 대화 모델
- Code Interpreter, File Search 등 내장 도구 지원
- Function Calling을 통한 사용자 정의 도구 통합
- Bing Grounding, Azure AI Search 등 엔터프라이즈 도구 연동

## 지원 모델
- GPT-4o / GPT-4o mini
- GPT-4 Turbo
- GPT-3.5 Turbo
- 기타 Azure AI 모델 카탈로그의 모델
"""


def main():
    endpoint = os.environ["PROJECT_ENDPOINT"]
    model = os.environ["MODEL_DEPLOYMENT_NAME"]

    client = AgentsClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )

    agent = None
    vector_store = None
    sample_file_path = Path(__file__).parent / "_sample_document.txt"

    try:
        # 1단계: 샘플 문서 파일 생성
        sample_file_path.write_text(SAMPLE_DOCUMENT, encoding="utf-8")
        print("샘플 문서 파일 생성 완료")

        # 2단계: 벡터 스토어 생성 - File Search에서 사용할 벡터 저장소를 만듭니다
        vector_store = client.vector_stores.create(
            name="module1-sample-store",
        )
        print(f"벡터 스토어 생성 완료: {vector_store.id}")

        # 3단계: 파일 업로드 - 문서를 에이전트 서비스에 업로드합니다
        with open(sample_file_path, "rb") as f:
            uploaded_file = client.files.upload(
                file=f,
                purpose="agents",
            )
        print(f"파일 업로드 완료: {uploaded_file.id}")

        # 4단계: 벡터 스토어에 파일 등록 - 업로드된 파일을 벡터 스토어에 추가하고 인덱싱합니다
        file_batch = client.vector_store_file_batches.create_and_poll(
            vector_store_id=vector_store.id,
            file_ids=[uploaded_file.id],
        )
        print(f"파일 벡터화 완료 - 상태: {file_batch.status}")

        # 5단계: File Search 도구가 활성화된 에이전트 생성
        # tool_resources로 벡터 스토어를 에이전트에 연결합니다
        agent = client.create_agent(
            model=model,
            name="file-search-agent",
            instructions=(
                "당신은 제공된 문서를 기반으로 질문에 답변하는 AI 도우미입니다. "
                "File Search 도구를 사용하여 문서에서 관련 정보를 찾아 답변하세요. "
                "한국어로 답변하고, 문서에 없는 내용은 '문서에서 해당 정보를 찾을 수 없습니다'라고 답하세요."
            ),
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store.id],
                }
            },
        )
        print(f"에이전트 생성 완료 (File Search 활성화): {agent.id}")

        # 6단계: 대화 스레드 생성 및 질문
        thread = client.threads.create()
        print(f"스레드 생성 완료: {thread.id}")

        # 문서 내용에 대한 질문 추가
        client.messages.create(
            thread_id=thread.id,
            role="user",
            content="Azure AI Foundry의 주요 기능 5가지를 정리해주세요. 그리고 Agent SDK v2의 특징도 알려주세요.",
        )
        print("메시지 추가 완료")

        # 7단계: Run 실행 - 에이전트가 File Search를 통해 문서를 검색하고 답변합니다
        run = client.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id,
        )
        print(f"Run 실행 완료 - 상태: {run.status}")

        if run.status != "completed":
            print(f"Run 실패: {run.last_error}")
            return

        # 8단계: 응답 출력
        messages = client.messages.list(thread_id=thread.id)
        print("\n=== 에이전트 응답 ===")

        for msg in reversed(messages.data):
            if msg.role == "assistant":
                for content_block in msg.content:
                    if hasattr(content_block, "text"):
                        print(f"[{msg.role}]: {content_block.text.value}")

                        # 인용(annotation) 정보가 있으면 출력
                        if content_block.text.annotations:
                            print("\n--- 참조 ---")
                            for annotation in content_block.text.annotations:
                                if hasattr(annotation, "file_citation"):
                                    print(
                                        f"  📄 파일 인용: {annotation.file_citation.file_id}"
                                    )

    finally:
        # 9단계: 정리 - 생성한 리소스를 삭제합니다
        if agent is not None:
            client.delete_agent(agent.id)
            print("\n에이전트 삭제 완료")

        if vector_store is not None:
            client.vector_stores.delete(vector_store.id)
            print("벡터 스토어 삭제 완료")

        # 임시 샘플 파일 삭제
        if sample_file_path.exists():
            sample_file_path.unlink()
            print("샘플 문서 파일 삭제 완료")


if __name__ == "__main__":
    main()
