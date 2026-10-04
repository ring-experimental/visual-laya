"""나레이션 테이크 선택 (.venv-tts): Whisper CER이 낮은 테이크, 같으면 더 짧은(덜 늘어진) 테이크 → ../assets/narration/<id>.wav"""

import json
import re
import shutil
from pathlib import Path

import jiwer
import librosa
import torch
from transformers import pipeline

HERE = Path(__file__).resolve().parent
DST = HERE.parent / "assets" / "narration"
norm = lambda t: re.sub(r"[^0-9A-Za-z가-힣]", "", t)  # noqa: E731

asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo",
               torch_dtype=torch.float16, device="cuda:0")
DST.mkdir(parents=True, exist_ok=True)
report = []
for line in json.loads((HERE / "narration.json").read_text(encoding="utf-8"))["lines"]:
    cands = []
    for p in sorted((HERE / "takes").glob(f"{line['id']}_*.wav")):
        w, _ = librosa.load(p, sr=16000)
        hyp = asr(w, generate_kwargs={"language": "korean"})["text"].strip()
        cands.append((round(jiwer.cer(norm(line["text"]), norm(hyp) or "x"), 3), len(w) / 16000, p.name, hyp))
    cer, dur, name, hyp = min(cands)
    shutil.copy(HERE / "takes" / name, DST / f"{line['id']}.wav")
    report.append({"id": line["id"], "take": name, "cer": cer, "dur": round(dur, 2), "hyp": hyp})
    print(f"{line['id']:3} {name:9} CER {cer * 100:3.0f}% {dur:4.1f}s  {hyp}")
(HERE / "picks.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
