"""나레이션 길이에 맞춰 index.html의 장면 타이밍을 다시 계산한다 (.venv-tts 또는 soundfile 있는 아무 파이썬).

- 장면 길이 = max(원래 길이, NARR_AT + 나레이션 + TAIL)
- 청취 장면(l1~l3)은 나레이션이 끝난 뒤 A → D → C 샘플 재생
- 고쳐 쓰는 곳: 각 section의 data-start/duration, 루트 duration, <!-- audio --> 블록, 타임라인의 const T
나레이션을 다시 만들었으면 이 스크립트만 다시 돌리면 된다.
"""

import json
import re
from pathlib import Path

import soundfile as sf

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
NARR_AT, TAIL, GAP, LISTEN_TAIL = 0.4, 0.8, 0.5, 0.9
BASE = {"s1": 5, "s2": 8, "s3": 10, "s4": 9, "s5": 9, "s6": 8, "s7": 7}  # 나레이션 넣기 전 장면 길이
ORDER = ["s1", "s2", "s3", "s4", "s5", "s6", "l1", "l2", "l3", "s7"]
LISTEN = {"l1": ("01_haram_knife", "C_higgs_v3_2"), "l2": ("04_yuri_sorry", "C_higgs_v3_1"),
          "l3": ("12_baek_kneel", "C_higgs_v3_2")}


def dur(rel):
    return round(sf.info(PROJ / rel).duration, 2)


def main():
    lines = [l["id"] for l in json.loads((HERE / "narration.json").read_text(encoding="utf-8"))["lines"]]
    assert sorted(lines) == sorted(ORDER), lines
    t, scenes, audio, plays = 0.0, {}, [], []
    for sid in ORDER:
        n = dur(f"assets/narration/{sid}.wav")
        audio.append(f'      <audio id="n_{sid}" src="assets/narration/{sid}.wav" data-start="{t + NARR_AT:.2f}" '
                     f'data-duration="{n}" data-track-index="4" data-volume="1"></audio>')
        if sid in LISTEN:
            sample, cfile = LISTEN[sid]
            cur = t + NARR_AT + n + GAP
            for k, f in enumerate(["A_qwen_base", "D_qwen_design", cfile], 1):
                d = dur(f"assets/voice/{sample}/{f}.wav")
                audio.append(f'      <audio id="v{sid[1]}{"adc"[k - 1]}" src="assets/voice/{sample}/{f}.wav" '
                             f'data-start="{cur:.2f}" data-duration="{d}" data-track-index="{k}" data-volume="1"></audio>')
                plays.append(f'      play("#{sid}", ".lr{sid[1]}{k}", ".lf{sid[1]}{k}", {cur:.2f}, {d});')
                cur += d + GAP
            length = cur - GAP + LISTEN_TAIL - t
        else:
            length = max(BASE[sid], NARR_AT + n + TAIL)
        length = round(length, 2)
        scenes[sid] = (round(t, 2), length)
        t = round(t + length, 2)

    p = PROJ / "index.html"
    h = p.read_text(encoding="utf-8")
    for sid, (start, length) in scenes.items():
        h, k = re.subn(rf'(<section id="{sid}" class="[^"]*") data-start="[\d.]+" data-duration="[\d.]+"',
                       rf'\1 data-start="{start}" data-duration="{length}"', h)
        assert k == 1, sid
    h, k = re.subn(r'(data-composition-id="main" data-start="0") data-duration="[\d.]+"',
                   rf'\1 data-duration="{t}"', h)
    assert k == 1
    h, k = re.subn(r"      <!-- audio -->\n(?:      <audio .*\n)*",
                   "      <!-- audio -->\n" + "\n".join(audio) + "\n", h)
    assert k == 1
    tmap = ", ".join(f"{sid}: [{s}, {s + l:.2f}]" for sid, (s, l) in scenes.items())
    h, k = re.subn(r"      const T = \{.*\};", f"      const T = {{ {tmap} }};", h)
    assert k == 1
    h, k = re.subn(r"(      // listen plays\n)(?:      play\(.*\n)*", r"\1" + "\n".join(plays).replace("\\", "\\\\") + "\n", h)
    assert k == 1
    p.write_text(h, encoding="utf-8")
    print(f"[retime] {len(ORDER)}개 장면, 총 {t}s")
    for sid, (s, l) in scenes.items():
        print(f"  {sid}: {s:6.2f} + {l}")


if __name__ == "__main__":
    main()
