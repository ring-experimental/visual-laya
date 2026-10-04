# BGM 생성 프롬프트 (11곡)

> 파일: `game/assets/bgm/<key>.mp3` (엔진이 자동 반복 재생, 없으면 무음 진행)
> 생성 모델: Suno / Udio (스타일 태그형) 또는 Stable Audio / MusicGen (서술형). 두 형식을 모두 적었다.

---

## 채택 현황 (ACE-Step 1.5, 2026-10-04)

생성: `tools/gen_bgm.py` (ACE-Step venv로 실행). 후보는 `tools/bgm_out/`, 채택본은 `game/assets/bgm/<key>.mp3` (-15 LUFS, 끝 무음 제거).
가이드 형식 스펙(`tools/bgm_specs/*.json`)은 ACE-Step 공식 가이드를 따른다 — 메타데이터(BPM·조성·박자)는 캡션이 아닌 파라미터로, 곡 흐름은 lyrics 칸의 구조 태그로, 원치 않는 요소는 캡션에 쓰지 않고 LM 네거티브 프롬프트로.

| key | 채택 후보 | 프롬프트 출처 |
|---|---|---|
| theme_ashes | `theme_ashes_waltz_2` | `tools/bgm_specs/theme_ashes_v2.json` — 단조 왈츠, 첫머리에 훅 선율 |
| calm_sea | `calm_sea_1` | 아래 2번 (스타일 태그형) |
| school_day | `school_day_2` | 아래 3번 (스타일 태그형) |
| tension | `tension_2` | 아래 4번 (타악 제거 개정판) |
| sorrow | `sorrow_theme_cover55_1` | `tools/bgm_specs/derived_v2.json` — 새 theme_ashes를 cover(강도 0.55), 캡션으로 슬픔 |
| romance | `romance_guitar_piano_1` | `tools/bgm_specs/romance.json` |
| party | `party_baroque_irony_2` | `tools/bgm_specs/party_v2.json` — 과시적 바로크 현악 + 불길한 저음 |
| fire | `fire_1` | 아래 8번 (스타일 태그형) |
| revenge | `revenge_1` | 아래 9번 (스타일 태그형) |
| dawn | `dawn_1` | 아래 10번 (theme_ashes 구버전 레퍼런스) |
| ending_bad | `ending_bad_theme_cover55_1` | `tools/bgm_specs/derived_v2.json` — 새 theme_ashes를 cover(강도 0.55), 캡션으로 붕괴 |
| memory | `calm_sea_rocking_cello_2` | `tools/bgm_specs/theme_family.json` — 회상·후회 (2장 승하의 갑판, 4장 별관 폐허, BAD 「재의 백작」 등대곶) |
| scary | 구 `romance_1` | 미사용 예비곡 (소름끼치는 분위기) |

> 주의: 아래 1~11번의 스타일 태그형 프롬프트 중 theme_ashes·sorrow·romance·party는 더 이상 채택본의 출처가 아니다.
> 「등대의 주제」 라이트모티프: `reference_audio`는 음색만 전달하고 선율은 지우므로(ACE-Step 가이드), 선율을 물려받으려면 `cover`(src_audio)로 파생한다.
> sorrow·ending_bad는 새 theme_ashes의 cover 파생. calm_sea·dawn은 구버전 그대로 유지(선율 연결 없음).

## 0. 공통 규칙

| 항목 | 지정 |
|---|---|
| 보컬 | **없음 (instrumental)**. Suno는 Instrumental 토글을 켜고, 가사 칸은 비운다 |
| 길이 | 1분 30초 ~ 3분. 대사 뒤에 깔리므로 길 필요 없음 |
| 루프 | 엔진이 처음부터 다시 재생한다. **시작과 끝의 에너지·화성이 비슷해야** 이음매가 덜 튄다. 페이드아웃 엔딩 금지, 급격한 클라이맥스 엔딩 금지 |
| 음량 | 대사를 방해하지 않게 다이내믹 범위를 좁게. 생성 후 모든 곡을 비슷한 체감 음량(-16~-14 LUFS)으로 맞출 것 |
| 공통 색채 | 항구도시의 안개·파도·등대. **피아노 + 현악**을 축으로, 장면에 따라 첼로·앰비언트 패드·저음 퍼커션을 더한다 |

