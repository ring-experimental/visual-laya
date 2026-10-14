# 재의 백작 (The Count of Ashes)

로컬 **Laya**(System 1 decision model)가 플레이어가 *직접 타이핑한 대사*를 판정해 호감도를 움직이는 비주얼 노벨 프로토타입.

- 현대 한국 항구도시 배경의 몽테크리스토풍 복수극. 등장인물 5명(17세 소년소녀 + 16세 소녀)
- 트루엔딩 기준 약 1시간 (대본 약 680줄 / 자유 입력 이벤트 18회 / 엔딩 5종)
- 선택지 없음: 분기 이벤트마다 시온의 대사를 입력 → 파인튜닝된 Laya가 한 번의 forward pass(~15ms)로
  `impact`(5단계 점수) · `vengeance`(복수심) · `nonsense`(장난/욕설)를 판정 → 호감도 가중치 적용

## 빠른 시작 (Windows)

```powershell
.\run.ps1 setup    # 최초 1회: venv, PyTorch(CUDA 13), laya, 베이스 모델(laya-multilingual) + 판정 모델(laya-vn) 다운로드
.\run.ps1 train    # (선택) 판정 모델 재학습 → models\laya-vn  (RTX 5080 기준 수 분)
.\run.ps1          # 게임 서버 실행 → http://127.0.0.1:8765
```

모델이 없으면 서버는 `laya-multilingual`(제로샷) → 휴리스틱 순으로 자동 대체하고,
서버 없이 `game/`만 정적으로 열어도 브라우저 내 간이 판정으로 끝까지 플레이할 수 있다.

## 구조

```
docs/
  STORY_BIBLE.md         세계관·인물·비밀·장별 비트·이벤트 need·엔딩 조건 (기준 문서)
  SCRIPT_FORMAT.md       대본 DSL(.vns) 명세, 배경/CG/BGM/표정 키 목록
  TRAINING_DATA.md       판정 학습 데이터 규격
  CHARACTER_CONCEPTS.md  인물 컨셉 + 외부 이미지 생성용 프롬프트
story/*.vns              대본 (프롤로그 ~ 6장, 엔딩 5종)
server/
  app.py                 FastAPI: 게임 정적 파일 + POST /api/judge + GET /api/health
  judge.py               Laya 로딩·판정 (laya-vn → laya-multilingual → 휴리스틱)
  laya_prompt.py         판정 state/질문/가중치 정의 (학습과 추론이 공유)
  compile_story.py       .vns → game/data/story.json 컴파일 + 문법 검사
training/
  data/E00..E17*.jsonl   이벤트별 라벨 데이터 (부드러운 확률 분포 라벨)
  train.py               RLCD 파인튜닝(laya 공식 레시피의 CUDA 이식) + 평가 리포트
  report.json            베이스 vs 파인튜닝 평가 결과
game/                    HTML/CSS/JS 엔진 (빌드 불필요)
  assets/{characters,bg,cg,bgm,sfx}/   ← 일러스트·음악을 키 이름대로 넣으면 자동 교체
models/                  laya-multilingual(베이스), laya-vn(파인튜닝 결과)
logs/judgments.jsonl     실제 플레이 판정 로그 (추가 학습 데이터로 재활용 가능)
```

## 판정 → 호감도

| impact 단계 | 의미 | 가중치 |
|---|---|---|
| 0 | 깊은 상처를 주거나 적대감을 키운다 | −12 |
| 1 | 무신경하거나 엉뚱해서 실망시킨다 | −5 |
| 2 | 무난하지만 마음에 닿지 않는다 | 0 |
| 3 | 공감하며 마음을 열게 한다 | +7 |
| 4 | 상대가 필요로 하던 말을 정확히 건네 깊이 흔든다 | +13 |

- Δ호감도 = Σ p(단계)·가중치 (nonsense > 0.5면 추가 감점). Δ ≤ −3 → `low`, Δ ≥ 5 → `high`, 그 외 `mid` 리액션.
- 복수심 = 모든 입력의 vengeance 확률 가중 평균(최종 이벤트 E17은 2배).
- 엔딩: 복수심 ≥60% → BAD「재의 백작」 / 하람 <35 → BAD「칼끝」 / 전원 ≥50·하람 ≥65·복수심 <45% → TRUE「새벽의 등대」 / 하람 ≥55·나머지 중 3명 ≥45 → HAPPY「봄의 귀환」 / 그 외 NORMAL「백작의 퇴장」

