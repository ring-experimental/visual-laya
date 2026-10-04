# 판정 서버 원격 호스팅 검토 (보류)

GitHub Pages에 올린 게임(https://ring-experimental.github.io/visual-laya/)에서도 파인튜닝 모델 `laya-vn`으로 판정하려고
판정 API를 외부에 띄우는 방법을 시도했다. 무료로는 쓸 만한 지연이 나오지 않아 **보류**했다.
지금 Pages 배포판은 브라우저 간이 판정(`engine.js`의 `localJudge`)으로 진행한다. 로컬에서 `.\run.ps1`로 실행하면 그대로 laya-vn을 쓴다.

## 1. 남아 있는 것

| 위치 | 내용 |
|---|---|
| Hugging Face `ringwring/laya-vn` (public) | 배포 모델 + 모델 카드. `run.ps1 setup`이 받는다 |
| `server/app.py` | `--api-only`(정적 파일·파일 쓰기 없이 `/api`만), `CORS_ORIGINS`, `LAYA_LOG=0` |
| `game/engine.js` | 판정 API 위치: `?api=<url>` > GitHub Pages면 `REMOTE_API` > 같은 서버. 원격이면 타임아웃 20초, 잠든 서버를 깨우려고 health를 10초 간격 12회 재시도. `REMOTE_API`는 비어 있음 |
| `space/`, `tools/deploy_space.py` | HF Docker Space용 Dockerfile·README·배포 스크립트 (아래 2절, 미배포) |
| `deploy/oci/` | OCI VM 배포 스크립트·systemd 유닛·Caddy 경로 (아래 3절). VM에서는 모두 제거됨 |

## 2. Hugging Face Space — 무료 불가

- Docker Space를 만들려 하자 402: *Gradio·Docker Space를 무료 cpu-basic에서 돌리려면 PRO 구독 필요* (2026-10 기준, 정적 Space만 무료).
- PRO(월 $9)면 `.\.venv\Scripts\python.exe tools\deploy_space.py` 후 `REMOTE_API = "https://ringwring-visual-laya-judge.hf.space/"`로 바로 쓸 수 있다.
  빌드할 때 모델을 이미지에 받아 두고, 대사는 저장하지 않는다(`LAYA_LOG=0`), CORS는 `ring-experimental.github.io`만 허용.
- cpu-basic(2 vCPU)의 실제 판정 시간은 재 보지 못했다.

## 3. OCI 무료 VM — 동작은 하지만 너무 느림

기존 매치 서버 VM(`ofa-match-a1`, Ampere A1 Neoverse-N1 2 OCPU / 12GB, Caddy가 `168.107.48.33.sslip.io` TLS 담당)에 경로만 추가했다.

- **Caddy**: one-finger-act `provision.sh`가 Caddyfile을 매번 덮어쓰므로, 사이트 블록이 `/etc/caddy/sites.d/*.caddy`를 import하고
  나머지는 `handle`로 매치 서버에 넘기는 형태로 바꿔 썼다. 보류하면서 provision.sh 변경은 버리고 VM의 Caddyfile도 원래대로 되돌렸다.
  다시 쓰려면 provision.sh의 Caddyfile을 아래 형태로 바꾸고 VM에도 반영해야 한다(`install.sh`가 이 import를 확인한다).

  ```
  <HOST> {
  	import /etc/caddy/sites.d/*.caddy
  	handle {
  		reverse_proxy 127.0.0.1:8080
  	}
  }
  ```
- **배포**: `deploy/oci/deploy.sh` → VM에서 `install.sh`(멱등): `laya` 사용자, `/opt/visual-laya`(venv + CPU torch + 모델),
  `visual-laya-judge.service`(127.0.0.1:8790), `/etc/caddy/sites.d/visual-laya.caddy`(`/laya/*`). 약 2분.
- **매치 서버 보호**: 실시간 매치 서버가 첫 코어를 쓰므로 판정은 두 번째 코어에만(`AllowedCPUs=1`, `CPUQuota=80%`, `Nice=15`,
  `OMP_NUM_THREADS=1`, `MemoryMax=3G`). 메모리는 약 2GB 사용.
- 경로·CORS(허용 출처만 통과, 그 외 preflight 400)·매치 서버 무중단까지 확인했다.

### 측정 (대사 1줄, 같은 입력)

입력은 대사 상태 약 300토큰 + 질문 3개(impact·vengeance·nonsense) 행을 합쳐 **약 1,200토큰**으로 고정이다. 줄이려면 재학습이 필요하다.

| 환경 | 판정 1회 |
|---|---|
| 로컬 RTX 5080 (CUDA) | ~16ms |
| 로컬 x86 데스크톱 CPU, 2스레드 | 0.7~2초 |
| OCI N1, 1코어 (서비스 설정, `CPUQuota=80%`) | **13초** |
| OCI N1, 1코어 (제한 없음) | 10.5초 |
| OCI N1, 2코어 | 5.5초 (매치 서버 코어까지 씀) |
| OCI N1, 1코어 + torch int8 동적 양자화(qnnpack) | 17초 (더 느림, 확률도 소폭 변함) |

laya는 CPU에서 이미 fp32로 돈다(`LAYA_CPU_AMP`를 켜야 bf16). N1에는 bf16 명령이 없어 켜도 이득이 없다.

### 시도하지 않은 것

- **ONNX Runtime**: laya에 `ONNXAgent`(입력 `input_ids`·`attention_mask`·`marker_pos`·`marker_mask`·`qtype`, 출력 `logits`·`act_logits`)는 있지만
  export 스크립트는 패키지에 없다. `DecisionModel.forward`를 `torch.onnx.export`로 직접 내보낸 뒤 ORT int8(N1의 `asimddp` 활용)로
  2~4배를 기대할 수 있으나, 그래도 1코어 3~5초 수준으로 예상해 중단했다.
- 브라우저 안 추론(onnxruntime-web): 서버가 필요 없지만 모델 다운로드 150MB 이상 + 전처리 JS 이식이 필요하다.

### 다시 켜기 / 완전히 지우기

위 Caddyfile 형태를 먼저 적용한 뒤:

```bash
deploy/oci/deploy.sh                       # 재설치 + 서비스 시작 + /laya/* 경로 등록
```

그다음 `engine.js`의 `REMOTE_API`를 `"https://168.107.48.33.sslip.io/laya/"`로 채운다(타임아웃 20초 안에 들어와야 하므로 지금 속도로는 권장하지 않음).

2026-10-04에 VM에서 모두 제거했다: 서비스·유닛, `sites.d` 경로, `/opt/visual-laya`(venv·모델), `laya` 사용자. apt로 설치한 `python3-venv`만 남아 있다.
다시 설치한 뒤 지울 때:

```bash
sudo systemctl disable --now visual-laya-judge; sudo rm -f /etc/systemd/system/visual-laya-judge.service /etc/caddy/sites.d/visual-laya.caddy; sudo rm -rf /opt/visual-laya; sudo userdel laya; sudo systemctl daemon-reload; sudo systemctl reload caddy
```
