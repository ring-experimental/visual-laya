# CG 생성 프롬프트 (21장)

> 각 CG는 대본에서 실제로 쓰이는 순간을 기준으로 썼다. 파일은 `game/assets/cg/<key>.png` (16:9, 1920×1080 권장. 1672×941처럼 16:9면 OK).
> 프롬프트 = **[공통 스타일] + [등장인물 블록] + [장면 프롬프트]**. 네거티브는 맨 아래 공통.

---

## 0. 공통

### 공통 스타일 (모든 CG 앞에 붙임)
```
anime visual novel event CG, cinematic 16:9 composition, detailed 2D illustration, clean thin lineart, soft painterly shading, cool blue-grey shadows with warm ember-orange accent light, atmospheric fog, foggy korean harbor city, emotional dramatic lighting, high detail, masterpiece
```

### 공통 네거티브
```
text, watermark, signature, logo, speech bubble, extra fingers, fused fingers, deformed hands, extra limbs, bad anatomy, multiple heads, lowres, blurry face, nsfw, revealing clothes, cleavage, mature body, gore, blood, wound detail, chibi, 3d render, photo
```

### 등장인물 블록 (이미 만든 스프라이트 외형 기준 — 그대로 복사)

| id | 블록 |
|---|---|
| **sion** (현재, 17) | `17yo korean boy, ash-blonde messy hair with long bangs, thin rimless round glasses, grey eyes, slim and tall, black school blazer with lighthouse emblem on left chest, grey shirt, loose burgundy tie, black leather glove on his LEFT hand only, right hand bare` |
| **haeon** (과거, 14) | `14yo korean boy, messy wavy dark brown hair, tanned skin, bright grey-brown eyes, navy and white middle school tracksuit with burgundy stripes, chunky hand-knitted grey scarf, black backpack` |
| **yuri** (17) | `17yo korean girl, shoulder-length soft brown hair, white seashell-and-pearl hairpin on her right side, gentle grey eyes, grey cable-knit sweater vest over white shirt, teal ribbon bow, long sleeves covering her hands, dark pleated skirt` |
| **yuri14** (과거, 14) | `14yo korean girl, younger rounder face, shoulder-length brown hair, red nose from cold, winter middle school uniform with navy duffle coat, mittens` |
| **dohyun** (17) | `17yo korean boy, short neat black hair, dark grey-blue eyes, broad swimmer shoulders, navy track jacket with white stripes over black blazer, white shirt, striped burgundy tie` |
| **dohyun14** (과거, 14) | `14yo korean boy, short black hair, younger face, middle school winter uniform, stiff posture` |
| **eunchae** (17) | `17yo korean girl, very long dark brown hair with blunt bangs, amber eyes, silver glasses chain hanging from her ears, black blazer, burgundy student council armband, burgundy tie, dark red plaid skirt, black tights` |
| **seungha** (17) | `17yo korean boy, golden-brown swept hair, small gold earring, droopy half-lidded amber eyes, black blazer with gold trim draped over shoulders, grey shirt with rolled sleeves, loose burgundy tie, gold ring, black wristwatch, faint bruise on the side of his neck` |
| **haram** (16) | `16yo korean girl, short choppy dark brown bob, deep red-vermilion eyes, small build, oversized worn white lab coat with rolled sleeves and pens in breast pocket over black blazer and burgundy tie, dark red plaid skirt, old brown leather notebook` |
| **gyeonghan** | `frail elderly korean man in his late 70s, thin white hair, beige cardigan, wheelchair, kind but sharp eyes, wrinkled hands` |
| **baek** | `korean man in his 50s, slicked-back black hair with grey at temples, tailored charcoal three-piece suit, gold cufflinks, calm smiling eyes that do not smile` |

