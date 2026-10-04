"""story/*.vns → game/data/story.json 컴파일러.

사용법: python server/compile_story.py [--check]
출력 JSON:
  {"ops": [...], "labels": {name: index}, "events": {id: {...}}, "speakers": {...}, "stats": {...}}
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from voice_map import VOICE_DIR, voice_rel  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STORY_DIR = ROOT / "story"
OUT = ROOT / "game" / "data" / "story.json"

SPEAKERS = {
    "sion": "시온", "yuri": "유리", "dohyun": "도현", "eunchae": "은채", "seungha": "승하",
    "haram": "하람", "gyeonghan": "윤경한", "baek": "백 회장", "jang": "장 실장", "ma": "마정훈",
    "butler": "최 집사", "mom": "어머니",
}
TARGETS = {"yuri", "dohyun", "eunchae", "seungha", "haram", "none"}
SAY_RE = re.compile(r"^([a-z_]+)(?:\[([^\]]+)\])?\s*:\s*(.*)$")
CMD_RE = re.compile(r"^\[(\w+)\s*(.*?)\]$")
COND_RE = re.compile(r"^(!?flag\.\w+|aff\.\w+\s*(>=|<=|==|!=|>|<)\s*-?\d+|vengeance\s*(>=|<=|>|<)\s*\d+|last\s*(>=|<=|>|<)\s*-?\d+)$")


class CompileError(Exception):
    pass


def write_asset_manifest():
    """game/assets 아래 실제 존재하는 이미지 목록 → game/data/assets.json (엔진이 404 없이 교체 판단)."""
    base = ROOT / "game" / "assets"
    files = sorted(p.relative_to(base).as_posix() for p in base.rglob("*")
                   if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"))
    out = ROOT / "game" / "data" / "assets.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(files, ensure_ascii=False), encoding="utf-8")
    return files


def compile_story():
    ops, labels, events, errors = [], {}, {}, []
    stack = []  # 열린 if / case 블록
    pending_event = None  # event 직후 case를 기다리는 중
    chars = 0

    def err(where, msg):
        errors.append(f"{where}: {msg}")

    files = sorted(STORY_DIR.glob("*.vns"))
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            raw = lines[i]
            where = f"{path.name}:{i + 1}"
            line = raw.strip()
            i += 1
            if not line or line.startswith(";"):
                continue
            if line.startswith("*"):
                name = line[1:].strip()
                if name in labels:
                    err(where, f"중복 라벨 {name}")
                labels[name] = len(ops)
                continue

            m = CMD_RE.match(line)
            if m:
                cmd, arg = m.group(1), m.group(2).strip()
                parts = arg.split()
                src = {"src": where}
                if cmd == "event":
                    if len(parts) != 2 or parts[1] not in TARGETS:
                        err(where, f"event 형식 오류: {arg}")
                        continue
                    ev = {"id": parts[0], "target": parts[1]}
                    while i < len(lines) and lines[i].strip() != "[endevent]":
                        kv = lines[i].strip()
                        i += 1
                        if not kv or kv.startswith(";"):
                            continue
                        if ":" not in kv:
                            err(f"{path.name}:{i}", f"event 필드 형식 오류: {kv}")
                            continue
                        k, v = kv.split(":", 1)
                        ev[k.strip()] = v.strip()
                    i += 1
                    for f in ("prompt", "situation", "need"):
                        if not ev.get(f):
                            err(where, f"event {ev['id']}에 {f} 없음")
                    if ev["id"] in events:
                        err(where, f"중복 event {ev['id']}")
                    events[ev["id"]] = {k: v for k, v in ev.items()}
                    ops.append({"op": "event", "id": ev["id"], "cases": {}, "end": None, **src})
                    pending_event = len(ops) - 1
                    continue
                if cmd == "case":
                    if parts not in (["high"], ["mid"], ["low"]):
                        err(where, f"case 인자 오류: {arg}")
                        continue
                    if stack and stack[-1]["kind"] == "case":
                        blk = stack[-1]
                        ops.append({"op": "goto", "to": None, **src})
                        blk["exits"].append(len(ops) - 1)
                    elif pending_event is not None:
                        blk = {"kind": "case", "event": pending_event, "exits": [], "src": where}
                        stack.append(blk)
                        pending_event = None
                    else:
                        err(where, "event 없이 case")
                        continue
                    ops[blk["event"]]["cases"][parts[0]] = len(ops)
                    continue
                if cmd == "endcase":
                    if not stack or stack[-1]["kind"] != "case":
                        err(where, "짝 없는 endcase")
                        continue
                    blk = stack.pop()
                    ev = ops[blk["event"]]
                    for t in ("high", "mid", "low"):
                        if t not in ev["cases"]:
                            err(blk["src"], f"event {ev['id']}에 case {t} 없음")
                    for e in blk["exits"]:
                        ops[e]["to"] = len(ops)
                    ev["end"] = len(ops)
                    continue
                if pending_event is not None:
                    err(where, f"event {ops[pending_event]['id']} 다음에 case가 와야 함")
                    pending_event = None
                if cmd == "if":
                    cond = " ".join(parts)
                    for c in re.split(r"\s*&&\s*", cond):
                        if not COND_RE.match(c.strip()):
                            err(where, f"조건 형식 오류: {cond}")
                    ops.append({"op": "if", "cond": cond, "else": None, **src})
                    stack.append({"kind": "if", "at": len(ops) - 1, "goto": None, "src": where})
                    continue
                if cmd == "else":
                    if not stack or stack[-1]["kind"] != "if" or stack[-1]["goto"] is not None:
                        err(where, "짝 없는 else")
                        continue
                    blk = stack[-1]
                    ops.append({"op": "goto", "to": None, **src})
                    blk["goto"] = len(ops) - 1
                    ops[blk["at"]]["else"] = len(ops)
                    continue
                if cmd == "endif":
                    if not stack or stack[-1]["kind"] != "if":
                        err(where, "짝 없는 endif")
                        continue
                    blk = stack.pop()
                    if blk["goto"] is None:
                        ops[blk["at"]]["else"] = len(ops)
                    else:
                        ops[blk["goto"]]["to"] = len(ops)
                    continue
                op = {"op": cmd, **src}
                if cmd == "chapter":
                    op["title"] = arg
                elif cmd in ("bg", "cg", "bgm", "sfx", "fx", "flag"):
                    if len(parts) != 1:
                        err(where, f"{cmd} 인자 오류: {arg}")
                    op["key"] = parts[0] if parts else ""
                elif cmd == "show":
                    if not parts:
                        err(where, "show 인자 없음")
                        continue
                    op.update(char=parts[0], expr=parts[1] if len(parts) > 1 else "neutral",
                              pos=parts[2] if len(parts) > 2 else "center")
                    if op["pos"] not in ("left", "center", "right"):
                        err(where, f"위치 오류: {op['pos']}")
                elif cmd == "hide":
                    op["char"] = parts[0] if parts else "all"
                elif cmd == "wait":
                    op["sec"] = float(parts[0]) if parts else 1.0
                elif cmd == "aff":
                    if len(parts) != 2 or parts[0] not in TARGETS - {"none"}:
                        err(where, f"aff 인자 오류: {arg}")
                        continue
                    op.update(char=parts[0], delta=int(parts[1]))
                elif cmd == "jump":
                    op["label"] = parts[0] if parts else ""
                elif cmd in ("ending", "end"):
                    pass
                else:
                    err(where, f"알 수 없는 명령 [{cmd}]")
                    continue
                ops.append(op)
                continue

            if pending_event is not None:
                err(where, f"event {ops[pending_event]['id']} 다음에 case가 와야 함")
                pending_event = None
            m = SAY_RE.match(line)
            if m and (m.group(1) in SPEAKERS or m.group(1) == "extra"):
                who, alias, text = m.group(1), m.group(2), m.group(3).strip()
                name = alias if who == "extra" else SPEAKERS[who]
                if who == "extra" and not alias:
                    err(where, "extra에는 [이름]이 필요")
                op = {"op": "say", "who": who, "name": name, "text": text, "src": where}
                rel = voice_rel(op)
                if rel and (VOICE_DIR.parent / rel).exists():
                    op["voice"] = rel
                ops.append(op)
                chars += len(text)
            else:
                ops.append({"op": "narr", "text": line, "src": where})
                chars += len(line)

    for blk in stack:
        err(blk["src"], f"닫히지 않은 {blk['kind']}")
    for idx, op in enumerate(ops):
        if op["op"] == "jump" and op["label"] not in labels:
            err(op["src"], f"없는 라벨 {op['label']}")
    for need in ("prologue", "end_true", "end_happy", "end_normal", "end_bad_ashes", "end_bad_blade"):
        if need not in labels:
            err("story", f"필수 라벨 {need} 없음")

    stats = {
        "files": [p.name for p in files], "ops": len(ops), "chars": chars,
        "events": len(events), "lines": sum(1 for o in ops if o["op"] in ("say", "narr")),
        "says": sum(1 for o in ops if o["op"] == "say"), "voiced": sum(1 for o in ops if o.get("voice")),
    }
    return {"ops": ops, "labels": labels, "events": events, "speakers": SPEAKERS, "stats": stats}, errors


def main():
    data, errors = compile_story()
    for e in errors:
        print("ERROR", e)
    print(json.dumps(data["stats"], ensure_ascii=False))
    if errors:
        sys.exit(1)
    if "--check" not in sys.argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print(f"→ {OUT} (assets: {len(write_asset_manifest())})")


if __name__ == "__main__":
    main()
