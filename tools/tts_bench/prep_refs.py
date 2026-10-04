"""TTS 비교 준비 (.venv-tts에서 실행).  --refs-only: 레퍼런스만 다시 만들기

게임 음성 파일을 지운 뒤에도 다시 만들 수 있도록, 1차 파이프라인(VoiceDesign → Base 클론)을 여기서 재현한다.
목소리 후보는 tools/gen_voices.py design이 만든 tools/voice_refs/<voice>_<pick>.wav (없으면 먼저 만든다).

- samples/tts_compare/refs/<voice>.wav/.txt : 클론용 레퍼런스(약 10~12초)
    = 후보 + Base 클론으로 만든 같은 목소리 평서문 대사 1줄
      (Fish S2 Pro는 16GB GPU에서 15초 넘는 레퍼런스 인코딩 시 OOM)
- samples/tts_compare/<id>/A_qwen_current.wav : 1차 방식 (Qwen3 Base 클론, 감정 지시 없음)
- samples/tts_compare/<id>/D_qwen_design.wav  : Qwen3 VoiceDesign에 줄마다 감정 지시를 넣은 버전
"""

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "tools"))
from compile_story import compile_story  # noqa: E402
from gen_voices import DESIGN_MODEL, REF_DIR, design, free, load_model, plausible, polish  # noqa: E402
from voice_map import tts_text, voice_of  # noqa: E402

OUT = ROOT / "samples" / "tts_compare"
BASE_MODEL = ROOT / "models" / "Qwen3-TTS-12Hz-1.7B-Base"
SAMPLES = json.loads((Path(__file__).parent / "samples.json").read_text(encoding="utf-8"))["lines"]
VOICES = json.loads((ROOT / "tools" / "voices.json").read_text(encoding="utf-8"))["voices"]


def clone(model, text, ref_wav, ref_text, seed=0):
    for attempt in range(3):
        torch.manual_seed(seed + attempt)
        wavs, sr = model.generate_voice_clone(text=text, language="Korean", ref_audio=ref_wav,
                                              ref_text=ref_text, max_new_tokens=600)
        if plausible(wavs[0], sr, text):
            break
    return polish(wavs[0], sr), sr


def main():
    ops = [o for o in compile_story()[0]["ops"] if o["op"] == "say"]
    by_src = {o["src"]: o for o in ops}
    sample_srcs = {s["src"] for s in SAMPLES}
    voices = sorted({s["voice"] for s in SAMPLES})
    (OUT / "refs").mkdir(parents=True, exist_ok=True)
    design(VOICES, voices, False)  # 후보가 없을 때만 생성

    model = load_model(BASE_MODEL)
    for vid in voices:
        v = VOICES[vid]
        cand = REF_DIR / f"{vid}_{v.get('pick', 0)}.wav"
        wav, sr = sf.read(cand, dtype="float32")
        parts, texts = [wav], [v["ref_text"]]
        extra = [o for o in ops if voice_of(o) == vid and o["src"] not in sample_srcs
                 and 12 <= len(o["text"]) <= 40 and "…" not in o["text"] and "!" not in o["text"]]
        for o in extra[:1]:
            w, wsr = clone(model, tts_text(o["text"]), str(cand), v["ref_text"])
            assert wsr == sr, (wsr, sr)
            parts += [np.zeros(int(sr * 0.4), np.float32), w]
            texts.append(tts_text(o["text"]))
        ref = np.concatenate(parts)
        sf.write(OUT / "refs" / f"{vid}.wav", ref, sr)
        (OUT / "refs" / f"{vid}.txt").write_text(" ".join(texts), encoding="utf-8")
        print(f"[ref] {vid}: {len(ref) / sr:.1f}s")
    if "--refs-only" in sys.argv:
        return

    for s in SAMPLES:  # A: 1차 게임 음성과 같은 방식 — 레퍼런스 클론, 감정 지시 없음
        d = OUT / s["id"]
        d.mkdir(exist_ok=True)
        assert by_src[s["src"]]["text"] == s["text"], (s["src"], by_src[s["src"]]["text"])
        ref_text = (OUT / "refs" / f"{s['voice']}.txt").read_text(encoding="utf-8")
        w, sr = clone(model, tts_text(s["text"]), str(OUT / "refs" / f"{s['voice']}.wav"), ref_text)
        sf.write(d / "A_qwen_current.wav", w, sr)
        print(f"[qwen-base] {s['id']}")
    free(model)

    model = load_model(DESIGN_MODEL)
    for s in SAMPLES:
        instruct = VOICES[s["voice"]]["instruct"] + " " + s["qwen"]
        wavs, sr = model.generate_voice_design(text=tts_text(s["text"]), language="Korean",
                                               instruct=instruct, max_new_tokens=400)
        sf.write(OUT / s["id"] / "D_qwen_design.wav", polish(wavs[0], sr), sr)
        print(f"[qwen-design] {s['id']}")
    free(model)


if __name__ == "__main__":
    main()