### 라이트모티프 — 「등대의 주제」
게임 전체를 묶는 짧은 선율 하나를 둔다. 4~5음의 하강 후 상승("내려앉았다가 다시 빛이 도는") 피아노 프레이즈.
- 생성 모델은 같은 선율을 정확히 재현하지 못한다. 그래서 순서가 중요하다.
  1. **`theme_ashes`를 가장 먼저** 만든다.
  2. 마음에 드는 결과를 **레퍼런스 오디오로 넣어**(Suno *Cover/Extend*, Udio *Remix*, Stable Audio *audio-to-audio*) `dawn`, `sorrow`, `ending_bad`, `calm_sea`를 파생시킨다.
  3. 같은 주제가 슬픔·희망·파멸로 변주되면 엔딩에서 감정이 크게 돌아온다.

### 공통 네거티브 (지원하는 모델에서)
```
vocals, lyrics, singing, choir words, EDM drop, dubstep, heavy distortion, upbeat pop, comedic, 8-bit, abrupt ending, fade out
```

---

## 1. `theme_ashes` — 메인 테마 「재의 백작」
**쓰이는 곳 (6):** 소년원의 겨울, 윤경한의 임종, 새벽 두 시의 서재(복수 계획), 비 오는 서재에서 장갑을 벗는 밤, 6장 개관식 날 아침, TRUE 엔딩의 새벽 등대.
**역할:** 게임의 얼굴. 차갑고 고독하지만 품위가 있고, 아주 밑바닥에 꺼지지 않은 불씨 같은 온기. 처음엔 상실, 마지막(TRUE)엔 구원으로 들려야 한다.
**음악:** 68 BPM, D 단조, 솔로 피아노가 주제 → 첼로가 받음 → 현악 패드가 천천히 차오름. 타악 없음.

```
Suno/Udio style: melancholic neoclassical piano, solo cello, slow strings, cinematic visual novel main theme, D minor, 68 bpm, elegant and lonely, cold winter sea, faint hope, instrumental, seamless loop
```
```
Stable Audio / MusicGen: A slow melancholic neoclassical main theme for a revenge drama. Solo piano introduces a simple descending-then-rising motif in D minor at 68 BPM, answered by a warm solo cello, while soft string pads swell gently underneath. Cold, elegant, lonely, with a faint ember of hope. No drums, no vocals. Loopable, consistent energy from start to end.
```

## 2. `calm_sea` — 안개 낀 바다
**쓰이는 곳 (6):** 프롤로그 등대곶(사건 전의 평화), 3년 만에 돌아오는 해안도로, 어머니를 만나러 가는 차 안, 윤성관 개관식 입장, TRUE 엔딩 요양병원의 어머니, HAPPY 엔딩 재심 무죄.
**역할:** 해무시라는 도시 자체의 숨소리. 평온하지만 그리움이 섞인. 이 곡이 프롤로그에서 따뜻했기 때문에 이후 같은 곡이 쓸쓸하게 들린다.
**음악:** 76 BPM, F 장조와 D 단조 사이를 오감, 피아노 아르페지오 + 어쿠스틱 기타 하모닉스 + 아주 옅은 파도 앰비언스.

```
Suno/Udio style: gentle ambient piano arpeggios, soft acoustic guitar harmonics, distant ocean waves, foggy seaside town, nostalgic and calm, bittersweet, F major, 76 bpm, lo-fi warmth, instrumental, loop
```
```
Stable Audio / MusicGen: Calm nostalgic seaside music. Flowing piano arpeggios in F major at 76 BPM with soft acoustic guitar harmonics and a very quiet layer of distant ocean waves. Peaceful but tinged with longing, like a foggy harbor town at dusk. No drums, no vocals, steady and loopable.
```

## 3. `school_day` — 해무고의 낮
**쓰이는 곳 (3):** 전학 첫날 교문과 교실, 학생회장 은채를 처음 만나는 복도, 2장 유리가 먼저 인사하는 복도.
**역할:** 평범한 고등학교의 낮. 단, 주인공은 가면을 쓴 이방인이므로 *완전히 밝지는 않게* — 밝은 표면 아래 살짝 어긋난 화음.
**음악:** 96 BPM, G 장조, 피치카토 현악 + 가벼운 피아노 + 브러시 스네어. 가끔 단조로 미끄러지는 화음 하나.

```
Suno/Udio style: light slice-of-life school music, pizzicato strings, soft piano, brushed snare, glockenspiel accents, G major, 96 bpm, spring morning, gentle but slightly uneasy undertone, anime visual novel, instrumental, loop
```
```
Stable Audio / MusicGen: Light slice-of-life high school background music in G major at 96 BPM. Pizzicato strings, soft piano chords, gentle brushed snare and occasional glockenspiel. Bright spring morning feeling, but with a subtle uneasy minor chord now and then, as if someone in the crowd is wearing a mask. No vocals, loopable.
```

