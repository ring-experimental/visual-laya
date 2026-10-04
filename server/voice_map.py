"""대사(say op) → 보이스 id / 음성 파일 경로.

tools/gen_voices.py(생성)와 compile_story.py(story.json에 voice 필드 기록)가 함께 쓴다.
파일명은 (보이스 id, 대사 텍스트)의 해시라서, 대본을 고치면 바뀐 줄만 새로 생성하면 된다.
"""

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICE_DIR = ROOT / "game" / "assets" / "voice"
EXT = ".mp3"

# extra[이름] → 공용 단역 보이스 (tools/voices.json의 id)
EXTRA_VOICES = {
    "???": "teacher_f", "형사": "detective", "판사": "judge", "재판장": "judge",
    "뉴스": "anchor_f", "사회자": "anchor_f", "기자": "reporter_m", "담임": "teacher_m",
    "측근": "student_m", "학생A": "student_m", "학생B": "student_f",
}
SPOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]")


def voice_of(op):
    """say op의 보이스 id. 소리 낼 글자가 없는 줄(…… 등)은 None."""
    if op.get("op") != "say" or not SPOKEN_RE.search(op["text"]):
        return None
    who = op["who"]
    if who == "extra":
        return EXTRA_VOICES.get(op["name"], "extra_m")
    if who == "sion" and op.get("src", "").startswith("00_prologue"):
        return "haeon"  # 프롤로그의 시온은 14살 강해온
    return who


def tts_text(text):
    """화면 표시용 문장 → 낭독용 문장."""
    text = text.replace("—", ", ").replace("~", "")
    text = re.sub(r"…+", "…", text)
    return text.strip(" ,")


def voice_rel(op):
    """game/assets 기준 상대 경로 (예: voice/haram/1a2b3c4d5e6f.mp3) 또는 None."""
    vid = voice_of(op)
    if vid is None:
        return None
    h = hashlib.sha1(f"{vid}\n{op['text']}".encode("utf-8")).hexdigest()[:12]
    return f"voice/{vid}/{h}{EXT}"
