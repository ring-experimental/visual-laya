# 재의 백작 — 일러스트 컨셉 & 생성 프롬프트

> 모든 작업 완료 후 외부 이미지 생성 모델(Midjourney / SDXL·Illustrious 계열 / NovelAI / FLUX 등)로 제작한다.
> 게임은 지금 플레이스홀더로 동작하며, 아래 **파일명 그대로** `game/assets/...`에 넣으면 자동 교체된다.

## 0. 공통 아트 디렉션

| 항목 | 지정 |
|---|---|
| 장르감 | 현대 한국 청춘 멜로 × 복수극 느와르. "재와 불씨" |
| 화풍 | 셀 + 소프트 페인팅 혼합의 2D 비주얼노벨 일러스트. 선은 가늘고 깔끔하게, 그림자는 차갑게(청회색), 하이라이트는 따뜻하게(앰버) |
| 키 컬러 | 재색 `#1a1617`, 뼈색 `#ece5da`, 불씨 `#ff6a3d` — 모든 그림에 불씨색 포인트(빛·소품·반사) 1곳 |
| 조명 | 역광/림라이트 적극 사용. 안개 낀 항구도시라 공기 원근감 강하게 |
| 교복 | 해무고: 짙은 차콜 블레이저 + 은회색 셔츠 + 버건디 넥타이/리본, 왼쪽 가슴에 등대 문양 엠블럼 |
| 연령감 | 고등학생(16~17세). 과도한 성인화·성적 대상화 금지 |

### 스탠딩 스프라이트 규격
- 크기: **1200×2200px 이상**, 투명 배경 PNG, 무릎 위~전신(허벅지 중간까지 권장), 정면 3/4 포즈
- 같은 캐릭터의 모든 표정은 **같은 포즈·같은 크기·같은 위치** (얼굴만 교체) → 시드 고정 + 인페인팅으로 표정만 바꾸는 방식 권장
- 파일명: `game/assets/characters/<id>_<표정>.png`
- 필수 표정 8종: `neutral, smile, sad, angry, surprised, cold, cry, shy` + 인물별 특수 1종

### 배경 / CG 규격
- 배경 `game/assets/bg/<key>.jpg` 1920×1080, 인물 없음
- CG `game/assets/cg/<key>.jpg` 1920×1080

---

## 1. 윤시온 / 강해온 (주인공, 17)
- 스프라이트 없음(1인칭). CG와 회상에만 등장.
- **현재(윤시온)**: 은발에 가까운 애쉬 블론드 탈색 머리, 앞머리가 눈썹을 덮음. 무테 안경. 가늘고 날카로운 회색 눈. 키 크고 마른 체형. 교복 블레이저를 정석대로 단정히, **왼손에만 검은 가죽 장갑**. 미소는 입꼬리만.
- **과거(강해온, 14)**: 흑갈색 곱슬기 있는 머리, 햇볕에 탄 피부, 큰 눈, 장난스러운 웃음, 해무중 체육복 위에 유리가 떠준 **회색 손뜨개 목도리**.
- 상징 소품: 은색 지포 라이터(아버지 유품), 왼팔의 화상 흉터(손등~팔뚝, 장갑으로 은폐), 체스 나이트 말.

```
prompt (present): anime visual novel illustration, 17 year old korean boy, ash blonde bleached hair with long bangs, rimless glasses, sharp grey eyes, slim tall, charcoal school blazer with silver shirt and burgundy tie, black leather glove on left hand only, cold faint smile, foggy harbor city at dusk behind, rim light in ember orange, delicate lineart, soft painterly shading, cool blue-grey shadows
prompt (past): anime illustration, 14 year old korean boy, messy dark brown wavy hair, tanned skin, big bright eyes, playful grin, middle school tracksuit, hand-knitted grey scarf, winter night, lighthouse beam behind, warm nostalgic tone
```

## 2. 한유리 (17) — 첫사랑 · 청록
- **외형**: 어깨 길이의 부드러운 흑갈색 머리, 한쪽 귀 뒤로 넘기고 **조개껍데기 머리핀**(진주빛 + 청록). 둥근 눈매, 웃을 때 눈이 사라짐. 눈 밑에 옅은 그늘(밤마다 등대에 감).
- **복장**: 교복 리본 대신 니트 조끼, 소매를 손등까지 내려 덮음(손을 숨기는 습관). 합창부 악보 파일.
- **분위기**: 웃고 있지만 슬픔이 배어 나오는 얼굴. 파스텔 청록 + 바다빛.
- **특수 표정 `pin`**: 고개를 살짝 숙이고 머리핀을 만지는 포즈(망설임).

