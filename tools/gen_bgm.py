"""BGM 일괄 생성 (ACE-Step 1.5).

docs/BGM_PROMPTS.md의 스타일 태그 프롬프트를 읽어 곡마다 후보 N개를 만든다.
  - 후보: tools/bgm_out/<key>_<n>.mp3
  - 채택본(후보 1번, -15 LUFS 정규화): game/assets/bgm/<key>.mp3
theme_ashes를 먼저 만들고, 파생곡(sorrow/dawn/ending_bad/calm_sea)은 그것을 레퍼런스 오디오로 쓴다.

실행 (ACE-Step venv의 파이썬으로):
  D:\\ACE-Step-1.5\\.venv\\Scripts\\python.exe tools\\gen_bgm.py            # 전곡
  D:\\ACE-Step-1.5\\.venv\\Scripts\\python.exe tools\\gen_bgm.py tension sorrow -n 4
  ... --pick tension 3   # 후보 3번을 채택본으로 교체(생성 없음)
  ... romance --cover toolsgm_out
omance_base.mp3 --strengths 0.8 0.6 --extra "major key throughout"
      # 기존 곡의 구조/멜로디를 유지하며 다시 생성 → <key>_c<n>.mp3 (채택본은 바꾸지 않음, --pick romance c2)
  ... romance --spec toolsgm_specs
omance.json -n 2
      # ACE-Step 가이드 형식 스펙(JSON 배열: caption/lyrics/메타/LM 파라미터) → <name>_<n>.mp3 (채택본은 바꾸지 않음)
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACE = Path(os.environ.get("ACESTEP_ROOT", r"D:\ACE-Step-1.5"))
PROMPTS = ROOT / "docs" / "BGM_PROMPTS.md"
OUT = ROOT / "tools" / "bgm_out"
BGM = ROOT / "game" / "assets" / "bgm"

ORDER = ["theme_ashes", "sorrow", "dawn", "ending_bad", "calm_sea",
         "tension", "revenge", "fire", "romance", "school_day", "party"]
DERIVED = {"sorrow", "dawn", "ending_bad", "calm_sea"}
KEYS = {"Dm": "D minor", "F": "F major", "G": "G major", "Cm": "C minor", "Am": "A minor",
        "E♭": "Eb major", "Bm": "B minor", "D": "D major"}
DURATION = {"party": 120, "fire": 90}  # 나머지 150초


def load_specs():
    text = PROMPTS.read_text(encoding="utf-8")
    specs = {}
    for m in re.finditer(r"^## \d+\. `(\w+)`.*?```\s*\nSuno/Udio style: (.+?)\n```", text, re.S | re.M):
        specs[m.group(1)] = {"caption": m.group(2).strip()}
    for m in re.finditer(r"^\| (\w+) \| \**\d+\** \| (\d+) \| (\S+) \|", text, re.M):
        if m.group(1) in specs:
            specs[m.group(1)]["bpm"] = int(m.group(2))
            specs[m.group(1)]["keyscale"] = KEYS.get(m.group(3), "")
    return specs


def tail_cut(src: Path):
    """끝에 붙은 무음의 시작 시각(초). 생성 결과 끝의 수 초 무음이 루프 재생 시 끊김으로 들리므로 잘라낸다."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", "silencedetect=n=-45dB:d=1",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = re.findall(r"silence_start: ([\d.]+)", out)
    ends = re.findall(r"silence_end: ([\d.]+)", out)
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    total = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3))
    # 무음이 끝나지 않았거나 파일 끝 직전에 끝나면 = 끝까지 이어지는 꼬리
    if starts and (len(starts) > len(ends) or float(ends[-1]) > total - 0.5):
        return float(starts[-1]) + 0.3
    return None


def normalize(src: Path, dst: Path):
    cut = tail_cut(src)
    trim = f"atrim=0:{cut:.2f}," if cut else ""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                    "-af", trim + "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "48000",
                    "-b:a", "192k", str(dst)], check=True)


def init_handlers(use_lm: bool):
    os.chdir(ACE)
    sys.path.insert(0, str(ACE))
    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler

    dit, llm = AceStepHandler(), LLMHandler()
    msg, ok = dit.initialize_service(project_root=str(ACE), config_path="acestep-v15-turbo", device="cuda",
                                       offload_to_cpu=True)
    if not ok:
        sys.exit(f"DiT init failed: {msg}")
    if use_lm:
        for backend in ("vllm", "pt"):
            msg, ok = llm.initialize(checkpoint_dir=str(ACE / "checkpoints"),
                                     lm_model_path="acestep-5Hz-lm-1.7B", backend=backend, device="cuda",
                                     offload_to_cpu=True)  # 16GB: DiT 디코드용 VRAM 확보
            if ok:
                print(f"LM backend: {backend}")
                break
        else:
            print(f"LM init failed, DiT only: {msg}")
    return dit, llm


