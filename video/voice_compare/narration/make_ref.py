"""나레이터 레퍼런스 목소리 (.venv-tts, Windows): Qwen3 VoiceDesign 후보 3개 → ref_<n>.wav (pick은 gen_narration.py에서)."""

import json
import sys
from pathlib import Path

import soundfile as sf
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from gen_voices import DESIGN_MODEL, free, load_model, plausible, polish  # noqa: E402

cfg = json.loads((HERE / "narration.json").read_text(encoding="utf-8"))["voice"]
model = load_model(DESIGN_MODEL)
for i in range(3):
    for attempt in range(3):
        torch.manual_seed(1000 * i + attempt)
        wavs, sr = model.generate_voice_design(text=cfg["ref_text"], language="Korean",
                                               instruct=cfg["instruct"], max_new_tokens=500)
        if plausible(wavs[0], sr, cfg["ref_text"]):
            break
    sf.write(HERE / f"ref_{i}.wav", polish(wavs[0], sr), sr)
    print(f"[ref] ref_{i}.wav {len(wavs[0]) / sr:.1f}s")
free(model)