## 4. `tension` — 가면과 심문 (최다 사용)
**쓰이는 곳 (12):** 프롤로그 재판, 식당의 괴롭힘, 학생회실에서 은채와의 지적 결투, 승하가 웃지 않는 금요일, 옥상에서 도현과의 거래, 마정훈 기자회견 등.
**역할:** 대화로 하는 결투. 큰 사건이 아니라 *숨 막히는 신경전*이므로 과하지 않게, 낮게 깔리는 긴장.
**음악:** 72 BPM, C 단조, 저음 첼로·콘트라베이스의 레가토 롱톤 + 어두운 앰비언트 드론 + 높은 바이올린의 여린 트레몰로 + 간헐적 피아노 불협화음. **타악·스타카토·피치카토 없음** — 리듬감이 튀면 몰입이 깨진다. 멜로디 최소화.

```
Suno/Udio style: dark suspenseful ambient underscore, sustained low cello and double bass drones, slow legato strings, quiet high violin tremolo, sparse dissonant piano notes, ominous atmospheric pad, psychological thriller, C minor, 72 bpm, restrained tension, no percussion, no drums, no staccato, no pizzicato, smooth and static, no climax, instrumental, loop
```
```
Stable Audio / MusicGen: Restrained psychological tension underscore for a dialogue duel. Sustained low cello and double bass drones in C minor at 72 BPM, slow legato strings and a dark ambient pad, a quiet high violin tremolo, and occasional sparse dissonant piano notes. Tense and cold but quiet enough to sit under dialogue. No percussion, no staccato or pizzicato, no bouncy rhythm. No big climax, no vocals, loopable.
```

## 5. `sorrow` — 무너진 사람들 (최다 사용)
**쓰이는 곳 (12):** 수갑 찬 병실, 출원하던 비 오는 날의 바다, 옥상의 하람(부고 스크랩), 밤 수영장의 도현, 보건실의 하람, 은채의 USB 고백 등.
**역할:** 인물들이 가면을 벗고 가장 약해지는 순간. 감상적으로 짜내지 말고 *조용히 아프게*.
**음악:** 60 BPM, A 단조, 솔로 피아노(여백 많이) + 비올라/첼로 롱톤. 「등대의 주제」를 느리게 변주하면 좋다.

```
Suno/Udio style: sad solo piano with lots of space, sustained viola and cello long tones, intimate and fragile, A minor, 60 bpm, quiet grief, rain on window, emotional visual novel, instrumental, loop
```
```
Stable Audio / MusicGen: Quiet, fragile sorrow music. Sparse solo piano in A minor at 60 BPM with lots of silence between phrases, supported by sustained viola and cello long tones. Intimate grief, like rain on a window at night. Not melodramatic, no drums, no vocals, loopable.
```
→ 레퍼런스: `theme_ashes`를 넣고 "slower, sparser, sadder"로 파생.

## 6. `romance` — 따뜻한 손
**쓰이는 곳 (4):** 노을 진 등대 아래 유리와의 재회(1장), 비 오는 대문에서 장갑 위로 잡은 손 "해온이지?"(3장), 합창부실 피아노 앞에서 증언을 결심하며 웃다 우는 유리(5장), HAPPY 엔딩 4월 봄 바다에 발을 담그는 하람(엔딩).
**역할:** 사람의 온기. 복수극에서 시온이 *다시 따뜻해지는* 순간마다 깔린다. 애틋하되 **어둡거나 으스스하지 않게** — HAPPY 엔딩의 봄 바다에도 그대로 어울려야 한다. 슬픔은 `sorrow`의 몫이다.
**음악:** 76 BPM, G 장조, 4/4. 나일론 어쿠스틱 기타 핑거피킹 + 따뜻한 피아노 선율 + 첼로·부드러운 현악. 처음부터 끝까지 협화음, 단조 화음이 끼어들지 않게.

> **채택본:** ACE-Step 1.5 공식 프롬프트 가이드 형식으로 만든 [`tools/bgm_specs/romance.json`](../tools/bgm_specs/romance.json)의 `romance_guitar_piano` 변형.
> 가이드 원칙: BPM·조성·박자는 캡션이 아닌 메타데이터 파라미터로, 곡의 흐름은 lyrics 칸의 구조 태그로, 원치 않는 요소는 캡션에 쓰지 말고 LM 네거티브 프롬프트로.

