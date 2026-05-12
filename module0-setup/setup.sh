#!/usr/bin/env bash
# 모듈 0 - 실습용 Azure 리소스 일괄 생성 스크립트
#
# 요구 사항:
#   - Azure CLI 2.81.0 이상 (테스트: 2.86.0)
#   - 'az login' 완료
#   - 구독에 Microsoft.CognitiveServices, Microsoft.Search 공급자 등록
#
# 생성 리소스:
#   1. 리소스 그룹
#   2. Azure AI Foundry 리소스 (Microsoft.CognitiveServices/accounts, kind=AIServices)
#   3. Foundry 프로젝트
#   4. 모델 배포 (기본: gpt-4o)
#   5. Azure AI Search 서비스 (Basic + Semantic Free)
#   6. Foundry 프로젝트 → AI Search 연결 (AAD keyless)
#
# 사용법:
#   ./setup.sh                       # 기본 설정으로 실행
#   LOCATION=koreacentral ./setup.sh # 위치 변경
#   WRITE_ENV=1 ./setup.sh           # ../.env 파일에도 결과 자동 기록

set -euo pipefail

# ───── 설정값 (환경변수로 오버라이드 가능) ─────
SUFFIX="${SUFFIX:-$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 6)}"
LOCATION="${LOCATION:-eastus}"
RG_NAME="${RG_NAME:-foundry-lab-${SUFFIX}}"
FOUNDRY_NAME="${FOUNDRY_NAME:-foundry-lab-${SUFFIX}}"
PROJECT_NAME="${PROJECT_NAME:-lab-project}"
MODEL_NAME="${MODEL_NAME:-gpt-4o}"
MODEL_VERSION="${MODEL_VERSION:-2024-11-20}"
MODEL_DEPLOYMENT_NAME="${MODEL_DEPLOYMENT_NAME:-gpt-4o}"
MODEL_SKU="${MODEL_SKU:-GlobalStandard}"
MODEL_CAPACITY="${MODEL_CAPACITY:-50}"
SEARCH_NAME="${SEARCH_NAME:-search-lab-${SUFFIX}}"
SEARCH_SKU="${SEARCH_SKU:-basic}"
CONNECTION_NAME="${CONNECTION_NAME:-search-connection}"
KNOWLEDGE_BASE_NAME="${KNOWLEDGE_BASE_NAME:-smarttech-kb}"
WRITE_ENV="${WRITE_ENV:-0}"
MIN_AZ_VERSION="${MIN_AZ_VERSION:-2.81.0}"

# ───── 사전 점검 ─────
if ! command -v az >/dev/null 2>&1; then
  echo "❌ az CLI가 설치되어 있지 않습니다. https://learn.microsoft.com/cli/azure/install-azure-cli 참고" >&2
  exit 1
fi

# az 버전 점검
AZ_VERSION=$(az version --query '"azure-cli"' -o tsv 2>/dev/null || echo "0.0.0")
ver_lt() {
  # $1 < $2 인지 (semver 비교)
  [[ "$(printf '%s\n%s' "$1" "$2" | sort -V | head -1)" == "$1" && "$1" != "$2" ]]
}
if ver_lt "$AZ_VERSION" "$MIN_AZ_VERSION"; then
  echo "❌ Azure CLI ${MIN_AZ_VERSION} 이상이 필요합니다 (현재: ${AZ_VERSION})." >&2
  echo "   업그레이드: az upgrade --yes" >&2
  exit 1
fi

if ! az account show >/dev/null 2>&1; then
  echo "❌ az login이 필요합니다. 'az login' 후 다시 실행하세요." >&2
  exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo "🧰 Azure CLI ${AZ_VERSION}"
echo "📋 현재 구독: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"
echo "📍 위치:     $LOCATION"
echo "📦 RG:       $RG_NAME"
echo ""

# ───── 1. 리소스 그룹 ─────
echo "📦 [1/6] 리소스 그룹 생성 중: $RG_NAME"
az group create --name "$RG_NAME" --location "$LOCATION" -o none

