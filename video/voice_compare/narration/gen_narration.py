"""나레이션 낭독: Higgs TTS 3 (WSL ~/tts/higgs venv). ref_<PICK>.wav를 클론해 줄마다 2테이크 → takes/<id>_<t>.wav
테이크 선택은 pick_takes.py(Windows, Whisper)."""

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("VLLM_USE_DEEP_GEMM", "0")
os.environ.setdefault("VLLM_MOE_USE_DEEP_GEMM", "0")
os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")  # FlashInfer 샘플러는 nvcc JIT 필요

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools" / "tts_bench"))

import soundfile as sf  # noqa: E402
import torch  # noqa: E402

from common import polish  # noqa: E402

MODEL = str(Path.home() / "tts" / "models" / "higgs-tts-3-4b")
SR = 24_000
PICK = 0
TAKES = 2


def main():
    from transformers import AutoTokenizer
    from vllm import SamplingParams
    from vllm_omni import Omni
    from vllm_omni.model_executor.models.higgs_audio_v3.higgs_audio_v3_tokenizer import (
        HiggsAudioV3TokenizerAdapter, apply_delay_pattern, encode_reference_audio)

    cfg = json.loads((HERE / "narration.json").read_text(encoding="utf-8"))
    (HERE / "takes").mkdir(exist_ok=True)
    engine = Omni(model=MODEL, deploy_config=str(ROOT / "tools" / "higgs" / "higgs_16gb.yaml"), trust_remote_code=True)
    adapter = HiggsAudioV3TokenizerAdapter(AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True))
    wav, sr = sf.read(HERE / f"ref_{PICK}.wav", always_2d=False)
    ref_codes = apply_delay_pattern(encode_reference_audio(wav, int(sr)))

    for line in cfg["lines"]:
        for take in range(1, TAKES + 1):
            out = HERE / "takes" / f"{line['id']}_{take}.wav"
            if out.exists():
                continue
            t0 = time.time()
            params = [SamplingParams(temperature=1.0, top_p=0.95, top_k=50, max_tokens=2048, seed=take),
                      SamplingParams(temperature=0.0, top_k=-1, max_tokens=16384, seed=42)]
            ids = adapter.build_prompt(line["text"], num_ref_tokens=int(ref_codes.shape[0]),
                                       reference_text=cfg["voice"]["ref_text"])
            ids, pos = adapter.prepare_prompt_for_engine(ids)
            prompt = {"prompt_token_ids": ids, "additional_information": {
                "audio_input_ids": ref_codes.to(torch.long),
                "audio_input_ids_mask": torch.ones(ref_codes.shape[0], dtype=torch.bool),
                "audio_placeholder_positions": pos}}
            mm = engine.generate([prompt], sampling_params_list=params)[0].outputs[0].multimodal_output
            audio = mm.get("model_outputs", mm.get("audio"))
            if isinstance(audio, list):
                audio = torch.cat([torch.as_tensor(a).float().cpu().reshape(-1) for a in audio if a is not None])
            w = torch.as_tensor(audio).float().cpu().reshape(-1).numpy()
            sf.write(out, polish(w, SR), SR)
            print(f"[narr] {line['id']} take{take} {len(w) / SR:.1f}s ({time.time() - t0:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
