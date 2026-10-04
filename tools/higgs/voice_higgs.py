"""Higgs TTS 3로 대사 음성 생성 — WSL(~/tts/higgs venv)에서 실행. tools/gen_voices.py lines가 호출한다.

입력 tools/higgs/job.json (gen_voices가 작성):
  {"engine": ..., "seed": 1, "refs": {voice: {"wav": 레포 상대경로, "text": 전사}},
   "items": [{"rel": "voice/<id>/<hash>.mp3", "voice": id, "text": 낭독문, "tags": 감정 토큰, "seed"?: 줄별 시드}]}
출력 game/assets/<rel> (mp3) + tools/voice_manifest.json에 줄마다 기록 → 중간에 죽어도 이어서 생성.
"""

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("VLLM_USE_DEEP_GEMM", "0")
os.environ.setdefault("VLLM_MOE_USE_DEEP_GEMM", "0")
os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")  # FlashInfer 샘플러는 nvcc JIT 필요

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import soundfile as sf  # noqa: E402
import torch  # noqa: E402

from gen_voices import MANIFEST, plausible, polish  # noqa: E402

MODEL = str(Path.home() / "tts" / "models" / "higgs-tts-3-4b")
SR = 24_000


def main():
    from transformers import AutoTokenizer
    from vllm import SamplingParams
    from vllm_omni import Omni
    from vllm_omni.model_executor.models.higgs_audio_v3.higgs_audio_v3_tokenizer import (
        HiggsAudioV3TokenizerAdapter, apply_delay_pattern, encode_reference_audio)

    job = json.loads((HERE / "job.json").read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    items = [it for it in job["items"] if manifest.get(it["rel"]) != {"engine": job["engine"], "tags": it["tags"]}]
    print(f"[higgs] {len(items)}/{len(job['items'])}줄 남음", flush=True)
    if not items:
        return

    engine = Omni(model=MODEL, deploy_config=str(HERE / "higgs_16gb.yaml"), trust_remote_code=True)
    adapter = HiggsAudioV3TokenizerAdapter(AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True))
    codes = {}
    t0 = time.time()
    for n, it in enumerate(items, 1):
        if it["voice"] not in codes:
            ref = job["refs"][it["voice"]]
            wav, sr = sf.read(ROOT / ref["wav"], always_2d=False)
            codes[it["voice"]] = (apply_delay_pattern(encode_reference_audio(wav, int(sr))), ref["text"])
        ref_codes, ref_text = codes[it["voice"]]
        ids = adapter.build_prompt(it["tags"] + it["text"], num_ref_tokens=int(ref_codes.shape[0]),
                                   reference_text=ref_text)
        ids, pos = adapter.prepare_prompt_for_engine(ids)
        prompt = {"prompt_token_ids": ids, "additional_information": {
            "audio_input_ids": ref_codes.to(torch.long),
            "audio_input_ids_mask": torch.ones(ref_codes.shape[0], dtype=torch.bool),
            "audio_placeholder_positions": pos}}
        for attempt in range(3):  # 폭주·빈 출력이면 시드를 바꿔 재시도
            params = [SamplingParams(temperature=1.0, top_p=0.95, top_k=50, max_tokens=2048,
                                     seed=it.get("seed", job["seed"]) + 100 * attempt),
                      SamplingParams(temperature=0.0, top_k=-1, max_tokens=16384, seed=42)]
            mm = engine.generate([prompt], sampling_params_list=params)[0].outputs[0].multimodal_output
            audio = mm.get("model_outputs", mm.get("audio"))
            if isinstance(audio, list):
                audio = torch.cat([torch.as_tensor(a).float().cpu().reshape(-1) for a in audio if a is not None])
            wav = torch.as_tensor(audio).float().cpu().reshape(-1).numpy()
            if len(wav) and plausible(wav, SR, it["text"]):
                break
        else:
            print(f"[higgs] 길이 이상(재시도 3회): {it['rel']} {it['text']}", flush=True)
        out = ROOT / "game" / "assets" / it["rel"]
        out.parent.mkdir(parents=True, exist_ok=True)
        sf.write(out, polish(wav, SR), SR, format="MP3")
        manifest[it["rel"]] = {"engine": job["engine"], "tags": it["tags"]}
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=0), encoding="utf-8")
        if n % 10 == 0 or n == len(items):
            rate = n / (time.time() - t0)
            print(f"[higgs] {n}/{len(items)} ({rate:.2f}줄/s, 남은 시간 ~{(len(items) - n) / rate / 60:.0f}분)", flush=True)


if __name__ == "__main__":
    main()