### 일관성 팁
- **레퍼런스 이미지를 같이 넣을 것.** IP-Adapter, Midjourney `--cref`, NovelAI 바이브 트랜스퍼 등에 `game/assets/characters/<id>_neutral.png`를 넣으면 프롬프트만 쓸 때보다 훨씬 덜 흔들린다.
- **왼손 장갑**은 모델이 자주 틀린다. 결과를 보고 장갑이 오른손이면 좌우 반전하거나 다시 뽑을 것. 시온의 왼손 화상은 정체를 증명하는 장치라 CG에서 틀리면 장면이 성립하지 않는다(특히 storage_rescue, yuri_rain_glove, true_dawn).
- **글자(신문 제목, 현수막)**는 모델에 맡기지 말고 비워 두었다가 후보정으로 넣는 게 안전하다.
- 프롤로그 CG(gift_exchange, locked_door, courtroom_lie)는 **14세 버전**이다. 17세 블록을 쓰지 말 것.
- 위험 장면(커터칼, 방파제, 화재)은 *절박함*으로 그린다. 위협·상해 묘사가 아니라는 점이 프롬프트에 명시돼 있다. 필터에 걸리면 괄호 안 대체어를 쓴다.

---

## 1. 프롤로그

### `cg_gift_exchange` — 등대 아래, 목도리와 머리핀
**순간:** 축제 전야, 유리가 눈을 감긴 해온의 목에 직접 뜬 회색 목도리를 감아 준다. 행복의 마지막 장면.
**반드시:** 하얀 등대 불빛 / 회색 손뜨개 목도리를 감아 주는 유리의 손 / 해온 손바닥 위의 조개 머리핀 / 하얀 입김.
```
[haeon] [yuri14], winter night at the foot of a white lighthouse on a seaside cliff, yuri standing on tiptoe wrapping a chunky hand-knitted grey scarf around haeon's neck, haeon with eyes closed and a shy grin holding out his palm with a small white seashell hairpin, white breath in cold air, sweeping lighthouse beam behind them, harbor lights and fog below, gentle snow flakes, warm nostalgic glow, medium shot, tender bittersweet mood
```

### `cg_locked_door` — 잠긴 문
**순간:** 불타는 별관 복도. 안에서 선생님이 문을 두드리고, 해온이 밖에서 잠긴 철문을 온몸으로 연다.
**반드시:** 밖에서 잠긴 철문(자물쇠) / 문틈의 불빛과 연기 / 목도리 끝에 튄 불티 / 왼팔로 문을 미는 자세. 화상 묘사는 하지 않는다.
```
[haeon], burning school corridor at night, a heavy steel archive door locked from the outside with a padlock, orange firelight and smoke leaking through the door gap, haeon throwing his whole body against the door with his left shoulder and arm, desperate shouting face, sparks landing on the end of his grey scarf, embers in the air, dark smoke on the ceiling, dramatic low angle side view, red-orange and black palette, intense but not gory
```

### `cg_courtroom_lie` — 증언대
**순간:** 소년법정. 도현이 증언대에서 시선을 떨군 채 위증한다. 옆의 증인석은 비어 있고, 방청석 맨 뒤에서 백 회장이 웃는다.
**반드시:** 고개 숙인 도현 / 증언대를 꽉 쥔 손 / 빈 의자에 떨어지는 빛 / 흐릿한 배경 속 백 회장의 미소.
```
[dohyun14] standing at the witness stand of a small cold juvenile courtroom, head down avoiding eye contact, knuckles white gripping the wooden stand, an empty witness chair beside him lit by a pale shaft of window light, in the blurred far background last row a man in a grey coat [baek] smiling faintly, cold fluorescent blue-grey light, shallow depth of field focused on dohyun, oppressive silence
```

### `cg_chess_gyeonghan` — 다시 세운 킹
**순간:** 소년원 면회실. 노인이 쓰러진 해온의 킹을 집어 다시 판 위에 세운다.
**반드시:** 체스판 클로즈업 / 킹을 세우는 노인의 주름진 손 / 맞은편의 15세 해온(회색 체육복, 짧아진 머리).
```
[gyeonghan] in a wheelchair at a table in a bare detention center visiting room, his wrinkled hand setting a fallen black king upright on a wooden chessboard, across the table a 15yo korean boy with short-cropped dark brown hair in a plain grey detention sweatsuit watching with guarded eyes, spring afternoon light through barred window, dust in light, warm brown and grey tones, close-up on hands and board with both faces visible, quiet turning point
```

---

## 2. 제1장

