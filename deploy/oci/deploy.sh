#!/usr/bin/env bash
# 판정 API를 OCI VM에 배포한다 (Caddy /laya/* → 127.0.0.1:8790). 대본이나 서버 코드를 고친 뒤 다시 실행.
#   deploy/oci/deploy.sh [user@host] [ssh key]
set -euo pipefail
TARGET="${1:-ubuntu@168.107.48.33}"
KEY="${2:-$HOME/.ssh/ofa_match}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/app/server"
cp "$ROOT"/server/*.py "$STAGE/app/server/"
cp -r "$ROOT/story" "$STAGE/app/story"
cp "$ROOT/space/requirements.txt" "$ROOT"/deploy/oci/{install.sh,visual-laya-judge.service,visual-laya.caddy} "$STAGE/"

tar -C "$STAGE" -czf - . | ssh -i "$KEY" "$TARGET" "rm -rf /tmp/visual-laya-deploy && mkdir -p /tmp/visual-laya-deploy && tar -xzf - -C /tmp/visual-laya-deploy"
ssh -i "$KEY" "$TARGET" "sudo bash /tmp/visual-laya-deploy/install.sh"
