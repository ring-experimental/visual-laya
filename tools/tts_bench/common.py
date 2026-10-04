"""비교 스크립트 공용: 샘플 목록, 레퍼런스, 출력 경로, 음량 정리 (numpy/soundfile만 사용)."""

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "samples" / "tts_compare"
SAMPLES = json.loads((Path(__file__).parent / "samples.json").read_text(encoding="utf-8"))["lines"]
TAKES = 2


def ref(voice):
    return OUT / "refs" / f"{voice}.wav", (OUT / "refs" / f"{voice}.txt").read_text(encoding="utf-8")


def tts_text(text):
    return text.replace("—", ", ").strip(" ,")


def polish(wav, sr):
    """앞뒤 무음 정리 + RMS −20 dBFS, 피크 −1 dBFS (gen_voices.polish와 동일)."""
    wav = np.asarray(wav, dtype=np.float32).flatten()
    loud = np.flatnonzero(np.abs(wav) > 0.01)
    if loud.size:
        pad = int(sr * 0.08)
        wav = wav[max(0, loud[0] - pad):loud[-1] + pad]
    wav = wav * (0.1 / (float(np.sqrt(np.mean(wav ** 2))) or 1e-6))
    peak = float(np.max(np.abs(wav))) or 1e-6
    return wav * (0.89 / peak) if peak > 0.89 else wav
