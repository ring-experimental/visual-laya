#!/usr/bin/env bash
# OCI VM에 판정 API 설치/갱신 (root로 실행, 멱등). deploy/oci/deploy.sh가 올린 묶음 안에서 실행된다.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
BASE=/opt/visual-laya
MODEL_REPO="${LAYA_VN_REPO:-ringwring/laya-vn}"

if ! grep -q 'import /etc/caddy/sites.d/' /etc/caddy/Caddyfile; then
	echo "Caddyfile이 /etc/caddy/sites.d를 import하지 않습니다. one-finger-act의 provision.sh(sites.d 버전)를 먼저 실행하세요." >&2
	exit 1
fi

export DEBIAN_FRONTEND=noninteractive
if ! dpkg -s python3-venv >/dev/null 2>&1; then
	apt-get update -qq
	apt-get install -y -qq python3-venv >/dev/null
fi

id laya >/dev/null 2>&1 || useradd --system --home "$BASE" --shell /usr/sbin/nologin laya
install -d -m 0755 "$BASE" "$BASE/models"
install -d -o laya -g laya -m 0750 "$BASE/hf"

[ -x "$BASE/venv/bin/python" ] || python3 -m venv "$BASE/venv"
"$BASE/venv/bin/pip" install -q --upgrade pip
"$BASE/venv/bin/pip" install -q torch --index-url https://download.pytorch.org/whl/cpu
"$BASE/venv/bin/pip" install -q -r "$SRC/requirements.txt"
HF_HOME="$BASE/hf" "$BASE/venv/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download('$MODEL_REPO', local_dir='$BASE/models/laya-vn')" >/dev/null

rm -rf "$BASE/app.new"
cp -r "$SRC/app" "$BASE/app.new"
rm -rf "$BASE/app"
mv "$BASE/app.new" "$BASE/app"

install -m 0644 "$SRC/visual-laya-judge.service" /etc/systemd/system/visual-laya-judge.service
systemctl daemon-reload
systemctl enable visual-laya-judge >/dev/null 2>&1
systemctl restart visual-laya-judge

install -m 0644 "$SRC/visual-laya.caddy" /etc/caddy/sites.d/visual-laya.caddy
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null 2>&1
systemctl reload caddy

for _ in $(seq 60); do
	if curl -fs http://127.0.0.1:8790/api/health; then echo; exit 0; fi
	sleep 2
done
echo "판정 서버가 응답하지 않습니다: journalctl -u visual-laya-judge -n 50" >&2
exit 1
