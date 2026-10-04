# 로컬 음성(TTS) 도입 시도 보고서

작성일: 2026-10-03 · 상태: **보류** — 음성 파일과 TTS 모델은 제거했고, 재도입용 인터페이스만 유지한다.

## 1. 요약

- 목표: 캐릭터 대사(`say` 줄, 629줄)에 로컬 생성 음성을 넣는다. 지문/독백(633줄)은 대상 외.
- 결과: 로컬 TTS 5가지 방식을 비교하고, **Higgs TTS 3(시드 1)로 전체 대사 623줄**을 생성해 게임에 연결했다
  (나머지 6줄은 `…….`처럼 소리 낼 글자가 없는 줄).
- 직접 플레이해 본 결과, 프로토타입 단계에서 쓰기에는 연기 품질이 애매해 **도입을 보류**했다.
- 남긴 것: 엔진 재생 기능, 대본 컴파일러 연동, 생성 파이프라인 코드와 설정, 이 보고서.
  음성 파일과 모델은 모두 제거했다.

## 2. 진행 경과

| 단계 | 내용 | 결과 |
|---|---|---|
| 1차 | Qwen3-TTS-12Hz-1.7B **VoiceDesign**으로 인물별 목소리를 설계한 뒤, **Base** 모델로 클론해 전체 대사 생성 | 음색은 일관됐지만 감정이 거의 없음("발연기") |
| 원인 분석 | Base 클론은 레퍼런스의 톤까지 따라 하고, 줄별 감정 지시를 받지 못함. 레퍼런스가 평서문이라 전 대사가 평서 톤 | 모델보다 파이프라인 구조의 한계 |
| 2차 | 톤 유지 + 감정 제어가 되는 후보를 조사(2026-10 기준)하고 같은 조건으로 비교 샘플 생성 | Higgs TTS 3 선정 |
| 3차 | 비교에서 빠졌던 ZONOS2를 추가로 검증 | 한국어 불가 수준 |
| 4차 | Higgs TTS 3 + 표정 기반 감정 토큰으로 전체 623줄 생성, 품질 점검 후 재생성 | 게임 연결 완료 |
| 결정 | 직접 플레이 후 보류 | 파일·모델 제거, 인터페이스 유지 |

## 3. 후보 비교

### 3.1 후보 선정 (공개 지표 기준)

| 모델 | 근거 | 감정 제어 | 라이선스 | 실행 환경 |
|---|---|---|---|---|
| Fish Audio S2 Pro (5B) | CV3 한국어 WER 1.80 / SIM 0.817 (공개 한국어 지표 1위) | 인라인 태그 `[angry]` 등 | 연구·비상업 | Linux/WSL |
| Higgs TTS 3 (4B) | CV3 13개 언어 평균 WER 4.41 (Fish 4.60보다 낮음), 사람 선호도 평가에서 Fish 우위 | `<\|emotion:anger\|>` 등 제어 토큰 | 비상업 + 제작자 수익화 허용(출처 표기) | Linux/WSL (vLLM-Omni) |
| ZONOS2 (MoE 7.67B) | 공개 지표 없음, 한국어는 2등급(Tier 2) 지원 | 감정 슬라이더 4종 + valence/arousal 축 | MIT | Linux 전용 → Windows용 공식 C++ 포트로 실행 |
| (기준) Qwen3 VoiceDesign 줄별 생성 | 이미 설치된 모델 | 자연어 지시 | Apache 2.0 | Windows |

Breeze TTS 2는 목소리 클론 기능이 없어서 제외했다.

### 3.2 비교 조건

- 대사 12줄: 하람의 칼 장면, 유리의 울음, 도현의 고함, 승하의 고백, 백 회장의 위협 등 감정 폭이 큰 줄.
- 같은 레퍼런스: 1차에서 만든 게임 목소리 약 10초 = VoiceDesign 후보 + 같은 목소리 대사 1줄.
- 테이크 수: Fish·Higgs·ZONOS2는 2테이크, Qwen 계열은 1테이크.
- 지표:
  - 발음: Whisper large-v3-turbo로 받아 적어 원문과 비교한 문자 오류율(CER)
  - 톤 유지: WavLM-SV 화자 유사도(SIM, 레퍼런스 대비)
  - 감정 일치: emotion2vec+ large가 판정한 최상위 감정이 의도한 감정에 속하는 비율

### 3.3 결과

| 방식 | 발음 정확 (CER≤10%) | CER 중앙값 | 톤 유지 (SIM) | 감정 일치 |
|---|---|---|---|---|
| A. Qwen3 Base 클론 (1차) | 12/12 | 0% | 0.935 | 2/12 (17%) |
| B. Fish Audio S2 Pro | 24/24 | 0% | 0.935 | 5/24 (21%) |
| **C. Higgs TTS 3** | 23/24 | 0% | 0.911 | **15/24 (62%)** |
| D. Qwen3 VoiceDesign 줄별 | 12/12 | 0% | 0.848 | 4/12 (33%) |
| E. ZONOS2 (Q8_0) | 2/24 | 72% | 0.688 | 8/24 (33%) |

