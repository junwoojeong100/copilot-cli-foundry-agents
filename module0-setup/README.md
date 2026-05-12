# 모듈 0 — Azure 리소스 사전 준비 (az CLI 자동화)

모듈 1~4 실습에 필요한 Azure 리소스를 az CLI 한 번에 생성/삭제합니다.

## 생성되는 리소스

| # | 리소스 | 용도 |
|---|--------|------|
| 1 | 리소스 그룹 | 전체 컨테이너 |
| 2 | Azure AI Foundry (AIServices 계정) | 모듈 1~4 공통 |
| 3 | Foundry 프로젝트 | Agent SDK 호출 대상 |
| 4 | 모델 배포 (gpt-4o) | 모든 모듈 |
| 5 | Azure AI Search (Basic + Semantic Free) | 모듈 3 RAG 인덱싱 |
| 6 | 프로젝트 ↔ AI Search 연결 (keyless AAD) | 모듈 3 RAG 호출 |

## 사전 준비

> **Azure CLI 2.81.0 이상 필수** (테스트 버전: 2.86.0)
> Foundry 프로젝트 관련 명령(`account project create`, `--allow-project-management` 등)이
> 2.78부터 도입되었고, 2.81 이상에서 안정적으로 동작합니다.

```bash
# 1. Azure CLI 버전 확인 (2.81.0 미만이면 업그레이드)
az version
az upgrade --yes      # 필요 시

# 2. 로그인
az login

# 3. 사용할 구독 선택
az account set --subscription "<subscription-name-or-id>"

# 4. 리소스 공급자 등록 (한 번만)
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.Search
```

> **쿼터**: gpt-4o `GlobalStandard` 50K TPM 이상이 필요합니다.
> 부족하면 `MODEL_CAPACITY=10` 또는 `MODEL_SKU=Standard`로 줄여 실행하세요.

## 실행

```bash
cd module0-setup
chmod +x setup.sh cleanup.sh

# 기본 설정으로 생성 (지역 eastus, 리소스명 자동 생성)
./setup.sh

# 옵션 — 환경변수로 커스터마이즈
LOCATION=koreacentral \
RG_NAME=my-foundry-rg \
FOUNDRY_NAME=my-foundry-001 \
PROJECT_NAME=my-project \
MODEL_CAPACITY=10 \
./setup.sh

# .env 파일에 자동 기록까지 한 번에
WRITE_ENV=1 ./setup.sh
```

스크립트 마지막에 `.env`에 복사할 값이 출력됩니다. `WRITE_ENV=1` 지정 시 프로젝트 루트의 `.env`를 자동으로 작성합니다.

## 수동 마무리 단계 (모듈 3 RAG용)

지식 베이스(Knowledge Base) 생성은 현재 Foundry 포털에서만 지원합니다.

1. https://ai.azure.com 접속 → 위 스크립트로 만든 프로젝트 선택
2. 좌측 메뉴 **지식 베이스(Knowledge Bases)** → **+ 새 지식 베이스**
3. 이름: `smarttech-kb` (기본값) 또는 `.env`의 `KNOWLEDGE_BASE_NAME`
4. 연결된 AI Search: `search-connection` 선택
5. 파일 업로드: `module3-foundry-iq-rag/sample_data/sample_docs.md`
6. 인덱싱 완료 대기 (1~5분)
7. (선택) `python module3-foundry-iq-rag/01_create_knowledge_base.py`로 검증

## 정리

```bash
# 리소스 그룹과 그 안의 모든 리소스 삭제 (백그라운드)
RG_NAME=foundry-lab-xxxxxx ./cleanup.sh

# 확인 프롬프트 생략
RG_NAME=foundry-lab-xxxxxx ./cleanup.sh --yes
```

## 비용 안내 (예상)

| 리소스 | SKU | 시간당 (USD) |
|--------|-----|--------------|
| Foundry (AIServices) | S0 | 무료 (사용량 과금) |
| gpt-4o GlobalStandard | — | $2.5/1M input, $10/1M output 토큰 |
| AI Search Basic | Basic | ~$0.10 |
| Semantic Search | Free | $0 (월 1,000건) |

> 실습이 끝나면 반드시 `cleanup.sh`로 정리하세요.

## 트러블슈팅

| 에러 | 해결 |
|------|------|
| `'project' is misspelled or not recognized` | az CLI가 2.81 미만입니다. `az upgrade --yes` 실행 |
| `unrecognized arguments: --allow-project-management` | 위와 동일 (az CLI 업그레이드) |
| `Quota exceeded for gpt-4o` | `MODEL_CAPACITY=10` 또는 `MODEL_SKU=Standard`로 재시도 |
| `Custom domain name already exists` | `FOUNDRY_NAME`을 다른 값으로 변경 (전 세계 고유) |
| `RoleAssignment ... already exists` | 무시해도 됩니다 (스크립트가 `\|\| true`로 처리) |
| `principal does not exist` (역할 부여) | 약 1분 후 재실행 (AAD 전파 지연) |
| Foundry 프로젝트 생성 실패 | `az cognitiveservices account show ... --query "properties.allowProjectManagement"` 확인 |