### `cg_haram_clipping` — 태우지 못한 부고
**순간:** 노을 옥상. 하람이 철망 아래 쪼그려 앉아, 누런 신문 스크랩(강해온 실족사 기사)을 라이터로 태우려다 손이 떨려 불이 꺼진다.
**반드시:** 쪼그려 앉은 자세 / 떨리는 손의 라이터 불꽃 / 누런 신문 조각(글자는 비워 둘 것) / 철망 너머 노을 항구.
```
[haram] crouching alone by the chain-link fence on a school rooftop at sunset, holding a yellowed newspaper clipping in one hand and a flickering cheap lighter in her trembling other hand, the small flame bending in the wind, jaw clenched, eyes wet but furious, lab coat sleeves fluttering, orange-purple sunset over the foggy harbor through the fence, side view medium shot, lonely and defiant
```

### `cg_yuri_lighthouse` — 등대 아래 유리
**순간:** 하굣길, 시온의 시점. 하얀 등대 아래 유리가 무릎을 끌어안고 바다만 본다.
**반드시:** 멀리서 보는 구도(시온 시점) / 무릎을 안은 유리 / 머리핀의 반짝임 / 노을 등대.
```
[yuri] sitting alone on the rocks at the foot of a white lighthouse at dusk, hugging her knees, looking out at the sea, wind lifting her hair, the seashell hairpin catching the last sunlight, seen from behind at a slight distance as if someone just arrived, orange and teal dusk sky, fog over the sea, melancholic wide shot
```

---

## 3. 제2장

### `cg_dohyun_pool` — 벌
**순간:** 밤 11시, 불 하나만 켜진 실내 수영장. 레인을 50번 왕복한 도현이 물가 타일에 엎드려 숨을 몰아쉰다.
**반드시:** 조명 하나 / 물가 타일 위에 무너진 자세 / 젖은 머리 / 물빛 반사. 상반신 노출 대신 래시가드를 입힌다.
```
[dohyun] (wearing a black swim team rash guard and dark swim jammers, no jacket), collapsed on hands and knees on wet tiles at the edge of an indoor pool at night, soaked hair dripping, head hanging, gasping for breath, only one ceiling light on, the rest dark, rippling blue water reflections on his face and walls, high angle shot, lonely self-punishment mood
```
대체: 너무 노출이 걱정되면 `wearing navy track jacket over rash guard`를 넣는다.

### `cg_seungha_deck` — 목줄
**순간:** 파티가 끝난 요트 선실 앞. 아버지 전화를 끊은 승하가 웃으면서 벽을 주먹으로 친다. 금반지가 벽을 긁는다.
**반드시:** 한 손엔 휴대폰, 다른 손 주먹이 벽에 / 웃는데 텅 빈 얼굴 / 금반지 / 흐릿한 파티 조명.
```
[seungha] alone outside a yacht cabin at night after a party, phone in one hand hanging down, his other fist pressed against the cabin wall after punching it, gold ring scraped, laughing with hollow empty eyes, blazer slipping off his shoulders, blurred golden party lights and the night city skyline behind, cold blue moonlight on his face, medium close-up, beautiful but broken
```

---

## 4. 제3장

### `cg_storage_rescue` — 이번엔, 열렸다
**순간:** 하람이 갇힌 체육 창고. 하람의 시점에서, 시온이 네 번째 발길질에 문을 부수고 들어온다. 3년 전 열지 못한 문의 반복.
**반드시:** 어두운 창고 안에서 바깥을 보는 구도(하람 시점) / 쏟아지는 역광 / 부서진 문짝과 먼지 / 시온의 실루엣과 **왼손의 찢어진 검은 장갑** / 화면 아래 노트를 꼭 쥔 하람의 손.
```
POV from inside a pitch-dark school sports storage room, the door bursting inward off its hinges, blinding white light flooding in, dust and splinters in the air, [sion] silhouetted in the doorway after kicking the door, breathing hard, glasses glinting, his black glove on his LEFT hand torn at the edge, in the bottom foreground a girl's trembling hands clutching an old brown notebook, strong backlight and god rays, dramatic rescue moment
```

