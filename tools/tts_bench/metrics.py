"""TTS 비교 샘플 객관 지표 (.venv-tts에서 실행) → samples/tts_compare/metrics.json

- CER  : Whisper large-v3-turbo로 받아 적은 결과와 원문의 문자 오류율 (공백·문장부호 제외, 낮을수록 정확)
- SIM  : WavLM-SV 화자 임베딩 코사인 유사도, 레퍼런스(refs/<voice>.wav) 대비 (높을수록 톤 유지)
- EMO  : emotion2vec+ large 감정 분류. emo = 1 − P(neutral) (높을수록 감정이 실림), top = 최상위 감정
"""

import json
import re
import sys
from pathlib import Path

import jiwer
import librosa
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, SAMPLES  # noqa: E402

SYSTEMS = {"A_qwen_current": "A_qwen_current.wav", "B_fish_s2pro": "B_fish_s2pro_{t}.wav",
           "C_higgs_v3": "C_higgs_v3_{t}.wav", "D_qwen_design": "D_qwen_design.wav",
           "E_zonos2": "E_zonos2_{t}.wav"}
EMO_EN = {"生气": "angry", "厌恶": "disgusted", "恐惧": "fearful", "开心": "happy", "中立": "neutral",
          "其他": "other", "难过": "sad", "吃惊": "surprised", "<unk>": "unk"}


def files(sample):
    d = OUT / sample["id"]
    for sys_id, pat in SYSTEMS.items():
        for t in (1, 2):
            p = d / pat.format(t=t)
            if p.exists():
                yield sys_id, p
            if "{t}" not in pat:
                break


def norm(text):
    return re.sub(r"[^0-9A-Za-z가-힣]", "", text)


def main():
    from funasr import AutoModel
    from transformers import AutoFeatureExtractor, WavLMForXVector, pipeline

    asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo",
                   torch_dtype=torch.float16, device="cuda:0")
    fe = AutoFeatureExtractor.from_pretrained("microsoft/wavlm-base-plus-sv")
    sv = WavLMForXVector.from_pretrained("microsoft/wavlm-base-plus-sv").cuda().eval()
    emo = AutoModel(model="iic/emotion2vec_plus_large", hub="hf", disable_update=True)

    def embed(wav):
        inp = fe(wav, sampling_rate=16000, return_tensors="pt").to("cuda")
        with torch.no_grad():
            e = sv(**inp).embeddings[0]
        return torch.nn.functional.normalize(e, dim=-1)

    refs, rows = {}, []
    for s in SAMPLES:
        if s["voice"] not in refs:
            refs[s["voice"]] = embed(librosa.load(OUT / "refs" / f"{s['voice']}.wav", sr=16000)[0])
        for sys_id, path in files(s):
            wav = librosa.load(path, sr=16000)[0]
            hyp = asr(wav.copy(), generate_kwargs={"language": "korean", "task": "transcribe"})["text"]
            cer = jiwer.cer(norm(s["text"]), norm(hyp) or "∅")
            sim = float(embed(wav) @ refs[s["voice"]])
            r = emo.generate(wav, granularity="utterance", extract_embedding=False)[0]
            probs = {EMO_EN.get(k.split("/")[0], k.split("/")[-1]): float(v) for k, v in zip(r["labels"], r["scores"])}
            top = max(probs, key=probs.get)
            rows.append({"id": s["id"], "system": sys_id, "file": path.name, "hyp": hyp, "cer": round(cer, 3),
                         "sim": round(sim, 3), "emo": round(1 - probs.get("neutral", 0), 3), "top": top})
            print(f"{s['id']:20s} {path.name:22s} cer={cer:.2f} sim={sim:.3f} emo={rows[-1]['emo']:.2f} {top}", flush=True)

    summary = {}
    for sys_id in SYSTEMS:
        rs = [r for r in rows if r["system"] == sys_id]
        summary[sys_id] = {k: round(float(np.mean([r[k] for r in rs])), 3) for k in ("cer", "sim", "emo")}
        summary[sys_id]["n"] = len(rs)
    (OUT / "metrics.json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
