"""Higgs TTS 3 샘플 (WSL, ~/tts/higgs). vLLM-Omni 오프라인 엔진, 레퍼런스 클론 + 제어 토큰."""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("VLLM_USE_DEEP_GEMM", "0")
os.environ.setdefault("VLLM_MOE_USE_DEEP_GEMM", "0")
os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")  # FlashInfer 샘플러는 nvcc JIT 필요
sys.path.insert(0, str(Path(__file__).parent))

import soundfile as sf  # noqa: E402
import torch  # noqa: E402

from common import OUT, SAMPLES, TAKES, polish, ref, tts_text  # noqa: E402

MODEL = str(Path.home() / "tts" / "models" / "higgs-tts-3-4b")
SR = 24_000


def main():
    from transformers import AutoTokenizer
    from vllm import SamplingParams
    from vllm_omni import Omni
    from vllm_omni.model_executor.models.higgs_audio_v3.higgs_audio_v3_tokenizer import (
        HiggsAudioV3TokenizerAdapter, apply_delay_pattern, encode_reference_audio)

    engine = Omni(model=MODEL, deploy_config=str(Path(__file__).parents[1] / "higgs" / "higgs_16gb.yaml"), trust_remote_code=True)
    adapter = HiggsAudioV3TokenizerAdapter(AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True))

    codes = {}
    for s in SAMPLES:
        if s["voice"] not in codes:
            path, text = ref(s["voice"])
            wav, sr = sf.read(path, always_2d=False)
            codes[s["voice"]] = (apply_delay_pattern(encode_reference_audio(wav, int(sr))), text)
        ref_codes, ref_text = codes[s["voice"]]
        for take in range(1, TAKES + 1):
            out = OUT / s["id"] / f"C_higgs_v3_{take}.wav"
            if out.exists():
                continue
            t0 = time.time()
            # 배포 설정의 기본 시드(42) 고정이면 테이크가 같아진다 → 테이크마다 시드 지정
            params = [SamplingParams(temperature=1.0, top_p=0.95, top_k=50, max_tokens=2048, seed=take),
                      SamplingParams(temperature=0.0, top_k=-1, max_tokens=16384, seed=42)]
            ids = adapter.build_prompt(s["higgs"] + tts_text(s["text"]),
                                       num_ref_tokens=int(ref_codes.shape[0]), reference_text=ref_text)
            ids, pos = adapter.prepare_prompt_for_engine(ids)
            prompt = {"prompt_token_ids": ids, "additional_information": {
                "audio_input_ids": ref_codes.to(torch.long),
                "audio_input_ids_mask": torch.ones(ref_codes.shape[0], dtype=torch.bool),
                "audio_placeholder_positions": pos}}
            mm = engine.generate([prompt], sampling_params_list=params)[0].outputs[0].multimodal_output
            audio = mm.get("model_outputs", mm.get("audio"))
            if isinstance(audio, list):
                audio = torch.cat([torch.as_tensor(a).float().cpu().reshape(-1) for a in audio if a is not None])
            wav = torch.as_tensor(audio).float().cpu().reshape(-1).numpy()
            sf.write(out, polish(wav, SR), SR)
            print(f"[higgs] {s['id']} take{take} {len(wav) / SR:.1f}s ({time.time() - t0:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