- **Higgs:** 감정 표현이 가장 강하다. 고함 대사는 Whisper가 받아 적을 때 느낌표가 붙을 정도였다. 톤은 조금 흔들리고 가끔 발음 실수가 있다.
- **Fish:** 발음과 톤 유지는 가장 좋지만, 한국어에서는 감정 태그가 거의 먹히지 않았다. Fish가 태그 반응률을 공개한 언어도 중국어·영어뿐이다.
- **Qwen 줄별 생성:** 감정은 나아지지만 줄마다 목소리가 바뀐다(14살 해온 대사는 SIM 0.46).
- **ZONOS2:** 한국어 발음이 무너지고(예: "강해온은 너무 쉽게 죽었어" → "가메오는 너무 쉽게 죽었어…"), 빈 출력이나 끝없이 이어지는 생성이 잦다. 24개를 얻는 데 44번 시도했다.
  감정을 끄고 기본(accurate) 모드로 돌려도, 모델에 들어 있는 기본 목소리로 바꿔도 같았다. 영어는 안정적이었다.
  원본(bf16 15.3GB)은 16GB GPU에 들어가지 않아 공식 C++ 포트의 Q8_0으로만 시험했다.
- 감정 분류기는 한국어 연기를 잘 구분하지 못한다(A의 "1−P(neutral)"도 0.885로 나옴). 감정 지표는 참고용이고, 최종 선택은 청취로 했다(Higgs #1).

## 4. 최종 파이프라인 (Higgs TTS 3)

```
design  Qwen3 VoiceDesign → 인물별 목소리 후보 3개 (tools/voices.json의 instruct, pick으로 선택)
refs    고른 후보 + 같은 목소리 대사 1줄 → 클론용 레퍼런스 약 10초
lines   WSL Higgs TTS 3: 레퍼런스 클론 + 감정 토큰 → game/assets/voice/<id>/<hash>.mp3
        → story.json 재컴파일 시 say op에 voice 필드 기록 → 엔진 재생
```

- **감정 토큰:** 말하는 인물의 직전 표정(`[show haram cry]`)을 토큰으로 변환한다(`tools/voice_emotion.py`). 줄별로 직접 지정할 수도 있다(`tools/voice_emotions.json`).
  629줄 중 280줄은 평서, 나머지는 표정에 따라 sadness / bitterness / anger / surprise 등.
- **증분 생성:** 파일 이름이 (보이스, 대사) 해시이고 `tools/voice_manifest.json`에 엔진과 토큰을 기록해서, 대본이나 감정이 바뀐 줄만 다시 생성한다.
- **속도:** RTX 5080에서 약 0.55줄/초. 618줄에 약 19분.
- **품질 점검:** 전체 622개 파일을 Whisper로 받아 적었다.
  - CER 10% 이하가 553개, 20% 초과가 16개였다.
  - 16개는 시드 2~4로 다시 만들어 가장 나은 결과를 남겼다.
  - 그래도 남은 8개 중 6개는 이름 "해온"이 Whisper에서 "혜원"으로 인식되는 경우였다(인식 문제일 가능성이 높음).

## 5. 겪은 문제와 대응

| 문제 | 원인 | 대응 |
|---|---|---|
| 1차 음성이 평서 톤 | Base 클론이 레퍼런스 톤을 따라 하고, 감정 지시 입력이 없음 | 감정 제어가 되는 모델로 교체 |
| Fish·Higgs·ZONOS2 모두 Linux 기준 | vLLM-Omni·Fish 공식 지원이 Linux/WSL뿐 | WSL Ubuntu에 venv 구성 |
| WSL VM이 반복해서 죽음 (`Wsl/Service/E_UNEXPECTED`) | 모델 로드 시 메모리 부족(WSL 기본 15GB). Fish는 CPU에서 fp32로 모델을 만들어 20GB 필요 | `.wslconfig` 메모리 22GB로 상향, Fish는 GPU에서 bf16으로 모델 생성, 이어서 생성하는 재시도 루프 |
| Fish가 16GB GPU를 넘침 | KV 캐시 최대 길이 32,768, 코덱 1.9GB를 GPU에 올림 | 캐시 길이 4,096으로 제한, 코덱은 CPU에서 실행 |
| Higgs 실행 시 nvcc 요구 | FlashInfer 어텐션·샘플러가 실행 시점 JIT 컴파일 | Triton 어텐션 + `VLLM_USE_FLASHINFER_SAMPLER=0`, 16GB용 배포 설정(동시 2개, 문맥 4,096) |
| ZONOS2가 16GB에 안 들어감 | 7.67B 파라미터 bf16 = 15.3GB | 공식 C++ 포트(Windows Vulkan) Q8_0 8.5GB로 실행 |

## 6. 보류 결정

직접 플레이하며 들어보니 Higgs의 감정 표현은 1차보다 확실히 나아졌지만, 프로토타입에 넣기에는 아직 애매했다.
더 좋은 방법을 찾을 때까지 음성은 넣지 않는다.

다시 검토할 때 볼 만한 방향:
- 감정별 레퍼런스를 따로 만들어 클론하기 (같은 음색을 유지하면서 레퍼런스 톤 자체를 바꾸는 방식)
- 한국어 감정 연기에 강한 새 오픈 모델이나 상용 API(ElevenLabs v3 등) 재조사
- 핵심 장면(이벤트 리액션, 엔딩)에만 음성을 넣는 부분 도입

## 7. 현재 남아 있는 것 (재도입 인터페이스)

| 파일 | 역할 |
|---|---|
| `game/engine.js` | `op.voice`가 있으면 대사 표시와 함께 재생하고, 다음 줄로 넘기면 정지. 자동 진행은 음성이 끝날 때까지 대기. 음성 슬라이더와 크레딧의 음성 항목은 음성이 있을 때만 표시 |
| `server/compile_story.py` | `game/assets/voice/…` 파일이 있으면 say op에 `voice` 필드를 기록. stats에 `voiced` 수 |
| `server/voice_map.py` | 대사 → 보이스 id(프롤로그 시온 = `haeon`, 단역 → 공용 보이스)와 파일 경로(해시) |
| `tools/gen_voices.py` | design → refs → lines(WSL Higgs) 파이프라인, `--only` `--limit` `--force` `--redo` `--seed` |
| `tools/voices.json` | 인물별 목소리 설명(VoiceDesign instruct)과 레퍼런스 대사 |
| `tools/voice_emotion.py`, `tools/voice_emotions.json` | 표정 → 감정 토큰 규칙, 줄별 지정 |
| `tools/higgs/` | WSL 설치(`setup_wsl.sh`), 16GB용 배포 설정, 생성 작업자 |
| `tools/check_voices.py` | Whisper로 생성 결과 발음 점검 |
| `tools/tts_bench/` | 비교 실험 스크립트와 대사 12줄 설정 (실행하려면 각 모델을 다시 설치해야 함) |
| `video/voice_compare/assets/voice/` | 2026-10-03 재생성한 비교 샘플 A·C·D(12줄, C는 2테이크)와 레퍼런스. `prep_refs.py`가 게임 음성 없이 Base 클론으로 A를 다시 만든다 |

**음성 파일만 다시 넣는 경우:** `game/assets/voice/<보이스id>/<해시>.mp3` 경로에 파일을 두고 서버를 재시작하면(서버 없이 쓸 때는 `.\.venv\Scripts\python.exe server\compile_story.py`) 자동으로 연결된다.
경로는 `server/voice_map.py`의 `voice_rel()`이 정한다. 다른 TTS 엔진을 쓰려면 `tools/gen_voices.py`의 `gen_lines()`만 바꾸면 된다.

**Higgs로 다시 생성하는 경우:** `.\run.ps1 voice-setup`(Qwen VoiceDesign + WSL Higgs 설치, 약 20GB 다운로드) 후 `.\run.ps1 voice`.
목소리 후보(`tools/voice_refs/`)는 지웠으므로 design 단계부터 새로 만든다. 같은 설명이어도 결과는 이전과 달라질 수 있다.

## 8. 제거한 것

- 음성 파일: `game/assets/voice/` 622개, `tools/voice_refs/`(후보와 클론 레퍼런스), `samples/tts_compare/`(비교 샘플), `tools/voice_manifest.json`, 생성·점검 로그
- 모델·환경:
  - WSL `~/tts`(Higgs TTS 3 모델 8.7GB, vLLM-Omni 환경 8.5GB), Higgs 레퍼런스 인코더 캐시, uv
  - 이전 단계에서 Fish S2 Pro, ZONOS2, Qwen3 Base, CUDA 툴킷 12.8, emotion2vec·WavLM 캐시도 제거
- 남아 있는 관련 설치물(필요 없으면 직접 제거 가능):
  - Windows `.venv-tts` + `models/Qwen3-TTS-12Hz-1.7B-VoiceDesign`(4.3GB)
  - Whisper large-v3-turbo HF 캐시(1.6GB)
  - `C:\Users\enne1\.wslconfig`(WSL 메모리 22GB)
  - WSL 시스템 패키지 ffmpeg / build-essential / git / python3-dev

## 참고 자료

- Fish Audio S2 Technical Report — https://arxiv.org/html/2603.08823v2
- Higgs TTS 3 모델 카드 — https://huggingface.co/bosonai/higgs-tts-3-4b
- vLLM-Omni Higgs 레시피 — https://github.com/vllm-project/vllm-omni/blob/main/recipes/BosonAI/Higgs-Audio-V3-TTS.md
- ZONOS2 / zonos2.cpp — https://github.com/Zyphra/Zonos2 , https://github.com/Zyphra/zonos2.cpp
- Qwen3-TTS — https://github.com/QwenLM/Qwen3-TTS