### `cg_yuri_rain_glove` — 이 손
**순간:** 비 오는 밤, 시온의 저택 대문 앞. 흠뻑 젖은 유리가 시온의 장갑 낀 왼손을 두 손으로 잡아 자기 뺨에 댄다. "해온이지?"
**반드시:** 클로즈업 / 검은 장갑 낀 손을 감싼 유리의 두 손 / 뺨에 닿은 손 / 빗물과 눈물 / 머리핀 / 대문 등불의 따뜻한 빛.
```
close-up, rainy night at a modern mansion gate, [yuri] soaked by rain with wet hair stuck to her cheeks and a drenched cardigan, holding a black-gloved LEFT hand with both of her hands and pressing it against her cheek, eyes closed, tears mixing with rain, seashell hairpin glistening, warm gate lamp light against cold blue rain, raindrops in the foreground, intimate heartbreaking moment
```

---

## 5. 제4장

### `cg_eunchae_usb` — 열쇠
**순간:** 학생회실. 은채가 서랍 안쪽에 테이프로 붙여 숨겨 둔 봉투에서 꺼낸 작은 은색 USB를 손바닥에 올려 보인다.
**반드시:** 손바닥 위 은색 USB(화면의 초점) / 열린 서랍과 떼어 낸 봉투·테이프 / 흔들리는 눈의 은채 / 안경 체인과 완장.
```
[eunchae] sitting at a desk in the student council room at evening, an open bottom drawer with a small envelope and peeled tape, holding out a tiny silver usb drive on her open palm toward the viewer, focus on the usb, her face behind it slightly soft-focused, composed expression cracking, trembling lips, glasses chain glinting, warm desk lamp against blue window light, close-up over the shoulder
```

### `cg_seungha_ruins` — 내가 잠갔어
**순간:** 밤, 불탄 옛 별관(자료관) 폐허. 승하가 그을린 계단에 앉아 녹슨 열쇠를 쥐고 자백한다.
**반드시:** 그을린 벽과 무너진 지붕 사이 달빛 / 손 안의 녹슨 열쇠 / 무너지는 얼굴.
```
[seungha] sitting on charred concrete steps inside the burned ruins of an old school annex at night, blackened walls, collapsed roof beams, moonlight falling through the broken roof, holding a small rusted key in both hands between his knees, staring at it, face crumbling as he confesses, tears on the verge, blazer fallen beside him, cold blue moonlight with faint orange ember tones, wide-to-medium shot, guilt and confession
```

---

## 6. 제5장

### `cg_haram_knife_rain` — 칼끝 (게임 최대 클라이맥스)
**순간:** 비 오는 학교 옥상. 시온의 정체를 안 하람이 떨리는 손으로 커터칼 날을 밀어 시온 쪽을 향해 든다. 울면서 노려본다.
**반드시:** 장대비 / 흠뻑 젖은 실험 가운 / 작은 커터칼(위협보다 **절박함**) / 미친 듯이 떨리는 손 / 울며 노려보는 얼굴 / 시온 시점.
```
heavy rain on a school rooftop at night, [haram] soaked to the bone, wet hair stuck to her face, white lab coat drenched and heavy, holding a small box cutter out in front of her with both trembling hands, the blade barely extended, crying and glaring at the same time, desperate and heartbroken rather than menacing, blurred city lights and chain-link fence behind, cold blue rain with a single warm light source, POV from the person she faces, slight low angle
```
필터에 걸리면 `holding a small box cutter` → `clenching her fists, trembling, holding a small silver object`.

### `cg_dohyun_breakwater` — 한 걸음 더는 바다
**순간:** 밤 방파제 맨 끝. 흠뻑 젖은 도현이 빨간 등표 아래 서 있고, 등대 불빛이 돌 때마다 윤곽이 드러난다. 뛰어내리는 장면이 아니라 *멈춰 서 있는* 장면.
**반드시:** 원경(작은 인물) / 방파제 끝의 빨간 등표 / 테트라포드에 부서지는 검은 파도 / 회전하는 등대 빛줄기 / 젖은 도현의 뒷모습.
```
night breakwater, a lone figure [dohyun] soaked from head to toe standing still at the very end of the concrete breakwater under a red beacon light tower, back half-turned, shoulders shaking, black waves crashing on tetrapods, a sweeping lighthouse beam illuminating his silhouette, harbor lights far behind in the fog, wide shot from behind with the figure small in frame, tense and lonely, no jumping
```