```
prompt: anime visual novel character sprite, full body to mid-thigh, 17 year old korean girl, shoulder length soft dark brown hair tucked behind one ear, pearl seashell hairpin with teal accent, gentle round eyes with faint dark circles, knit vest over school uniform, sleeves covering hands, holding choir sheet music folder, melancholic soft smile, teal and sea-green color accents, transparent background, clean lineart, soft shading
expressions: neutral gentle smile / bright smile with eyes closed / sad looking down / angry teary / surprised hand over mouth / cold distant stare / crying while smiling / shy blush / [pin] touching hairpin head tilted down
```

## 3. 서도현 (17) — 배신한 친구 · 남색
- **외형**: 짧게 정리한 흑발, 각진 턱, 반듯한 눈썹. 수영으로 다져진 넓은 어깨. **손톱을 물어뜯은 흔적**, 눈 충혈.
- **복장**: 반장답게 교복 완벽 착용, 그러나 셔츠 단추 하나가 늘 어긋나 있음. 수영부 저지를 어깨에 걸침.
- **분위기**: 성실한 모범생 → 금이 간 유리. 짙은 남색 + 젖은 머리.
- **특수 표정 `wet`**: 수영장에서 막 나온 젖은 머리, 수영부 저지, 숨이 가쁜 얼굴.

```
prompt: anime visual novel character sprite, 17 year old korean boy, short neat black hair, straight eyebrows, strong jaw, broad swimmer shoulders, perfect school uniform with one misaligned shirt button, swim team jersey over shoulders, bloodshot tired eyes behind polite smile, navy blue color accents, transparent background, clean lineart, soft shading
expressions: polite smile / forced smile / sad guilt / angry shouting / surprised / cold / crying / embarrassed / [wet] wet hair after swimming, breathing hard
```

## 4. 마은채 (17) — 침묵의 공범 · 은회색/버건디
- **외형**: 허리까지 오는 곧은 흑발, 정확한 일자 앞머리. 얇은 은테 안경(공부할 때만, 평소엔 목에 체인으로 걸침). 가늘고 긴 눈, 흰 피부, 무표정이 기본.
- **복장**: 학생회장 완장(버건디), 넥타이 꽉 맨 단정한 교복, 검은 스타킹, 서류철을 품에 안음.
- **분위기**: 얼음공주. 무너질 때 아이 같아지는 갭.
- **특수 표정 `usb`**: 두 손으로 작은 은색 USB를 가슴 앞에 꼭 쥔 포즈, 흔들리는 눈.

```
prompt: anime visual novel character sprite, 17 year old korean girl, very long straight black hair with blunt bangs, thin silver glasses hanging on chain around neck, narrow sharp eyes, pale skin, expressionless, student council president burgundy armband, tightly tied tie, black tights, holding document folder against chest, silver grey and burgundy color accents, transparent background, clean lineart, cool lighting
expressions: expressionless / faint smirk / sad lowered eyes / cold anger / shocked wide eyes / icy glare / crying like a child / flustered blush / [usb] clutching small silver usb drive with both hands, trembling eyes
```

## 5. 백승하 (17) — 왕의 아들 · 금/검정
- **외형**: 금빛이 도는 브라운 투블럭, 한쪽 귀에 작은 금 피어싱. 길고 처진 눈매, 늘 반쯤 감긴 나른한 눈. 입가의 비웃음. 목 옆에 **멍 자국**(셔츠 깃으로 반쯤 가려짐 — 아버지의 폭력 암시, 과도한 묘사 금지).
- **복장**: 교복 블레이저를 어깨에만 걸치고 넥타이 풀어헤침, 고급 손목시계, 반지.
- **분위기**: 화려하고 위험한 폭군 / 혼자 있을 때 텅 빈 아이.
- **특수 표정 `smirk`**: 턱을 들고 내려다보는 비웃음, 손가락으로 사람을 가리키는 포즈.

```
prompt: anime visual novel character sprite, 17 year old korean boy, golden brown undercut hair, small gold earring, long droopy half-lidded eyes, arrogant smirk, school blazer draped over shoulders, loosened tie, luxury wristwatch and ring, faint bruise near collar half hidden, gold and black color accents, transparent background, clean lineart, dramatic rim light
expressions: bored / charming fake smile / hollow sad / furious / startled / cold contempt / crying with clenched teeth / awkward / [smirk] chin up looking down, pointing finger
```

