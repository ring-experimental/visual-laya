"""samples/tts_compare/index.html — 대사별 A/B/C/D 청취 비교 + 지표 (metrics.json)."""

import html
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, SAMPLES  # noqa: E402

SYSTEMS = [
    ("A_qwen_current", "A · 현재 (Qwen3 Base 클론)", "감정 지시 없음"),
    ("B_fish_s2pro", "B · Fish Audio S2 Pro", "레퍼런스 클론 + [태그]"),
    ("C_higgs_v3", "C · Higgs TTS 3", "레퍼런스 클론 + <|emotion|> 토큰"),
    ("D_qwen_design", "D · Qwen3 VoiceDesign 줄별", "클론 없음, 줄마다 감정 서술"),
    ("E_zonos2", "E · ZONOS2 (Q8_0)", "레퍼런스 클론 + 감정 슬라이더, MIT"),
]
EXPECT = {"01": "angry/sad", "02": "sad", "03": "angry/disgusted", "04": "sad/fearful", "05": "fearful/sad",
          "06": "angry", "07": "sad/angry/disgusted", "08": "fearful/sad", "09": "angry/disgusted",
          "10": "disgusted/angry", "11": "fearful/sad", "12": "angry/disgusted"}


def main():
    m = json.loads((OUT / "metrics.json").read_text(encoding="utf-8"))
    rows = {(r["id"], r["file"]): r for r in m["rows"]}
    match = {k: [r["top"] in EXPECT[r["id"][:2]].split("/") for r in m["rows"] if r["system"] == k]
             for k, *_ in SYSTEMS}

    by = {k: [r for r in m["rows"] if r["system"] == k] for k, *_ in SYSTEMS}
    summary = "".join(
        f"<tr><th>{html.escape(name)}<small>{html.escape(note)}</small></th>"
        f"<td>{sum(r['cer'] <= 0.1 for r in by[k])}/{len(by[k])} · 중앙값 "
        f"{statistics.median(r['cer'] for r in by[k]) * 100:.0f}%</td><td>{m['summary'][k]['sim']:.3f}</td>"
        f"<td>{sum(match[k])}/{len(match[k])} ({sum(match[k]) / len(match[k]) * 100:.0f}%)</td></tr>"
        for k, name, note in SYSTEMS)

    cards = []
    for s in SAMPLES:
        d = OUT / s["id"]
        cells = []
        for k, name, _ in SYSTEMS:
            for f in sorted(d.glob(f"{k}*")):
                r = rows.get((s["id"], f.name), {})
                take = f.stem.rsplit("_", 1)[-1] if f.stem[-1].isdigit() else ""
                cells.append(
                    f'<div class="cell {k[0]}"><div class="lab">{html.escape(name.split(" · ")[1])}'
                    f'{" #" + take if take else ""}</div>'
                    f'<audio controls preload="none" src="{s["id"]}/{f.name}"></audio>'
                    f'<div class="met">CER {r.get("cer", 0) * 100:.0f}% · SIM {r.get("sim", 0):.2f} · '
                    f'<b>{r.get("top", "")}</b></div></div>')
        cards.append(
            f'<section><h2><span>{s["id"][:2]}</span> {html.escape(s["text"])}</h2>'
            f'<p class="meta">{s["voice"]} · {s["src"]} · 의도한 감정 <b>{EXPECT[s["id"][:2]]}</b><br>'
            f'Fish <code>{html.escape(s["fish"])}</code> · Higgs <code>{html.escape(s["higgs"])}</code> · '
            f'Zonos <code>{html.escape(json.dumps(s["zonos"]))}</code></p>'
            f'<div class="grid">{"".join(cells)}</div></section>')

    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>TTS 감정 비교</title>
<style>
:root{{--bg:#f6f4f0;--fg:#1d1b18;--mut:#6b655c;--card:#fff;--line:#e3ded5;--a:#8a8a8a;--b:#2f6fb0;--c:#1f8a5b;--d:#a8641f;--e:#8a3fa8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151412;--fg:#ece8e1;--mut:#9c958a;--card:#1f1d1a;--line:#34312c}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,"Malgun Gothic",sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:24px 16px 64px}}h1{{font-size:22px;margin:0 0 4px}}
.lead{{color:var(--mut);margin:0 0 18px}}table{{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-bottom:8px}}
th,td{{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left;font-variant-numeric:tabular-nums}}th small{{display:block;color:var(--mut);font-weight:400}}
thead th{{font-size:13px;color:var(--mut);font-weight:600}}.note{{color:var(--mut);font-size:13px;margin:6px 0 26px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:14px 0}}
h2{{font-size:17px;margin:0 0 4px}}h2 span{{color:var(--mut);font-weight:500;margin-right:4px}}.meta{{color:var(--mut);font-size:13px;margin:0 0 10px}}
code{{font-size:12px;background:var(--bg);padding:1px 5px;border-radius:4px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}}
.cell{{border:1px solid var(--line);border-left:4px solid var(--a);border-radius:8px;padding:8px 10px}}
.cell.B{{border-left-color:var(--b)}}.cell.C{{border-left-color:var(--c)}}.cell.D{{border-left-color:var(--d)}}.cell.E{{border-left-color:var(--e)}}
.lab{{font-weight:600;font-size:13px;margin-bottom:4px}}audio{{width:100%;height:34px}}.met{{color:var(--mut);font-size:12px;margin-top:3px}}
</style></head><body><main>
<h1>TTS 감정 표현 비교</h1>
<p class="lead">같은 대사 · 같은 레퍼런스 음색(현재 게임 목소리)으로 생성. B·C·E는 테이크 2개씩.</p>
<table><thead><tr><th>방식</th><th>발음 정확 (CER≤10%) ↑</th><th>SIM ↑ (톤 유지)</th><th>감정 일치 ↑</th></tr></thead><tbody>{summary}</tbody></table>
<p class="note">발음: Whisper large-v3-turbo 전사와 원문의 문자 오류율(CER)이 10% 이하인 샘플 수와 CER 중앙값 · SIM: WavLM-SV 화자 유사도(레퍼런스 대비) ·
감정 일치: emotion2vec+ 최상위 감정이 의도한 감정에 속하는 비율. 감정 분류기는 한국어 연기를 잘 구분하지 못해 참고용이며, 최종 판단은 청취로.</p>
{"".join(cards)}
</main></body></html>"""
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(OUT / "index.html")


if __name__ == "__main__":
    main()