def generate(dit, llm, key, spec, n, use_lm, cover=None, strengths=(), extra="", stem=None):
    from acestep.inference import GenerationConfig, GenerationParams, generate_music

    import gc
    import torch

    ref = BGM / "theme_ashes.mp3"

    def make_params(i):
        # generate_music이 params에 LM 오디오 코드를 채워 넣으므로 후보마다 새로 만든다
        if cover:
            return GenerationParams(
                task_type="cover",
                src_audio=str(cover),
                audio_cover_strength=strengths[(i - 1) % len(strengths)],
                caption=spec["caption"] + (", " + extra if extra else "") + ", no vocals",
                lyrics="[Instrumental]",
                instrumental=True,
                bpm=spec.get("bpm"),
                keyscale=spec.get("keyscale", ""),
            )
        if "src_audio" in spec:  # 가이드 형식 + cover: 원곡의 선율·화성·구조를 물려받고 캡션으로 감정을 바꾼다
            return GenerationParams(
                task_type="cover",
                src_audio=str((ROOT / spec["src_audio"]).resolve()),
                audio_cover_strength=spec.get("cover_strength", 0.5),
                caption=spec["caption"],
                lyrics=spec["lyrics"],
                instrumental=True,
                bpm=spec.get("bpm"),
                keyscale=spec.get("keyscale", ""),
                timesignature=spec.get("timesignature", ""),
            )
        if "lyrics" in spec:  # 가이드 형식 스펙: 메타데이터는 캡션이 아닌 파라미터로, 구조는 lyrics 태그로
            return GenerationParams(
                caption=spec["caption"],
                lyrics=spec["lyrics"],
                instrumental=True,
                bpm=spec.get("bpm"),
                keyscale=spec.get("keyscale", ""),
                timesignature=spec.get("timesignature", ""),
                duration=spec.get("duration", DURATION.get(key, 150)),
                thinking=use_lm,
                use_cot_caption=False,
                use_cot_metas=False,
                use_cot_lyrics=False,
                lm_negative_prompt=spec.get("lm_negative_prompt", "NO USER INPUT"),
                lm_temperature=spec.get("lm_temperature", 0.85),
                lm_cfg_scale=spec.get("lm_cfg_scale", 2.0),
            )
        return GenerationParams(
            caption=spec["caption"] + ", no vocals",
            lyrics="[Instrumental]",
            instrumental=True,
            bpm=spec.get("bpm"),
            keyscale=spec.get("keyscale", ""),
            duration=DURATION.get(key, 150),
            reference_audio=str(ref) if key in DERIVED and ref.exists() else None,
            thinking=use_lm,
            use_cot_caption=False,  # 프롬프트를 LM이 다시 쓰지 않게
            use_cot_lyrics=False,
        )

    config = GenerationConfig(batch_size=1, audio_format="mp3", mp3_bitrate="192k")
    tmp = OUT / "_tmp"
    # 16GB에서는 150초 곡이 배치 1로 제한되므로 후보를 하나씩 뽑는다
    made = 0
    tag = "c" if cover else ""
    for i in range(1, n + 1):
        for attempt in range(3):
            gc.collect()
            torch.cuda.empty_cache()
            shutil.rmtree(tmp, ignore_errors=True)
            result = generate_music(dit, llm, make_params(i), config, save_dir=str(tmp))
            if result.success:
                break
            print(f"[{key}] retry {attempt + 1}: {result.error}")
        else:
            print(f"[{key}] FAILED candidate {i}")
            continue
        audio = result.audios[0]
        dst = OUT / (f"{stem}_{i}.mp3" if stem else f"{key}_{tag}{i}.mp3")
        shutil.move(audio["path"], dst)
        strength = f"  strength={strengths[(i - 1) % len(strengths)]}" if cover else ""
        print(f"[{key}] {dst.name}  seed={audio['params'].get('seed')}{strength}")
        made += 1
    shutil.rmtree(tmp, ignore_errors=True)
    if not made:
        return False
    if cover or stem:
        return True
    first = min(OUT.glob(f"{key}_*.mp3"))
    normalize(first, BGM / f"{key}.mp3")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="*", help="생성할 키 (기본: 전곡)")
    ap.add_argument("-n", type=int, default=2, help="곡당 후보 수")
    ap.add_argument("--no-lm", action="store_true", help="5Hz LM 없이 DiT만 사용")
    ap.add_argument("--pick", nargs=2, metavar=("KEY", "N"), help="후보 N번을 채택본으로 교체")
    ap.add_argument("--cover", type=Path, help="이 오디오를 베이스로 cover 생성 (LM 미사용)")
    ap.add_argument("--strengths", type=float, nargs="+", default=[0.7], help="cover 강도 목록, 후보마다 순환")
    ap.add_argument("--spec", type=Path, help="가이드 형식 스펙 JSON (변형별 n개씩 생성)")
    ap.add_argument("--extra", default="", help="cover 시 캡션에 덧붙일 지시")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    BGM.mkdir(parents=True, exist_ok=True)
    if args.pick:
        key, n = args.pick
        normalize(OUT / f"{key}_{n}.mp3", BGM / f"{key}.mp3")
        print(f"{key} <- {key}_{n}.mp3")
        return

    specs = load_specs()
    keys = [k for k in ORDER if not args.keys or k in args.keys]
    missing = [k for k in keys if k not in specs]
    if missing and not args.spec:
        sys.exit(f"프롬프트를 못 찾음: {missing}")

    if args.cover:
        args.cover = args.cover.resolve()  # init_handlers가 ACE 폴더로 chdir하므로
    use_lm = not args.no_lm and not args.cover
    if args.spec:
        import json
        variants = json.loads(args.spec.read_text(encoding="utf-8"))
        dit, llm = init_handlers(use_lm)
        # 변형에 "track"이 있으면 그 곡으로, 없으면 명령줄의 첫 키로
        failed = [v["name"] for v in variants
                  if not generate(dit, llm, v.get("track", keys[0]), v, args.n, use_lm, stem=v["name"])]
        print("done." + (f" failed: {failed}" if failed else ""))
        return
    dit, llm = init_handlers(use_lm)
    failed = [k for k in keys
              if not generate(dit, llm, k, specs[k], args.n, use_lm, args.cover, args.strengths, args.extra)]
    print("done." + (f" failed: {failed}" if failed else ""))


if __name__ == "__main__":
    main()
