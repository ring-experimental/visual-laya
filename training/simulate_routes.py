"""story.json 경로 시뮬레이터: 엔진과 같은 규칙으로 대본을 끝까지 실행해 본다.

- 모든 엔딩 도달 가능 여부, 무한 루프, 경로별 분량(줄 수/글자 수/예상 플레이 시간) 확인
  python training/simulate_routes.py
"""

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))
from compile_story import compile_story  # noqa: E402

INIT = {"yuri": 30, "dohyun": 30, "eunchae": 28, "seungha": 25, "haram": 40}
TIER_DELTA = {"high": 9, "mid": 2, "low": -8}  # high = "좋은 답" 평균치
READ_CPM = 450      # 분당 읽는 글자 수(공백 포함, 보통 속도의 VN 독자)
CLICK_SEC = 0.5     # 줄마다 클릭/연출 여유
INPUT_SEC = 40      # 자유 입력 1회 평균


def run(story, policy, venge_for):
    ops, labels = story["ops"], story["labels"]
    st = {"aff": dict(INIT), "flags": {}, "venge": [], "last": 0}
    pc, steps, lines, chars, events, ending = labels["prologue"], 0, 0, 0, 0, None

    def vpct():
        if not st["venge"]:
            return 0
        return round(sum(v * w for v, w in st["venge"]) / sum(w for _, w in st["venge"]) * 100)

    def cond(c):
        for part in re.split(r"\s*&&\s*", c):
            part = part.strip()
            if part.startswith("!flag."):
                ok = not st["flags"].get(part[6:])
            elif part.startswith("flag."):
                ok = bool(st["flags"].get(part[5:]))
            else:
                m = re.match(r"^(aff\.(\w+)|vengeance|last)\s*(>=|<=|==|!=|>|<)\s*(-?\d+)$", part)
                lhs = st["aff"].get(m.group(2), 0) if m.group(2) else (vpct() if m.group(1) == "vengeance" else st["last"])
                ok = eval(f"{lhs} {m.group(3)} {int(m.group(4))}")
            if not ok:
                return False
        return True

    while steps < 20000:
        steps += 1
        if pc >= len(ops):
            break
        op = ops[pc]
        pc += 1
        k = op["op"]
        if k in ("say", "narr"):
            lines += 1
            chars += len(op["text"])
        elif k == "if" and not cond(op["cond"]):
            pc = op["else"]
        elif k == "goto":
            pc = op["to"]
        elif k == "jump":
            pc = labels[op["label"]]
        elif k == "aff":
            st["aff"][op["char"]] = max(0, min(100, st["aff"][op["char"]] + op["delta"]))
        elif k == "flag":
            st["flags"][op["key"]] = True
        elif k == "event":
            events += 1
            ev = story["events"][op["id"]]
            tier = policy(op["id"], ev["target"])
            d = TIER_DELTA[tier]
            if ev["target"] != "none":
                st["aff"][ev["target"]] = max(0, min(100, st["aff"][ev["target"]] + d))
            st["venge"].append((venge_for(op["id"], tier), 2 if op["id"] == "E17" else 1))
            st["last"] = d
            pc = op["cases"][tier]
        elif k == "ending":
            a, v = st["aff"], vpct()
            others = ["yuri", "dohyun", "eunchae", "seungha"]
            if v >= 60:
                ending = "end_bad_ashes"
            elif a["haram"] < 35:
                ending = "end_bad_blade"
            elif all(x >= 50 for x in a.values()) and a["haram"] >= 65 and v < 45:
                ending = "end_true"
            elif a["haram"] >= 55 and sum(a[o] >= 45 for o in others) >= 3:
                ending = "end_happy"
            else:
                ending = "end_normal"
            pc = labels[ending]
        elif k == "end":
            break
    minutes = chars / READ_CPM + lines * CLICK_SEC / 60 + events * INPUT_SEC / 60
    return {"ending": ending, "lines": lines, "chars": chars, "events": events,
            "minutes": round(minutes, 1), "aff": st["aff"], "vengeance": vpct(), "loop": steps >= 20000}


def main():
    story, errors = compile_story()
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    rng = random.Random(1)
    routes = {
        "all high (kind)": (lambda e, t: "high", lambda e, tier: 0.1),
        "all mid": (lambda e, t: "mid", lambda e, tier: 0.3),
        "all low (cruel)": (lambda e, t: "low", lambda e, tier: 0.8),
        "kind but vengeful": (lambda e, t: "high", lambda e, tier: 0.7),
        "hurt haram only": (lambda e, t: "low" if t == "haram" else "high", lambda e, tier: 0.2),
        "kind, but cold to seungha": (lambda e, t: "mid" if t == "seungha" else "high", lambda e, tier: 0.2),
        "neglect seungha+eunchae": (lambda e, t: "mid" if t in ("seungha", "eunchae") else "high", lambda e, tier: 0.2),
    }
    for i in range(4):
        r = random.Random(i)
        routes[f"random #{i}"] = (lambda e, t, r=r: r.choice(["high", "high", "mid", "low"]),
                                  lambda e, tier, r=r: r.random() * 0.6)
    print(f"total: {story['stats']}")
    seen = set()
    for name, (pol, ven) in routes.items():
        res = run(story, pol, ven)
        seen.add(res["ending"])
        print(f"{name:26s} → {res['ending']:14s} {res['minutes']:5.1f}분  lines={res['lines']:4d} chars={res['chars']:5d} "
              f"V={res['vengeance']:3d}% aff={res['aff']}{'  LOOP!' if res['loop'] else ''}")
    missing = {"end_true", "end_happy", "end_normal", "end_bad_ashes", "end_bad_blade"} - seen
    print("unreached endings:", missing or "none")


if __name__ == "__main__":
    main()
