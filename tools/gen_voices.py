"""대사 음성 일괄 생성.

  1) design : Qwen3 VoiceDesign으로 인물별 목소리 후보를 만든다 (tools/voice_refs/<id>_<n>.wav, Windows .venv-tts)
  2) refs   : 고른 후보(voices.json pick) + 같은 목소리 대사 1줄 → 클론용 레퍼런스 약 10초
              (tools/voice_refs/clone/<id>.wav/.txt)
  3) lines  : WSL의 Higgs TTS 3가 레퍼런스를 클론하고 감정 토큰(tools/voice_emotion.py)을 붙여 낭독
              → game/assets/voice/<id>/<hash>.mp3, 끝나면 story.json 재컴파일(voice 필드 기록)

tools/voice_manifest.json에 줄마다 (엔진, 감정 토큰)을 기록해, 대본·감정 지정이 바뀐 줄만 다시 만든다.
WSL 환경 구성은 tools/higgs/setup_wsl.sh (최초 1회).

사용법 (.venv-tts):
  python tools/gen_voices.py                    # design·refs(없는 것만) → lines(바뀐 것만)
  python tools/gen_voices.py design --only haram --force   # 목소리 후보 다시 만들기
  python tools/gen_voices.py lines --only haram,yuri --limit 5
  python tools/gen_voices.py lines --force      # 전체 대사 재생성
  python tools/gen_voices.py lines --redo check --seed 2   # tools/check_voices.py가 찾은 줄만 다른 시드로
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))
from compile_story import OUT as STORY_JSON  # noqa: E402
from compile_story import compile_story, write_asset_manifest  # noqa: E402
from voice_map import VOICE_DIR, tts_text, voice_of, voice_rel  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
from voice_emotion import line_tags  # noqa: E402

CONFIG = ROOT / "tools" / "voices.json"
REF_DIR = ROOT / "tools" / "voice_refs"
CLONE_DIR = REF_DIR / "clone"
MANIFEST = ROOT / "tools" / "voice_manifest.json"
JOB = ROOT / "tools" / "higgs" / "job.json"
DESIGN_MODEL = ROOT / "models" / "Qwen3-TTS-12Hz-1.7B-VoiceDesign"
ENGINE = "higgs-tts-3-4b"
SEED = 1  # 비교 샘플에서 고른 "Higgs TTS 3 #1"
CANDIDATES = 3


def load_model(path):
    from qwen_tts import Qwen3TTSModel

    try:
        import flash_attn  # noqa: F401
        attn = "flash_attention_2"
    except ImportError:
        attn = "sdpa"
    return Qwen3TTSModel.from_pretrained(str(path), device_map="cuda:0", dtype=torch.bfloat16,
                                         attn_implementation=attn)


def free(model):
    del model
    torch.cuda.empty_cache()


def collect_lines():
    data, errors = compile_story()
    if errors:
        raise SystemExit("대본 컴파일 오류:\n" + "\n".join(errors))
    tags = line_tags(data["ops"])
    lines, seen = defaultdict(list), set()
    for op in data["ops"]:
        rel = voice_rel(op)
        if rel and rel not in seen:  # 같은 인물의 같은 대사는 파일 하나 공유
            seen.add(rel)
            lines[voice_of(op)].append({"rel": rel, "voice": voice_of(op), "text": tts_text(op["text"]),
                                        "src": op["src"], "tags": tags[op["src"]]})
    return lines


def polish(wav, sr):
    """앞뒤 무음 정리 + 음량 맞춤 (RMS −20 dBFS, 피크 −1 dBFS 이하)."""
    wav = np.asarray(wav, dtype=np.float32).flatten()
    loud = np.flatnonzero(np.abs(wav) > 0.01)
    if loud.size:
        pad = int(sr * 0.08)
        wav = wav[max(0, loud[0] - pad):loud[-1] + pad]
    rms = float(np.sqrt(np.mean(wav ** 2))) or 1e-6
    wav = wav * (10 ** (-20 / 20) / rms)
    peak = float(np.max(np.abs(wav))) or 1e-6
    if peak > 0.89:
        wav = wav * (0.89 / peak)
    return wav


def plausible(wav, sr, text):
    """폭주(끝없이 이어지는 생성)·빈 출력 감지. 한국어 낭독 ≈ 초당 5~8자."""
    sec = len(wav) / sr
    n = len(text)
    return 0.25 + n * 0.04 <= sec <= 2.5 + n * 0.3


def design(cfg, used, force):
    REF_DIR.mkdir(parents=True, exist_ok=True)
    todo = [vid for vid in used
            if force or not all((REF_DIR / f"{vid}_{i}.wav").exists() for i in range(CANDIDATES))]
    if not todo:
        print("[design] 레퍼런스가 모두 있습니다 (다시 만들려면 --force)")
        return
    print(f"[design] VoiceDesign 로딩… ({len(todo)}명 × 후보 {CANDIDATES})")
    model = load_model(DESIGN_MODEL)
    for vid in todo:
        v = cfg[vid]
        for i in range(CANDIDATES):
            for attempt in range(3):
                torch.manual_seed(1000 * i + attempt)
                wavs, sr = model.generate_voice_design(text=v["ref_text"], language="Korean",
                                                       instruct=v["instruct"], max_new_tokens=400)
                if plausible(wavs[0], sr, v["ref_text"]):
                    break
            sf.write(REF_DIR / f"{vid}_{i}.wav", polish(wavs[0], sr), sr)
        print(f"[design] {vid}: {REF_DIR.name}/{vid}_0..{CANDIDATES - 1}.wav")
    free(model)


def build_refs(cfg, lines, force):
    """design 후보(pick) + 같은 목소리의 평서문 대사 1줄 → 클론용 레퍼런스(약 10초).
    대사 1줄은 기존 생성 음성에서 가져오므로, 없으면 후보만 쓴다."""
    CLONE_DIR.mkdir(parents=True, exist_ok=True)
    for vid, items in sorted(lines.items()):
        if not force and (CLONE_DIR / f"{vid}.wav").exists():
            continue
        v = cfg[vid]
        wav, sr = sf.read(REF_DIR / f"{vid}_{v.get('pick', 0)}.wav", dtype="float32")
        parts, texts = [wav], [v["ref_text"]]
        for it in items:
            mp3 = VOICE_DIR.parent / it["rel"]
            if 12 <= len(it["text"]) <= 40 and "…" not in it["text"] and "!" not in it["text"] and mp3.exists():
                w, wsr = sf.read(mp3, dtype="float32")
                if wsr == sr:
                    parts += [np.zeros(int(sr * 0.4), np.float32), w]
                    texts.append(it["text"])
                    break
        sf.write(CLONE_DIR / f"{vid}.wav", np.concatenate(parts), sr)
        (CLONE_DIR / f"{vid}.txt").write_text(" ".join(texts), encoding="utf-8")
        print(f"[refs] {vid}: {sum(map(len, parts)) / sr:.1f}s")


def gen_lines(lines, args):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    if args.redo:  # 지정한 줄(파일:줄 쉼표 목록, 또는 check = logs/voice_check.json)만 다른 시드로 다시
        srcs = ({r["src"] for r in json.loads((ROOT / "logs" / "voice_check.json").read_text(encoding="utf-8"))}
                if args.redo == "check" else set(args.redo.split(",")))
        lines = {vid: [dict(it, seed=args.seed) for it in its if it["src"] in srcs] for vid, its in lines.items()}
        args.force = True
    items = []
    for vid, its in lines.items():
        its = [it for it in its if args.force or not (VOICE_DIR.parent / it["rel"]).exists()
               or manifest.get(it["rel"]) != {"engine": ENGINE, "tags": it["tags"]}]
        items += its[:args.limit] if args.limit else its
    if not items:
        print("[lines] 생성할 대사가 없습니다 (전부 최신)")
        return
    if args.force:  # 작업자는 manifest가 같으면 건너뛰므로, 강제 재생성 대상은 기록에서 지운다
        for it in items:
            manifest.pop(it["rel"], None)
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=0), encoding="utf-8")
    refs = {vid: {"wav": (CLONE_DIR / f"{vid}.wav").relative_to(ROOT).as_posix(),
                  "text": (CLONE_DIR / f"{vid}.txt").read_text(encoding="utf-8")}
            for vid in {it["voice"] for it in items}}
    JOB.write_text(json.dumps({"engine": ENGINE, "seed": SEED, "refs": refs, "items": items},
                              ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"[lines] Higgs TTS 3 (WSL)로 {len(items)}줄 생성")
    run_sh = f"/mnt/{ROOT.drive[0].lower()}/{ROOT.relative_to(ROOT.anchor).as_posix()}/tools/higgs/run.sh"
    for attempt in range(1, 11):  # WSL이 가끔 통째로 죽는다 → 배포판만 재시작하고 이어서 생성
        subprocess.run(["wsl", "--terminate", "Ubuntu"], capture_output=True)
        r = subprocess.run(["wsl", "-d", "Ubuntu", "--", "bash", run_sh], capture_output=True)
        print(r.stdout.decode("utf-8", "replace").strip())
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
        left = sum(manifest.get(it["rel"]) != {"engine": ENGINE, "tags": it["tags"]} for it in items)
        if not left:
            return
        print(f"[lines] {left}줄 남음 — WSL 재시작 후 이어서 ({attempt}/10)")
    raise SystemExit("[lines] WSL에서 생성을 마치지 못했습니다. ~/tts/logs/voice_higgs.log 확인")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", nargs="?", default="all", choices=["all", "design", "refs", "lines"])
    ap.add_argument("--only", help="보이스 id 쉼표 목록 (예: haram,yuri)")
    ap.add_argument("--limit", type=int, default=0, help="보이스별 최대 생성 줄 수 (시험용)")
    ap.add_argument("--force", action="store_true", help="이미 있는 파일도 다시 생성")
    ap.add_argument("--redo", help="lines: 이 줄들만 다시 (파일:줄 쉼표 목록, 또는 check)")
    ap.add_argument("--seed", type=int, default=SEED, help="--redo와 함께 쓸 시드")
    args = ap.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))["voices"]
    lines = collect_lines()
    if args.only:
        keep = set(args.only.split(","))
        lines = {k: v for k, v in lines.items() if k in keep}
    missing = set(lines) - set(cfg)
    if missing:
        raise SystemExit(f"voices.json에 정의되지 않은 보이스: {sorted(missing)}")
    print("[plan] " + ", ".join(f"{k}:{len(v)}" for k, v in sorted(lines.items(), key=lambda x: -len(x[1]))))

    if args.stage in ("all", "design"):
        design(cfg, sorted(lines), args.force and args.stage == "design")
    if args.stage in ("all", "refs"):
        build_refs(cfg, lines, args.force and args.stage == "refs")
    if args.stage in ("all", "lines"):
        gen_lines(lines, args)
        data, _ = compile_story()
        STORY_JSON.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        write_asset_manifest()
        print(f"[story] voice {data['stats'].get('voiced', 0)}/{data['stats']['says']}줄 연결 → {STORY_JSON}")


if __name__ == "__main__":
    main()