### 판정 모델 성능 (training/report_author.json)

학습 데이터 1,989줄(이벤트당 a배치 약 60줄 + 다른 라벨러가 쓴 b배치 50줄). a배치로만 학습하고 **본 적 없는 b배치 900줄**로 평가:

| | 제로샷 laya-multilingual | 파인튜닝 laya-vn |
|---|---|---|
| 리액션 단계(low/mid/high) 정확도 | 31.9% | **68.8%** |
| impact 기대값 오차(MAE, 0~4) | 1.09 | **0.52** |
| impact ±1단계 이내 | 68% | **92%** |
| vengeance 오차 | 0.44 | **0.12** |
| nonsense 오차 | 0.35 | **0.04** |
| 판정 1회 지연 (RTX 5080) | ~16ms | ~16ms |

배포 모델(`models/laya-vn`)은 a+b 전체로 다시 학습한 것이다(RTX 5080에서 6 에폭 약 8분).
Hugging Face `ringwring/laya-vn`(private)에 올려 두었고 `setup`이 내려받는다. 받기 전에 `.\.venv\Scripts\hf.exe auth login`,
다른 저장소를 쓰려면 환경변수 `LAYA_VN_REPO`.

판정 기준(장면·상대의 need)은 대본의 `[event]` 블록에 있으므로, **대본을 고치면 판정도 함께 바뀐다**.
새 이벤트를 추가하면 `training/data/<ID>.jsonl`을 60줄 정도 쓰고 `.\run.ps1 train`.

## 웹 배포

`game/`은 main에 push하면 GitHub Pages(https://ring-experimental.github.io/visual-laya/)로 배포된다(`.github/workflows/pages.yml`).
Pages에서는 판정 서버 없이 브라우저 간이 판정으로 진행한다. 원격 판정 서버(HF Space, OCI) 검토 과정과 측정은 **`docs/JUDGE_HOSTING.md`**.
다른 곳에 띄운 판정 서버를 쓰려면 `?api=<서버 URL>`을 붙여 연다(서버에 `CORS_ORIGINS` 필요).

## 조작

클릭/Space/Enter 진행 · `H` 호감도 · `L`/휠업 로그 · `A` 자동 · `S` 스킵 · `Esc` 메뉴 · 입력창 `Ctrl+Enter` 전송
메뉴에서 "Laya 판정 상세 표시"를 켜면 단계별 확률과 지연시간이 보인다. `?debug=1`로 열면 `J`로 라벨 점프.

## 일러스트

`docs/CHARACTER_CONCEPTS.md`의 프롬프트로 외부 모델에서 생성 후 파일명 규칙대로 `game/assets/`에 넣고 서버를 재시작하면
(시작 시 `game/data/assets.json` 매니페스트 갱신) 플레이스홀더가 자동으로 교체된다.

표정 시트 한 장(`game/assets/characters_sprite/<id>.png`)으로 받은 경우:

```powershell
.\.venv\Scripts\python.exe tools\split_sprites.py            # 전체
.\.venv\Scripts\python.exe tools\split_sprites.py yuri       # 한 캐릭터만
```

시트별 표정 순서는 `tools/split_sprites.py`의 `SHEETS`에 있다. 새 시트의 배치가 다르면 거기만 고치면 된다.

## 음성 (보류)

현재 음성 파일과 TTS 모델은 없다. 로컬 TTS(Qwen3-TTS, Fish S2 Pro, Higgs TTS 3, ZONOS2)로 전체 대사를 만들어 봤지만
프로토타입에 쓰기엔 애매해 보류했다. 과정·비교 결과·재도입 방법은 **`docs/VOICE_REPORT.md`**.

재생 인터페이스는 그대로 있다: `game/assets/voice/<보이스id>/<해시>.mp3`(경로는 `server/voice_map.py`)에 파일이 있으면
대본 컴파일 시 자동 연결되고, 엔진이 대사와 함께 재생한다. 음성이 하나도 없으면 메뉴의 "음성" 슬라이더와 크레딧 항목은 숨겨진다.
다시 생성하려면 `.\run.ps1 voice-setup` → `.\run.ps1 voice` (`tools/gen_voices.py`).
