# 대본 포맷 (.vns) 명세

`story/*.vns` 파일은 `server/compile_story.py`가 `game/data/story.json`으로 컴파일한다.
UTF-8, 한 줄에 한 명령. 파일은 이름순으로 이어 붙여진다(파일 끝에서 다음 파일로 자연히 넘어가지 않으므로 반드시 `[jump]`나 `[ending]`/`[end]`로 끝낼 것).

## 기본 줄

| 형식 | 의미 |
|---|---|
| `; 주석` | 무시 |
| 빈 줄 | 무시 |
| `* label_name` | 라벨 (영문 소문자/숫자/_). 장 시작 라벨은 `ch1`, `ch2`… |
| `haram: 대사` | 대사. 화자 id는 STORY_BIBLE의 표 참고. 대사에 따옴표는 붙이지 않는다 (엔진이 「」로 감쌈) |
| `extra[학생A]: 대사` | 임의 이름의 단역 대사 |
| `sion: 대사` | 주인공이 소리 내어 하는 말 |
| 그 외 일반 텍스트 | 지문/독백(주인공 1인칭). 한 줄 = 한 번의 클릭. 너무 길면 나눌 것(한 줄 80자 이내 권장) |

## 연출 명령 `[ ... ]`

| 명령 | 설명 |
|---|---|
| `[chapter 제1장 · 귀환]` | 장 타이틀 카드 표시 |
| `[bg key]` | 배경 전환 (페이드). 키 목록은 아래 |
| `[cg key]` / `[cg off]` | 이벤트 CG 표시/해제 |
| `[show char expr pos]` | 인물 표시. pos = `left` / `center` / `right` (생략 시 center). 이미 있으면 표정만 교체 |
| `[hide char]` / `[hide all]` | 인물 퇴장 |
| `[bgm key]` / `[bgm stop]` | 배경음 |
| `[sfx key]` | 효과음 |
| `[fx shake]` `[fx flash]` `[fx red]` `[fx fadeout]` `[fx fadein]` | 화면 효과 |
| `[wait 1.5]` | 초 단위 대기 |
| `[aff yuri +5]` | 호감도 직접 조정 (스토리상 고정 보정. 남용 금지, ±5 이내) |
| `[flag name]` | 플래그 세움 |
| `[if aff.yuri >= 50]` … `[else]` … `[endif]` | 조건 분기 (중첩 가능). 조건: `aff.<id> <op> N`, `flag.<name>`, `!flag.<name>`, `vengeance >= 60`, `last >= 5`(직전 이벤트 Δ) |
| `[jump label]` | 이동 |
| `[event E01 haram]` … `[endevent]` | 자유 입력 이벤트 정의 (아래) |
| `[case high]` / `[case mid]` / `[case low]` / `[endcase]` | 직전 이벤트 결과에 따른 리액션 |
| `[ending]` | 엔딩 판정 후 해당 엔딩 라벨로 이동 |
| `[end]` | 스태프롤 후 타이틀로 |

## 자유 입력 이벤트

```
[event E01 haram]
prompt: 떨리는 손으로 라이터를 쥔 하람에게, 무슨 말을 할까?
situation: 해질녘 옥상. 하람이 '방화범 강해온 실족사' 신문 스크랩을 태우려다 손이 떨려 못 태운다. 그녀는 "강해온은 너무 쉽게 죽었다, 가족이라도 찾아내겠다"고 말한 뒤 "선배도 날 불쌍하게 보지 마"라고 쏘아붙인다.
need: 동정하지 말고 그녀의 분노를 진지하게 받아줄 것. 섣부른 설교 금지.
hint: 그녀는 위로보다 '같은 편'을 원한다.
[endevent]
[case high]
[show haram surprised center]
haram: …….
...
[case mid]
...
[case low]
...
[endcase]
```