## 6. 진하람 (16) — 복수자의 거울 · 주홍
- **외형**: 턱선 길이의 단발, 끝이 들쭉날쭉(직접 자름). 짙은 주홍빛 눈동자, 짙은 눈썹, 작은 체구. 입술을 꽉 다문 표정이 기본. 손가락에 작은 화상 자국과 반창고.
- **복장**: 교복 위에 **엄마의 낡은 흰 실험 가운**(소매를 접어 입음, 가슴 주머니에 '진선영' 이름표). 어깨에 낡은 갈색 노트(엄마의 실험노트)를 끼고 다님.
- **분위기**: 날 선 고양이. 불꽃 같은 분노와, 가끔 무너지는 열여섯 살.
- **특수 표정 `knife`**: 비에 젖은 채 떨리는 손으로 커터칼을 앞으로 든 포즈, 울면서 노려보는 눈(칼날은 작게, 위협보다 절박함이 보이도록).

```
prompt: anime visual novel character sprite, 16 year old korean girl, short choppy self-cut bob hair, deep vermilion eyes, thick eyebrows, small build, tight-lipped glare, oversized worn white lab coat over school uniform with rolled sleeves and name tag, old brown notebook under arm, band-aids on fingers, vermilion and white color accents, transparent background, clean lineart, warm ember rim light
expressions: guarded neutral / rare small smile / sad / furious / surprised / cold glare / crying angrily / flustered / [knife] soaked in rain, trembling hands holding a small box cutter forward, crying and glaring, desperate not menacing
```

---

## 7. 조연 실루엣 (선택)
- `gyeonghan` 윤경한: 휠체어의 마른 노인, 카디건, 체스판. 따뜻한 갈색.
- `baek` 백태석: 50대, 올백 머리, 맞춤 정장, 금색 커프스, 미소 짓는 눈. 
- `butler` 최 집사: 50대, 회색 정장, 우산.
- 실루엣은 `characters/<id>_neutral.png` 한 장이면 충분.

## 8. 배경 프롬프트 (요약)

| key | 묘사 |
|---|---|
| lighthouse_night / dusk / dawn | 남해안 곶 위의 하얀 등대, 안개, 시간대별 |
| school_fire | 언덕 위 학교 별관이 겨울밤 불길에 휩싸임, 원경 |
| archive_door_fire | 불길 비치는 복도 끝 잠긴 철문, 문틈의 연기 |
| hospital_room / courtroom / detention_center / chess_room | 차가운 형광등 톤 |
| sea_night | 검은 겨울 바다, 해무항 불빛 |
| car_coast_road | 고급 세단 차창 너머 해안도로 |
| school_gate_spring | 벚꽃 + 언덕 위 해무고 정문, 바다가 보임 |
| classroom_day / evening, hallway, cafeteria, council_room, choir_room, infirmary | 해무고 교내 |
| rooftop_dusk / rooftop_rain | 학교 옥상, 철망 너머 항구 |
| pool_night | 실내 수영장, 조명 반만 켜짐, 물빛 반사 |
| yacht_party / yacht_deck_night | 호화 요트 파티, 밤 갑판 |
| sion_mansion_study / sion_mansion_gate_rain / empty_mansion | 바다가 보이는 현대식 저택 |
| storage_room_dark | 체육 창고, 문틈 빛 |
| press_conference | 선거 기자회견장, 플래시 |
| nursing_home | 요양병원 복도와 창가 |
| archive_ruins_night | 불탄 옛 별관 폐허, 검게 그을린 벽, 밤 |
| columbarium | 납골당, 흰 국화 |
| breakwater_night | 방파제 끝 빨간 등표, 밤바다 |
| new_hall_ceremony / new_hall_fire / smoke_corridor / new_hall_roof_night | 새 강당 '윤성관' 개관식 → 화재 |
| airport / spring_sea | 엔딩용 |

공통 접미어: `no humans, visual novel background, cinematic lighting, foggy korean harbor city, highly detailed, 16:9`

## 9. CG 목록
`docs/SCRIPT_FORMAT.md`의 CG 키 목록과 각 설명을 그대로 프롬프트로 사용. 인물 외형은 위 시트를 반드시 붙여 넣어 일관성 유지.
