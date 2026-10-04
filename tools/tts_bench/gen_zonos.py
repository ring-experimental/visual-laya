"""ZONOS2 샘플 (Windows, zonos2.cpp Vulkan 서버 http://127.0.0.1:1919 에 요청).

서버: models/zonos2cpp/start-zonos2.bat -Quant q8_0 -Yes -NoBrowser
레퍼런스 클론(speaker_audio_base64) + 감정 슬라이더/축, expressive 모드 + emotion CFG 1.5 (README 권장).
한국어에서 빈 출력·폭주(최대 길이까지 생성)가 잦아, 길이가 정상 범위일 때까지 시드를 바꿔 재시도하고
시도 횟수를 zonos_attempts.json에 남긴다.
"""

import base64
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, SAMPLES, TAKES, polish, ref, tts_text  # noqa: E402

URL = "http://127.0.0.1:1919"


def post(path, body):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.read()


def plausible(sec, text):
    return 0.25 + len(text) * 0.04 <= sec <= 2.5 + len(text) * 0.3


def main():
    caps = json.loads(urllib.request.urlopen(URL + "/tts/capabilities", timeout=30).read())
    print("[zonos] capabilities:", {k: caps.get(k) for k in ("emotion_enabled", "emotion_names", "emotion_axes")})
    refs, attempts = {}, {}
    for s in SAMPLES:
        if s["voice"] not in refs:
            refs[s["voice"]] = base64.b64encode(ref(s["voice"])[0].read_bytes()).decode()
        z = s["zonos"]
        for take in range(1, TAKES + 1):
            out = OUT / s["id"] / f"E_zonos2_{take}.wav"
            if out.exists():
                continue
            t0 = time.time()
            for n, seed in enumerate(range(take, take + 100 * 20, 100), 1):  # 테이크별로 겹치지 않는 시드
                wav_bytes = post("/tts/generate", {
                    "text": tts_text(s["text"]), "language": "ko", "seed": seed, "stream": False, "format": "wav",
                    "speaker_audio_base64": refs[s["voice"]], "speaker_audio_name": f"{s['voice']}.wav",
                    "accurate_mode": False, "emotion_enabled": True, "emotion_sliders": z["sliders"],
                    "emotion_valence": z.get("valence", 0.0), "emotion_arousal": z.get("arousal", 0.0),
                    "emotion_cfg_scale": 1.5, "quality_values": {"trailing_silence_s": 0.3},
                })
                wav, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32")
                if len(wav) and plausible(len(wav) / sr, s["text"]):
                    break
            attempts[f"{s['id']}/{out.name}"] = n
            sf.write(out, polish(wav, sr), sr)
            print(f"[zonos] {s['id']} take{take} {len(wav) / sr:.1f}s attempts={n} ({time.time() - t0:.1f}s)", flush=True)
    log = OUT / "zonos_attempts.json"
    prev = json.loads(log.read_text(encoding="utf-8")) if log.exists() else {}
    log.write_text(json.dumps({**prev, **attempts}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