---

## 7. 제6장

### `cg_hall_fire` — 3년 전의 재현
**순간:** 윤성관 개관식 도중 기계실 화재. 정전, 붉은 비상등, 무대 뒤에서 쏟아지는 검은 연기, 출구로 몰리는 학생들.
**반드시:** '개관식' 현수막과 무대(배경 new_hall_fire와 같은 공간) / 붉은 비상등 / 연기 / 도망치는 학생들 실루엣 / 화면 중앙에 홀로 무대 쪽을 보고 선 시온.
```
grand new school auditorium during an opening ceremony turning into chaos, thick black smoke pouring from behind the stage, lights out, pulsing red emergency lights, the ceremony banner above the stage starting to burn, silhouettes of students in uniforms running toward the exits, toppled chairs, scattered flowers, in the center [sion] standing still facing the stage against the fleeing crowd, wide cinematic shot, red black and orange palette, embers, chaos but no injuries shown
```

### `cg_roof_confront` — 무릎 꿇어라
**순간:** 불타는 윤성관 옥상. 시온이 옥상 문을 연다. 난간 앞에 백 회장이 서 있고, 승하는 그 앞에 반쯤 무릎이 꺾여 있다. 아래에서 소방차 불빛이 맴돈다.
**반드시:** 문에서 보는 구도(시온 시점) / 난간 앞에 선 백 회장 / 그 앞에서 무너지는 승하 / 아래에서 올라오는 붉고 푸른 경광등 빛 / 연기.
```
rooftop at night seen from an opened rooftop door, [baek] standing calmly at the railing in a tailored suit with hands behind his back, a faint cold smile, [seungha] in front of him with one knee buckling toward the ground, head bowed, fists clenched, red and blue fire truck lights flashing up from below, drifting smoke, wind, city lights, tense standoff composition with the father towering over the son, cinematic
```

---

## 8. 엔딩

### `cg_true_dawn` — TRUE · 새벽의 등대 (최종 CG)
**순간:** 새벽 4시 반 등대곶. 시온이 처음으로 왼손 장갑을 벗는다. 장갑이 바람에 날아가고, 흉터 위로 첫 햇살이 내려앉는다. 다섯 친구가 곁에 서 있다.
**반드시:** 화면 앞쪽에 **맨손이 된 왼손**(오래되어 옅어진 화상 흉터, 고어 없이) / 바람에 날아가는 검은 장갑 / 수평선의 첫 햇살 / 뒤쪽 등대 아래 다섯 명(유리, 도현, 은채, 승하, 하람).
```
dawn at a white lighthouse on a seaside cliff, first sunlight breaking over the horizon, foreground close-up of a young man's bare LEFT hand raised toward the sunrise with a faded old pale burn scar on the back of the hand and forearm, a black leather glove flying away in the wind, behind in soft focus five teenagers standing together near the lighthouse — [yuri], [dohyun], [eunchae], [seungha], [haram] — wind in their hair, pink-gold sky over blue fog, hopeful, cathartic, breathtaking
```
흉터가 징그럽게 나오면 `faded old pale burn scar`를 `subtle faded scar marks`로 약하게 바꾼다.

### `cg_happy_spring` — HAPPY · 봄의 귀환
**순간:** 4월 봄 바다. 하람이 흰 가운 대신 연한 봄 니트를 입고, 신발을 벗고 먼저 물에 발을 담근 뒤 뒤돌아 웃는다.
**반드시:** 실험 가운 없음(연한 니트) / 맨발로 얕은 물 / 손에 든 신발 / 뒤돌아보는 미소 / 벚꽃잎 / 화면 앞 시온의 손(시점).
```
[haram] without lab coat, wearing a light pastel spring knit sweater and skirt, barefoot in shallow clear sea water at a spring beach, holding her shoes in one hand, turning back toward the viewer with a small genuine smile, cherry blossom petals drifting on the wind, sparkling water, bright soft morning light, a hand reaching from the viewer's side in the foreground, gentle hopeful mood
```

