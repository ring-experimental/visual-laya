"""생성된 대사 음성 점검 (.venv-tts): Whisper로 받아 적어 원문과의 문자 오류율(CER)이 높은 줄을 찾는다.

  python tools/check_voices.py            # CER > 0.2 인 줄 목록 → logs/voice_check.json
다시 만들 줄은 tools/voice_manifest.json에서 해당 항목을 지우고 .\run.ps1 voice lines
"""

import json
import re
import sys
from pathlib import Path

import jiwer
import librosa
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from gen_voices import VOICE_DIR, collect_lines  # noqa: E402

THRESHOLD = 0.2


def norm(text):
    return re.sub(r"[^0-9A-Za-z가-힣]", "", text)


def main():
    from transformers import pipeline

    asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo",
                   torch_dtype=torch.float16, device="cuda:0")
    rows = []
    items = [it for its in collect_lines().values() for it in its]
    for n, it in enumerate(items, 1):
        wav = librosa.load(VOICE_DIR.parent / it["rel"], sr=16000)[0]
        hyp = asr(wav, generate_kwargs={"language": "korean", "task": "transcribe"})["text"]
        cer = jiwer.cer(norm(it["text"]), norm(hyp) or "∅")
        rows.append({**it, "hyp": hyp.strip(), "cer": round(cer, 3), "sec": round(len(wav) / 16000, 2)})
        if n % 100 == 0:
            print(f"[check] {n}/{len(items)}", flush=True)
    bad = sorted((r for r in rows if r["cer"] > THRESHOLD), key=lambda r: -r["cer"])
    (ROOT / "logs" / "voice_check.json").write_text(json.dumps(bad, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(r["cer"] <= 0.1 for r in rows)
    print(f"[check] {len(rows)}줄: CER≤10% {ok}줄, CER>{THRESHOLD:.0%} {len(bad)}줄 → logs/voice_check.json")
    for r in bad:
        print(f"  {r['cer']:.2f} {r['src']:18s} {r['text']}  →  {r['hyp']}")


if __name__ == "__main__":
    main()
