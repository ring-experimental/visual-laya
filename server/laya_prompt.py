"""Laya 판정 입력(state)과 질문(questions) 정의.

학습(training/)과 추론(server/judge.py)이 반드시 같은 문자열을 쓰도록 이 모듈 하나만 참조한다.
"""

CHAR_PROFILES = {
    "yuri": ("한유리", "주인공의 첫사랑. 3년 전 그의 알리바이를 알고도 침묵했고, 그가 죽은 게 자기 탓이라 믿는다. 밝은 척하지만 속은 죄책감으로 무너져 있다."),
    "dohyun": ("서도현", "주인공의 옛 단짝. 가족의 빚 때문에 법정에서 위증했다. 모범생의 가면 아래 자기혐오로 스스로를 벌하며 산다."),
    "eunchae": ("마은채", "학생회장. 검사 출신 정치인의 딸. 아버지가 묻은 화재 CCTV 원본을 몰래 숨겨 왔다. 차갑고 논리적이며 아버지에게 인정받는 것만이 존재 이유였다."),
    "seungha": ("백승하", "해무그룹 회장의 아들. 학교의 폭군. 아버지의 지시로 화재 당일 자료관 문을 잠갔다. 아버지에게 길들여진 삶과 죄책감에 짓눌려 있다."),
    "haram": ("진하람", "1학년. 3년 전 화재로 엄마를 잃었다. 방화범으로 알려진 강해온을 증오한다. 동정을 싫어하고 분노를 진지하게 받아줄 사람이 필요하다."),
    "none": ("(특정 인물 없음)", "주인공 자신의 선택이 드러나는 장면."),
}

IMPACT_LEVELS = [
    "깊은 상처를 주거나 적대감을 키운다",
    "무신경하거나 엉뚱해서 실망시킨다",
    "무난하지만 마음에 닿지 않는다",
    "공감하며 마음을 열게 한다",
    "상대가 필요로 하던 말을 정확히 건네 깊이 흔든다",
]

QUESTIONS = {
    "impact": {
        "type": "score",
        "instructions": "플레이어(시온)의 말이 상대의 마음에 어떤 영향을 주는가?",
        "criteria": IMPACT_LEVELS,
    },
    "vengeance": {
        "type": "noul",
        "instructions": "플레이어의 말이 차갑고 계산적이거나, 복수심·증오·상대를 조종하려는 의도를 드러내는가?",
    },
    "nonsense": {
        "type": "noul",
        "instructions": "플레이어의 말이 장면과 무관한 장난, 의미 없는 문자열, 메타 발언, 또는 욕설인가?",
    },
}

# 호감도 가중치 (impact 단계별)
IMPACT_WEIGHTS = [-12.0, -5.0, 0.0, 7.0, 13.0]


def build_state(event: dict, text: str) -> str:
    target = event.get("target", "none")
    name, profile = CHAR_PROFILES.get(target, CHAR_PROFILES["none"])
    text = " ".join(str(text).split())[:300]
    return (
        f"[장면] {event.get('situation', '').strip()}\n"
        f"[상대] {name}: {profile}\n"
        f"[상대에게 필요한 것] {event.get('need', '').strip()}\n"
        f"[플레이어(시온)의 말] \"{text}\""
    )


def score_answers(impact_probs, vengeance: float, nonsense: float) -> dict:
    """판정 확률 → 호감도 변화량과 리액션 단계."""
    delta = sum(p * w for p, w in zip(impact_probs, IMPACT_WEIGHTS))
    if nonsense > 0.5:
        delta = min(delta, 0.0) - 8.0 * nonsense
    delta = int(round(delta))
    tier = "low" if delta <= -3 else ("high" if delta >= 5 else "mid")
    return {"delta": delta, "tier": tier}
