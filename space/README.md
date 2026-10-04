---
title: Visual Laya Judge
emoji: 🕯️
colorFrom: gray
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
models:
  - ringwring/laya-vn
short_description: 재의 백작 — 플레이어 대사 판정 API (laya-vn)
---

# Visual Laya Judge

비주얼 노벨 프로토타입 「재의 백작」의 판정 서버. 플레이어가 입력한 대사를 파인튜닝 모델
[`ringwring/laya-vn`](https://huggingface.co/ringwring/laya-vn)이 판정해 호감도 변화를 돌려준다.

- 게임: https://ring-experimental.github.io/visual-laya/
- 소스: https://github.com/ring-experimental/visual-laya (`space/`가 이 Space의 원본, `tools/deploy_space.py`로 배포)

## API

```
GET  /api/health                        → {"ok": true, "model": "laya-vn", "events": 18}
POST /api/judge {"event_id", "text"}    → {"tier", "delta", "impact", "vengeance", "nonsense", ...}
```

CPU 무료 티어라 판정 1회에 수 초 걸리고, 한동안 호출이 없으면 잠들었다가 첫 요청에서 깨어난다.
입력한 대사는 저장하지 않는다(`LAYA_LOG=0`).