### `cg_normal_airport` — NORMAL · 백작의 퇴장
**순간:** 공항 탑승 대기. 이름을 되찾지 않고 떠나는 시온, 휴대폰에 하람의 문자가 온다.
**반드시:** 뒷모습 또는 옆모습 / 기내용 캐리어 / 손의 휴대폰 화면 빛 / 큰 창 너머 비행기와 아침 햇살 / 혼자.
```
[sion] seen from behind sitting alone at an airport departure gate by a huge window, carry-on suitcase beside him, looking down at the glowing screen of his phone in his gloved left hand, airplanes and morning sunlight outside, long shadows, empty seats around him, quiet bittersweet farewell, wide shot
```

### `cg_bad_mirror` — BAD · 재의 백작
**순간:** 텅 빈 저택 현관 거울. 넥타이를 고쳐 매는 시온. 거울 속의 그는 입꼬리만 천천히 올려 웃는다. 백 회장의 웃음이다.
**반드시:** 거울에 비친 얼굴이 주인공 / 실제 얼굴은 무표정, **거울 속은 입꼬리만 올린 차가운 미소** / 흰 천 덮인 가구 / 차가운 빛.
```
[sion] standing in front of a tall entrance hall mirror in an empty mansion with white sheets covering the furniture, adjusting his tie, his real face expressionless, but his reflection in the mirror smiling slowly with only the corners of the mouth, cold predatory smile, eyes not smiling, cold blue moonlight and a single warm lamp, the reflection in sharp focus, unsettling psychological horror mood, no blood
```

### `cg_bad_rain` — BAD · 칼끝
**순간:** 비 오는 옥상. 하람이 커터칼을 바닥에 내려놓고 "법한테 맡길 거야"라며 떠난다. 빗물이 칼날 위로 흐르고, 아무도 줍지 않는다.
**반드시:** 바닥 높이 로우앵글 / 화면 앞 젖은 바닥 위의 커터칼(빗물이 흐름) / 뒤쪽에 옥상 문으로 걸어가는 하람의 뒷모습과 젖은 노트 / 열린 채인 문.
```
extremely low angle at floor level on a rain-soaked school rooftop at night, in the sharp foreground a small box cutter lying abandoned on the wet concrete with rainwater running over it, in the blurred background [haram] walking away toward the rooftop door with her back turned, clutching a wet notebook, the door open with dim light inside, heavy rain, puddle reflections, cold desaturated blue, final and quiet
```

---

## 9. 체크리스트

| key | 시점 | 핵심 확인 |
|---|---|---|
| cg_gift_exchange | 3인칭 | 14세, 목도리·머리핀 |
| cg_locked_door | 3인칭 | 밖에서 잠긴 자물쇠 |
| cg_courtroom_lie | 3인칭 | 빈 증인석, 뒤쪽 백 회장 |
| cg_chess_gyeonghan | 3인칭 | 킹을 세우는 손 |
| cg_haram_clipping | 3인칭 | 신문 글자는 후보정 |
| cg_yuri_lighthouse | 시온 시점 | 뒷모습, 원경 |
| cg_dohyun_pool | 3인칭 | 래시가드 |
| cg_seungha_deck | 3인칭 | 금반지, 휴대폰 |
| cg_storage_rescue | 하람 시점 | **왼손** 찢어진 장갑 |
| cg_yuri_rain_glove | 클로즈업 | **왼손** 장갑 |
| cg_eunchae_usb | 시온 시점 | USB 초점 |
| cg_seungha_ruins | 3인칭 | 녹슨 열쇠 |
| cg_haram_knife_rain | 시온 시점 | 절박함 > 위협 |
| cg_dohyun_breakwater | 원경 | 멈춰 서 있음 |
| cg_hall_fire | 원경 | 개관식 현수막 |
| cg_roof_confront | 문에서 | 부자 구도 |
| cg_true_dawn | 시온 시점 | **왼손** 맨손 + 5명 |
| cg_happy_spring | 시온 시점 | 가운 없음 |
| cg_normal_airport | 뒷모습 | 혼자 |
| cg_bad_mirror | 거울 | 거울 속만 미소 |
| cg_bad_rain | 바닥 로우앵글 | 버려진 칼 |