```
ACE-Step caption: Instrumental warm acoustic romance, gentle fingerpicked nylon acoustic guitar, soft warm piano melody, warm cello and soft strings, tender, hopeful, peaceful and quietly happy, sunlit seaside spring afternoon feeling, consistently consonant and sweet harmony, uplifting major tonality throughout, intimate and cozy, smooth moderate even dynamics, warm, airy, natural live recording feel, slice-of-life soundtrack, slow tempo, laid-back, seamless looping background music
ACE-Step lyrics:  [Intro - acoustic guitar] / [Main Theme - guitar and piano] / [Verse - cello joins] / [Bridge - warm] / [Main Theme - guitar and piano] / [Outro - acoustic guitar]
metadata:         bpm 76, G Major, 4/4, 150s  ·  LM temperature 0.7, cfg 2.5
```

## 7. `party` — 승하의 요트 파티
**쓰이는 곳 (1):** 2장, 해무항 마리나의 금빛 요트 파티. '진실 혹은 벌칙'으로 하람을 조롱하려다 시온이 판을 뒤집는다.
**역할:** 화려하지만 천박하고 잔인한 부의 파티. 들뜬 표면 아래 *불길함*.
**음악:** 112 BPM, 딥하우스/라운지. 저음 신스 베이스 + 필터 걸린 피아노 코드 + 가벼운 하이햇. 마이너 키로 약간 어둡게.

```
Suno/Udio style: dark luxury lounge deep house, filtered piano chords, smooth sub bass, crisp hi-hats, champagne yacht party at night, glamorous but sinister, A minor, 112 bpm, background music, instrumental, loop
```
```
Stable Audio / MusicGen: Dark luxurious lounge deep house for a rich kids' yacht party at night, 112 BPM in A minor. Smooth sub bass, filtered piano chords, crisp hi-hats and subtle synth pads. Glamorous on the surface but quietly sinister underneath. Low enough to sit under dialogue. No vocals, loopable.
```

## 8. `fire` — 불
**쓰이는 곳 (3):** 프롤로그 언덕 위 학교가 붉게 물드는 순간과 잠긴 문, 3장 창고 문을 부수는 순간(플래시백 겹침), 6장 윤성관 화재.
**역할:** 게임의 트라우마 그 자체. 공포와 절박함. 소리가 *가까이 덮쳐 오는* 느낌.
**음악:** 128 BPM, 불규칙한 저음 타악(태고/팀파니) + 스타카토 현악 + 금속성 드론 + 심장박동 같은 킥. 화성은 거의 없이 리듬과 질감.

```
Suno/Udio style: intense cinematic action horror, pounding taiko and timpani, frantic staccato strings, metallic drones, heartbeat kick, rising dread, emergency, fire and smoke, 128 bpm, dark and chaotic, trailer underscore, instrumental, loop
```
```
Stable Audio / MusicGen: Intense, frightening cinematic underscore for a building on fire. Pounding taiko and timpani at 128 BPM, frantic staccato strings, a harsh metallic drone and a heartbeat-like kick drum. Almost no melody, just rhythm, texture and dread. Keep intensity steady so it loops. No vocals.
```

## 9. `revenge` — 백작의 계획
**쓰이는 곳 (4):** 서재 책상 위 다섯 개의 계획 파일, 3장 복수 개시 몽타주(월~목), 5장 끝 백 회장 "개관식 날 정리해", 6장 광장에서의 폭로.
**역할:** 몽테크리스토의 쾌감. 차갑고 치밀하고 통쾌한 — 체스 수를 하나씩 두는 느낌. 동시에 *주인공이 위험해지고 있다*는 그늘.
**음악:** 100 BPM, B 단조, 하프시코드/피치카토의 바로크풍 오스티나토 + 저음 신스 + 묵직한 스트링 스탭. 탱고 리듬을 살짝.

```
Suno/Udio style: dark baroque thriller, harpsichord ostinato, pizzicato strings, deep synth bass, sharp string stabs, subtle tango rhythm, cunning and elegant revenge plan, chess, B minor, 100 bpm, cinematic, instrumental, loop
```
```
Stable Audio / MusicGen: Cunning, elegant revenge music in B minor at 100 BPM. A dark baroque harpsichord ostinato with pizzicato strings, a deep modern synth bass and sharp string stabs, with a subtle tango rhythm underneath. Feels like a mastermind moving chess pieces one by one — satisfying, cold, and slightly dangerous. No vocals, loopable.
```

