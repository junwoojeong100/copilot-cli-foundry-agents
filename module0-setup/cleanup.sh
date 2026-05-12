#!/usr/bin/env bash
# 모듈 0 - setup.sh로 생성한 리소스 그룹 전체 삭제
#
# 사용법:
#   RG_NAME=foundry-lab-xxxxxx ./cleanup.sh
#   또는: RG_NAME=foundry-lab-xxxxxx ./cleanup.sh --yes  (확인 생략)

set -euo pipefail

RG_NAME="${RG_NAME:-}"
AUTO_YES=0
if [[ "${1:-}" == "--yes" ]]; then AUTO_YES=1; fi

if [[ -z "$RG_NAME" ]]; then
  echo "❌ RG_NAME 환경변수가 필요합니다." >&2
  echo "" >&2
  echo "사용법:" >&2
  echo "  RG_NAME=<리소스그룹명> ./cleanup.sh" >&2
  echo "" >&2
  echo "현재 구독의 foundry-lab-* 리소스 그룹 목록:" >&2
  az group list --query "[?starts_with(name, 'foundry-lab-')].name" -o tsv >&2 || true
  exit 1
fi

if ! az group show --name "$RG_NAME" >/dev/null 2>&1; then
  echo "❌ '$RG_NAME' 리소스 그룹을 찾을 수 없습니다." >&2
  exit 1
fi

echo "⚠️  '$RG_NAME' 리소스 그룹과 그 안의 모든 리소스를 삭제합니다."
if [[ "$AUTO_YES" -ne 1 ]]; then
  read -p "정말 삭제하시겠습니까? (yes/no): " CONFIRM
  if [[ "$CONFIRM" != "yes" ]]; then
    echo "취소되었습니다."
    exit 0
  fi
fi

echo "🗑️  삭제 중... (백그라운드, 수 분 소요)"
az group delete --name "$RG_NAME" --yes --no-wait
echo "✅ 삭제 명령이 시작되었습니다."
echo "   진행 상황 확인: az group show --name $RG_NAME"