# ───── 2. Foundry 리소스 ─────
echo "🏗️  [2/6] Foundry 리소스 생성 중: $FOUNDRY_NAME"
az cognitiveservices account create \
  --name "$FOUNDRY_NAME" \
  --resource-group "$RG_NAME" \
  --kind AIServices \
  --sku S0 \
  --location "$LOCATION" \
  --custom-domain "$FOUNDRY_NAME" \
  --allow-project-management true \
  --assign-identity \
  --yes -o none

# ───── 3. Foundry 프로젝트 ─────
echo "📂 [3/6] Foundry 프로젝트 생성 중: $PROJECT_NAME"
az cognitiveservices account project create \
  --name "$FOUNDRY_NAME" \
  --resource-group "$RG_NAME" \
  --project-name "$PROJECT_NAME" \
  --location "$LOCATION" -o none

PROJECT_ENDPOINT="https://${FOUNDRY_NAME}.services.ai.azure.com/api/projects/${PROJECT_NAME}"
AZURE_OPENAI_ENDPOINT="https://${FOUNDRY_NAME}.openai.azure.com/"

# ───── 4. 모델 배포 ─────
echo "🤖 [4/6] 모델 배포 중: ${MODEL_NAME} v${MODEL_VERSION} → ${MODEL_DEPLOYMENT_NAME}"
az cognitiveservices account deployment create \
  --name "$FOUNDRY_NAME" \
  --resource-group "$RG_NAME" \
  --deployment-name "$MODEL_DEPLOYMENT_NAME" \
  --model-name "$MODEL_NAME" \
  --model-version "$MODEL_VERSION" \
  --model-format OpenAI \
  --sku-name "$MODEL_SKU" \
  --sku-capacity "$MODEL_CAPACITY" -o none

# ───── 5. Azure AI Search ─────
echo "🔎 [5/6] Azure AI Search 생성 중: $SEARCH_NAME (SKU: $SEARCH_SKU)"
az search service create \
  --name "$SEARCH_NAME" \
  --resource-group "$RG_NAME" \
  --sku "$SEARCH_SKU" \
  --location "$LOCATION" \
  --auth-options aadOrApiKey \
  --semantic-search free -o none

SEARCH_ENDPOINT="https://${SEARCH_NAME}.search.windows.net"
SEARCH_ID=$(az search service show --name "$SEARCH_NAME" --resource-group "$RG_NAME" --query id -o tsv)

# Foundry 프로젝트/계정 시스템 ID 조회
PROJECT_PRINCIPAL_ID=$(az cognitiveservices account project show \
  --name "$FOUNDRY_NAME" \
  --resource-group "$RG_NAME" \
  --project-name "$PROJECT_NAME" \
  --query identity.principalId -o tsv 2>/dev/null || echo "")
ACCOUNT_PRINCIPAL_ID=$(az cognitiveservices account show \
  --name "$FOUNDRY_NAME" \
  --resource-group "$RG_NAME" \
  --query identity.principalId -o tsv 2>/dev/null || echo "")

# AAD 식별자 전파 대기 (신규 ID 즉시 할당 시 PrincipalNotFound 방지)
echo "   ⏳ AAD 복제 전파 대기 (15초)..."
sleep 15

assign_role() {
  local principal_id="$1"
  local principal_type="$2"
  local role="$3"
  local scope="$4"
  [[ -z "$principal_id" ]] && return 0
  az role assignment create \
    --assignee-object-id "$principal_id" \
    --assignee-principal-type "$principal_type" \
    --role "$role" \
    --scope "$scope" -o none 2>/dev/null || true
}

echo "   🔐 Foundry 프로젝트/계정 시스템 ID에 Search 권한 부여 중..."
for pid in "$PROJECT_PRINCIPAL_ID" "$ACCOUNT_PRINCIPAL_ID"; do
  assign_role "$pid" "ServicePrincipal" "Search Index Data Contributor" "$SEARCH_ID"
  assign_role "$pid" "ServicePrincipal" "Search Service Contributor" "$SEARCH_ID"
