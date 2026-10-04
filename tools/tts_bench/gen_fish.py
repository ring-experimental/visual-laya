"""Fish Audio S2 Pro 샘플 (WSL, ~/tts/fish-speech/.venv). 레퍼런스 클론 + 인라인 감정 태그."""

import os
import sys
import time
from pathlib import Path

FISH = Path.home() / "tts" / "fish-speech"
os.chdir(FISH)
sys.path.insert(0, str(FISH))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["EINX_FILTER_TRACEBACK"] = "false"
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import soundfile as sf  # noqa: E402
import torch  # noqa: E402

from common import OUT, SAMPLES, TAKES, polish, ref, tts_text  # noqa: E402
from fish_speech.inference_engine import TTSInferenceEngine  # noqa: E402
from fish_speech.models.dac.inference import load_model as load_decoder  # noqa: E402
from fish_speech.models.text2semantic.inference import launch_thread_safe_queue  # noqa: E402
from fish_speech.utils.schema import ServeReferenceAudio, ServeTTSRequest  # noqa: E402

import fish_speech.models.text2semantic.llama as llama  # noqa: E402

# 16GB를 꽉 채우면 WSL GPU 드라이버가 VM째 죽는다 → 그 전에 PyTorch OOM으로 끊기게
torch.cuda.set_per_process_memory_fraction(0.9)

CKPT = Path.home() / "tts" / "models" / "s2-pro"

# 원본은 CPU에서 fp32(20GB)로 모델을 만든 뒤 가중치를 올려 WSL RAM(15GB)을 넘는다.
# 골격을 GPU에 bf16으로 만들면 RAM에는 가중치(bf16 10GB)만 올라간다 (load_state_dict(assign=True)).
_from_pretrained = llama.BaseTransformer.from_pretrained


def _from_pretrained_gpu(*a, **k):
    k["max_length"] = 4096  # 기본 32768은 KV 캐시만 ~5GB → 16GB GPU에서 넘침. 대사+레퍼런스는 1천 토큰 남짓
    torch.set_default_dtype(torch.bfloat16)
    try:
        with torch.device("cuda"):
            return _from_pretrained(*a, **k)
    finally:
        torch.set_default_dtype(torch.float32)


llama.BaseTransformer.from_pretrained = staticmethod(_from_pretrained_gpu)
llama.DualARTransformer.from_pretrained = staticmethod(_from_pretrained_gpu)
queue = launch_thread_safe_queue(checkpoint_path=CKPT, device="cuda", precision=torch.bfloat16, compile=False)
# 코덱(1.9GB)은 CPU에서: GPU에는 LLM만 올려 16GB 안에서 레퍼런스 인코딩 OOM을 피한다
decoder = load_decoder(config_name="modded_dac_vq", checkpoint_path=CKPT / "codec.pth", device="cpu")
from fish_speech.inference_engine.vq_manager import VQManager  # noqa: E402

# 엔진은 코덱 장치(CPU)를 LLM 요청에도 그대로 쓴다 → LLM 쪽은 GPU, 디코딩 입력은 CPU로 맞춘다
_encode_reference, _decode = VQManager.encode_reference, VQManager.decode_vq_tokens
VQManager.encode_reference = lambda self, *a, **k: (lambda t: None if t is None else t.to("cuda"))(
    _encode_reference(self, *a, **k))
VQManager.decode_vq_tokens = lambda self, codes: _decode(self, codes=codes.to("cpu"))


class GpuQueue:
    def __init__(self, q):
        self.q = q

    def put(self, item):
        item.request["device"] = torch.device("cuda")
        self.q.put(item)


queue = GpuQueue(queue)
engine = TTSInferenceEngine(llama_queue=queue, decoder_model=decoder, compile=False, precision=torch.bfloat16)

print(f"[fish] loaded: {torch.cuda.memory_allocated() / 2**30:.1f}GB allocated", flush=True)
refs = {}
for s in SAMPLES:
    if s["voice"] not in refs:
        path, text = ref(s["voice"])
        refs[s["voice"]] = ServeReferenceAudio(audio=path.read_bytes(), text=text)
    for take in range(1, TAKES + 1):
        out = OUT / s["id"] / f"B_fish_s2pro_{take}.wav"
        if out.exists():
            continue
        torch.cuda.empty_cache()
        t0 = time.time()
        req = ServeTTSRequest(text=f"{s['fish']} {tts_text(s['text'])}", references=[refs[s["voice"]]],
                              seed=take, max_new_tokens=1024, chunk_length=200, top_p=0.8,
                              repetition_penalty=1.1, temperature=0.8, format="wav", normalize=False)
        final = None
        for r in engine.inference(req):
            if r.code == "error":
                raise r.error
            if r.code == "final":
                final = r.audio
        sr, wav = final
        sf.write(out, polish(wav, sr), sr)
        print(f"[fish] {s['id']} take{take} {len(wav) / sr:.1f}s ({time.time() - t0:.1f}s) "
              f"vram={torch.cuda.max_memory_allocated() / 2**30:.1f}GB", flush=True)