- `event` 블록은 그 자리에서 입력 창을 띄운다. 그 다음 줄에 반드시 `[case …]` 블록이 와야 한다.
- 두 번째 인자는 대상 인물 id (`yuri|dohyun|eunchae|seungha|haram|none`). `none`이면 호감도 변화 없이 복수심만 기록.
- `situation`과 `need`는 **Laya 판정 입력(state)** 에 그대로 들어간다. 구체적으로, 그 순간 인물의 감정이 드러나게 쓴다.
- `hint`는 플레이어가 힌트 버튼을 누를 때만 보인다.
- 리액션은 각 case 4~8줄. `[case]` 블록 안에서 `[aff …]` 추가 보정 금지(판정이 이미 반영됨).

## 배경 키 (`game/assets/bg/<key>.jpg`)

```
black, white,
lighthouse_night, lighthouse_dusk, lighthouse_dawn,
school_fire, archive_door_fire, hospital_room, courtroom, detention_center, chess_room, sea_night,
car_coast_road, school_gate_spring, classroom_day, classroom_evening, hallway, cafeteria,
rooftop_dusk, rooftop_rain, council_room, pool_night, yacht_party, yacht_deck_night,
sion_mansion_study, sion_mansion_gate_rain, storage_room_dark, infirmary,
press_conference, nursing_home, archive_ruins_night, columbarium, choir_room,
breakwater_night, new_hall_ceremony, new_hall_fire, smoke_corridor, new_hall_roof_night,
empty_mansion, airport, spring_sea
```

## CG 키 (`game/assets/cg/<key>.jpg`)

> 장면별 상세 생성 프롬프트는 `docs/CG_PROMPTS.md`.

```
cg_gift_exchange      ; 프롤로그: 등대에서 머리핀과 목도리 교환
cg_locked_door        ; 프롤로그: 불타는 문을 두드리는 소년
cg_courtroom_lie      ; 프롤로그: 증언대의 도현
cg_chess_gyeonghan    ; 프롤로그: 윤경한과 체스
cg_haram_clipping     ; 1장: 옥상에서 스크랩을 태우려는 하람
cg_yuri_lighthouse    ; 1장: 등대 아래 유리
cg_dohyun_pool        ; 2장: 물가에 엎드린 도현
cg_seungha_deck       ; 2장: 갑판의 승하
cg_storage_rescue     ; 3장: 창고 문을 부수는 시온
cg_yuri_rain_glove    ; 3장: 장갑 낀 손을 붙잡는 유리
cg_eunchae_usb        ; 4장: USB를 쥔 은채
cg_seungha_ruins      ; 4장: 폐허에서 무너지는 승하
cg_haram_knife_rain   ; 5장: 비 오는 옥상의 하람
cg_dohyun_breakwater  ; 5장: 방파제의 도현
cg_hall_fire          ; 6장: 불타는 윤성관
cg_roof_confront      ; 6장: 옥상의 백 회장과 승하
cg_true_dawn          ; TRUE: 새벽 등대, 장갑을 벗은 왼손
cg_happy_spring       ; HAPPY: 봄 바다의 하람과 시온
cg_normal_airport     ; NORMAL
cg_bad_mirror         ; BAD 재의 백작: 거울 속 미소
cg_bad_rain           ; BAD 칼끝
```

## BGM 키 (`game/assets/bgm/<key>.mp3`) / SFX 키 (`game/assets/sfx/<key>.mp3`)

> BGM별 생성 프롬프트는 `docs/BGM_PROMPTS.md`.

BGM: `theme_ashes, calm_sea, school_day, tension, sorrow, romance, party, fire, revenge, dawn, ending_bad, memory`
SFX: `fire, door_bang, glass, rain, waves, phone, heartbeat, slap, bell, camera, knife`

(파일이 없으면 무음으로 진행)

## 표정 키 (`game/assets/characters/<char>_<expr>.png`)

`neutral, smile, sad, angry, surprised, cold, cry, shy` + 특수 `yuri_pin, seungha_smirk, haram_knife, eunchae_usb, dohyun_wet`
(특수 표정은 `[show yuri pin left]`처럼 사용)