done

# 현재 사용자에게도 Search 권한 부여 (모듈 3 01_create_knowledge_base.py 실행용)
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv 2>/dev/null || echo "")
if [[ -n "$USER_OBJECT_ID" ]]; then
  echo "   🔐 현재 사용자에게 Search/Foundry 권한 부여 중..."
  assign_role "$USER_OBJECT_ID" "User" "Search Index Data Contributor" "$SEARCH_ID"
  assign_role "$USER_OBJECT_ID" "User" "Search Service Contributor" "$SEARCH_ID"
  PROJECT_ID="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RG_NAME}/providers/Microsoft.CognitiveServices/accounts/${FOUNDRY_NAME}/projects/${PROJECT_NAME}"
  assign_role "$USER_OBJECT_ID" "User" "Azure AI User" "$PROJECT_ID"
fi

# ───── 6. Foundry 프로젝트 → AI Search 연결 ─────
echo "🔗 [6/6] Foundry 프로젝트에 AI Search 연결 추가 중: $CONNECTION_NAME"
CONNECTION_FILE=$(mktemp -t foundry-connection.XXXXXX.json)
cat >"$CONNECTION_FILE" <<EOF
{
  "properties": {
    "category": "CognitiveSearch",
    "target": "${SEARCH_ENDPOINT}",
    "authType": "AAD"
  }
}
EOF
az cognitiveservices account project connection create \
  --name "$FOUNDRY_NAME" \
  --resource-group "$RG_NAME" \
  --project-name "$PROJECT_NAME" \
  --connection-name "$CONNECTION_NAME" \
  --file "$CONNECTION_FILE" -o none
rm -f "$CONNECTION_FILE"

# ───── 결과 출력 ─────
ENV_CONTENT=$(cat <<EOF
# 모듈 0 setup.sh로 생성됨 ($(date '+%Y-%m-%d %H:%M:%S'))
# 리소스 그룹: ${RG_NAME}

PROJECT_ENDPOINT=${PROJECT_ENDPOINT}
MODEL_DEPLOYMENT_NAME=${MODEL_DEPLOYMENT_NAME}

# 모듈 2 (Azure OpenAI 직접 호출)
AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
AZURE_OPENAI_DEPLOYMENT_NAME=${MODEL_DEPLOYMENT_NAME}

# 모듈 3 (Foundry IQ RAG)
SEARCH_SERVICE_ENDPOINT=${SEARCH_ENDPOINT}
KNOWLEDGE_BASE_NAME=${KNOWLEDGE_BASE_NAME}
PROJECT_CONNECTION_NAME=${CONNECTION_NAME}
EOF
)

cat <<EOF

============================================================
✅ 모든 리소스 생성이 완료되었습니다!

📌 .env 값:
------------------------------------------------------------
${ENV_CONTENT}
------------------------------------------------------------

📌 다음 단계 (모듈 3 실습용 — 포털에서 수동 작업):
  1. https://ai.azure.com 접속 → 프로젝트 '${PROJECT_NAME}' 선택
  2. 왼쪽 메뉴 '지식 베이스(Knowledge Bases)' → '+ 새 지식 베이스'
  3. 이름: '${KNOWLEDGE_BASE_NAME}'
  4. 연결된 AI Search: '${CONNECTION_NAME}' 선택
  5. 파일 업로드: module3-foundry-iq-rag/sample_data/sample_docs.md
  6. 인덱싱 완료 대기 (1~5분)

🧹 모든 리소스 정리:
  RG_NAME=${RG_NAME} ./module0-setup/cleanup.sh
============================================================
EOF

# ───── (옵션) .env 파일에 기록 ─────
if [[ "$WRITE_ENV" == "1" ]]; then
  ENV_PATH="$(cd "$(dirname "$0")/.." && pwd)/.env"
  echo "$ENV_CONTENT" > "$ENV_PATH"
  echo ""
  echo "📝 .env 파일에 기록 완료: $ENV_PATH"
fi
