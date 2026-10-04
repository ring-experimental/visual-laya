"""대사 → Higgs TTS 3 감정 제어 토큰.

말하는 인물의 직전 표정([show <char> <expr>])을 토큰으로 바꾼다. 표정이 없는 인물(시온·조연·단역)은
문장부호만 본다. 특정 줄을 직접 지정하려면 tools/voice_emotions.json에 "파일:줄": "토큰"을 넣는다
(빈 문자열이면 감정 없이 읽음).

토큰 문법: https://huggingface.co/bosonai/higgs-tts-3-4b (emotion / style / prosody)
"""

import json
from pathlib import Path

OVERRIDES = Path(__file__).resolve().parent / "voice_emotions.json"

EXPR_TAGS = {
    "neutral": "",
    "smile": "<|emotion:contentment|>",
    "sad": "<|emotion:sadness|>",
    "angry": "<|emotion:anger|>",
    "surprised": "<|emotion:surprise|>",
    "cold": "<|emotion:bitterness|><|prosody:expressive_low|>",
    "cry": "<|emotion:sadness|><|prosody:expressive_high|>",
    "shy": "<|emotion:shame|>",
    "pin": "<|emotion:longing|>",          # 유리: 머리핀을 만지는
    "smirk": "<|emotion:amusement|>",      # 승하: 비웃음
    "knife": "<|emotion:anger|><|prosody:expressive_high|>",  # 하람: 칼
    "usb": "<|emotion:fear|>",             # 은채: USB를 쥔
    "wet": "<|emotion:helplessness|>",     # 도현: 물에 젖은
}
SHOUT_EXPRS = {"angry", "cry", "knife"}


def tags_for(text, expr):
    tags = EXPR_TAGS.get(expr or "neutral", "")
    if text.rstrip("…. ").endswith("!"):
        if expr in SHOUT_EXPRS:
            tags += "<|style:shouting|>"
        elif not tags:
            tags = "<|prosody:expressive_high|>"
    return tags


def line_tags(ops):
    """compile_story ops → {src: 토큰 문자열} (say 줄만)."""
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.exists() else {}
    overrides = {k: v for k, v in overrides.items() if not k.startswith("_")}
    expr, out = {}, {}
    for op in ops:
        if op["op"] == "show":
            expr[op["char"]] = op["expr"]
        elif op["op"] == "hide":
            if op["char"] == "all":
                expr.clear()
            else:
                expr.pop(op["char"], None)
        elif op["op"] == "say":
            src = op["src"]
            out[src] = overrides[src] if src in overrides else tags_for(op["text"], expr.get(op["who"]))
    return out