## 10. `dawn` — 새벽의 등대 (TRUE 엔딩)
**쓰이는 곳 (1):** TRUE 엔딩, 새벽 네 시 반 등대곶에 다섯 명이 모이는 장면부터 장갑을 벗는 순간까지.
**역할:** 게임 전체의 보상. 「등대의 주제」가 마침내 장조로 완성된다. 울컥하지만 밝은.
**음악:** 80 BPM, D 장조(theme_ashes의 D 단조가 장조로 해방), 피아노 → 현악 풀 앙상블 → 호른. 점점 차오르되 루프를 위해 정점을 길게 유지.

```
Suno/Udio style: hopeful cinematic orchestral, piano melody blossoming into full strings and french horn, sunrise over the sea, redemption and forgiveness, D major, 80 bpm, emotional uplifting finale, visual novel true ending, instrumental, loop
```
```
Stable Audio / MusicGen: A hopeful, emotional true-ending theme in D major at 80 BPM. The main piano motif returns, now in a major key, blossoming into warm full strings and a gentle French horn. Sunrise over the sea, redemption and forgiveness. Grows in the first half, then sustains a warm plateau so it loops without a hard ending. No vocals.
```
→ 레퍼런스: `theme_ashes`를 넣고 "major key, hopeful, full orchestra"로 파생. 이 곡이 메인 테마와 이어져 들려야 엔딩이 산다.

## 11. `ending_bad` — 재
**쓰이는 곳 (2):** BAD 「재의 백작」(모두를 무너뜨리고 텅 빈 저택, 거울 속의 미소), BAD 「칼끝」(비 오는 옥상, 하람이 떠난다).
**역할:** 승리했지만 아무것도 남지 않은 공허. 메인 테마가 *망가진 채로* 돌아온다.
**음악:** 54 BPM, D 단조, 디튠된(살짝 어긋난) 피아노로 「등대의 주제」 + 낮은 드론 + 먼 빗소리. 끝까지 해결되지 않는 화음.

```
Suno/Udio style: haunting detuned piano, broken music box, low dark drone, distant rain, empty mansion, hollow victory, unresolved harmony, D minor, 54 bpm, desolate, psychological, instrumental, loop
```
```
Stable Audio / MusicGen: Haunting, desolate bad-ending music in D minor at 54 BPM. A slightly detuned piano plays a broken version of the main motif, with a low dark drone and distant rain. Hollow victory in an empty mansion; the harmony never resolves. No drums, no vocals, loopable.
```
→ 레퍼런스: `theme_ashes`를 넣고 "detuned, slower, broken, empty"로 파생.

---

## 12. 제작 순서 & 체크리스트

1. `theme_ashes` → 마음에 드는 버전 확정
2. 파생: `dawn`(희망) · `sorrow`(슬픔) · `ending_bad`(붕괴) · `calm_sea`(평온)
3. 독립: `tension` · `revenge` · `fire` · `romance` · `school_day` · `party`
4. 모든 곡 음량 정규화, 시작·끝 이음매 확인 → `game/assets/bgm/<key>.mp3`

| key | 사용 | BPM | 키 | 핵심 |
|---|---|---|---|---|
| theme_ashes | 6 | 68 | Dm | 메인 테마, 먼저 만들 것 |
| calm_sea | 6 | 76 | F | 도시의 숨소리 |
| school_day | 3 | 96 | G | 밝지만 살짝 어긋남 |
| tension | **12** | 72 | Cm | 대사 밑에 낮게, 타악 없음 |
| sorrow | **12** | 60 | Am | 조용히 아프게 |
| romance | 4 | 76 | G | 따뜻함, 어쿠스틱 기타 |
| party | 1 | 112 | Am | 화려함 + 불길함 |
| fire | 3 | 128 | — | 리듬과 질감 |
| revenge | 4 | 100 | Bm | 체스, 통쾌함 |
| dawn | 1 | 80 | D | 주제의 장조 완성 |
| ending_bad | 2 | 54 | Dm | 망가진 주제 |

`tension`과 `sorrow`는 각각 12장면에 깔리므로 플레이 시간의 상당 부분을 차지한다. 이 두 곡은 여러 번 뽑아서 **오래 들어도 피곤하지 않은 것**을 고르는 게 좋다.
