"""게임 서버: 정적 게임 파일 + Laya 판정 API.

실행: .venv\\Scripts\\python.exe server\\app.py  (기본 http://127.0.0.1:8765)
"""

import argparse
import json
import sys
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compile_story import OUT as STORY_JSON  # noqa: E402
from compile_story import compile_story, write_asset_manifest  # noqa: E402
from judge import Judge  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "logs" / "judgments.jsonl"

app = FastAPI(title="재의 백작 — Laya VN server")
state = {"judge": None, "events": {}}
log_lock = threading.Lock()


class JudgeRequest(BaseModel):
    event_id: str
    text: str = Field(min_length=1, max_length=300)


def load_story():
    data, errors = compile_story()
    if errors:
        for e in errors:
            print("[story] ERROR", e)
        if not STORY_JSON.exists():
            raise SystemExit("story 컴파일 실패")
        print("[story] 오류가 있어 기존 story.json을 사용합니다")
        data = json.loads(STORY_JSON.read_text(encoding="utf-8"))
    else:
        STORY_JSON.parent.mkdir(parents=True, exist_ok=True)
        STORY_JSON.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    state["events"] = data["events"]
    print(f"[story] {data['stats']}  assets={len(write_asset_manifest())}")


@app.get("/api/health")
def health():
    judge = state["judge"]
    return {"ok": True, "model": judge.model_name if judge else None,
            "error": judge.error if judge else None, "events": len(state["events"])}


@app.post("/api/judge")
def judge(req: JudgeRequest):
    event = state["events"].get(req.event_id)
    if event is None:
        raise HTTPException(404, f"unknown event {req.event_id}")
    result = state["judge"].judge(event, req.text)
    with log_lock:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.time(), "event": req.event_id, "text": req.text, **result},
                               ensure_ascii=False) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--device", default=None, help="cuda / cpu (기본: 자동)")
    args = parser.parse_args()

    load_story()
    print("[judge] Laya 로딩 중…")
    state["judge"] = Judge(device=args.device)
    print(f"[judge] model = {state['judge'].model_name}" + (f" ({state['judge'].error})" if state['judge'].error else ""))
    app.mount("/", StaticFiles(directory=ROOT / "game", html=True), name="game")

    import uvicorn

    print(f"▶ http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
