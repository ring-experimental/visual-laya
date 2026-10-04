"""「재의 백작」 대사 판정용 Laya 파인튜닝 (CUDA, RLCD 레시피).

laya 공식 노트북(notebooks/laya_finetune_typed_decisions_mps.py)의 학습 루프를
단일 CUDA GPU용으로 옮기고, 데이터 소스를 training/data/*.jsonl 로 바꿨다.

  .venv\\Scripts\\python.exe training\\train.py                # 학습 + 평가
  .venv\\Scripts\\python.exe training\\train.py --eval-only    # 저장된 모델 평가만
"""

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))

from laya.agent import _fix_tokenizer_config  # noqa: E402
from laya.common import QTYPES, build_model, build_sequence, proper_reward  # noqa: E402

from compile_story import compile_story  # noqa: E402
from laya_prompt import QUESTIONS, build_state, score_answers  # noqa: E402

BASE_DIR = ROOT / "models" / "laya-multilingual"
OUT_DIR = ROOT / "models" / "laya-vn"
DATA_DIR = ROOT / "training" / "data"
REPORT = ROOT / "training" / "report.json"
SEED = 20261003


# ---------------------------------------------------------------- data

def load_rows():
    story, errors = compile_story()
    events = story["events"]
    rows, bad = [], 0
    for path in sorted(DATA_DIR.glob("*.jsonl")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                ev = r["event"]
                imp = [float(x) for x in r["impact"]]
                assert ev in events, f"unknown event {ev}"
                assert len(imp) == 5 and sum(imp) > 0
                s = sum(imp)
                rows.append({
                    "batch": "b" if path.stem.endswith("_b") else "a",
                    "event": ev, "text": str(r["text"]).strip(),
                    "impact": [x / s for x in imp],
                    "vengeance": min(1.0, max(0.0, float(r.get("vengeance", 0.0)))),
                    "nonsense": min(1.0, max(0.0, float(r.get("nonsense", 0.0)))),
                })
            except Exception as exc:
                bad += 1
                print(f"  skip {path.name}:{n}: {exc}")
    # 중복 제거
    seen, uniq = set(), []
    for r in rows:
        key = (r["event"], r["text"])
        if key not in seen and r["text"]:
            seen.add(key)
            uniq.append(r)
    print(f"rows={len(uniq)} (bad={bad}, dup={len(rows) - len(uniq)}), events={len({r['event'] for r in uniq})}")
    return uniq, events


def split_rows(rows, eval_frac, mode="random"):
    if mode == "author":  # 다른 라벨러가 쓴 b 배치로만 평가 → 표현 일반화 측정
        return [r for r in rows if r["batch"] == "a"], [r for r in rows if r["batch"] == "b"]
    rng = random.Random(SEED)
    by_ev = {}
    for r in rows:
        by_ev.setdefault(r["event"], []).append(r)
    train, test = [], []
    for ev, group in sorted(by_ev.items()):
        rng.shuffle(group)
        k = max(1, int(len(group) * eval_frac))
        test += group[:k]
        train += group[k:]
    return train, test


def augment(train, events):
    """무의미/욕설 문장은 어떤 장면에서도 같은 판정 → 다른 이벤트에도 복제."""
    junk = [r for r in train if r["nonsense"] >= 0.8]
    out = list(train)
    rng = random.Random(SEED + 1)
    ev_ids = sorted(events)
    for r in junk:
        for ev in rng.sample(ev_ids, k=min(3, len(ev_ids))):
            if ev != r["event"]:
                out.append({**r, "event": ev})
    return out


def to_q(spec):
    q = {"t": spec["type"], "ins": spec["instructions"], "crit": spec.get("criteria", {})}
    return q


def build_items(rows, events, tok, cfg):
    items = []
    for r in rows:
        state = build_state(events[r["event"]], r["text"])
        targets = {
            "impact": r["impact"],
            "vengeance": [1 - r["vengeance"], r["vengeance"]],
            "nonsense": [1 - r["nonsense"], r["nonsense"]],
        }
        for qid, spec in QUESTIONS.items():
            ids, markers = build_sequence(tok, state, to_q(spec), cfg["max_len"], cfg["head_max_len"])
            target = targets[qid]
            if len(markers) != len(target):
                continue
            items.append({"ids": ids, "markers": markers, "qtype": QTYPES[spec["type"]],
                          "target": target, "qid": qid})
    return items


def collate(items, pad_id):
    b = len(items)
    seq = max(len(x["ids"]) for x in items)
    kmax = max(len(x["markers"]) for x in items)
    ids = torch.full((b, seq), pad_id, dtype=torch.long)
    att = torch.zeros((b, seq), dtype=torch.long)
    pos = torch.zeros((b, kmax), dtype=torch.long)
    mask = torch.zeros((b, kmax), dtype=torch.bool)
    tgt = torch.zeros((b, kmax), dtype=torch.float32)
    for i, x in enumerate(items):
        n, k = len(x["ids"]), len(x["markers"])
        ids[i, :n] = torch.tensor(x["ids"])
        att[i, :n] = 1
        pos[i, :k] = torch.tensor(x["markers"])
        mask[i, :k] = True
        tgt[i, :k] = torch.tensor(x["target"])
    return ids, att, pos, mask, tgt, torch.tensor([x["qtype"] for x in items])


# ---------------------------------------------------------------- train

def fit_temperature(samples):
    if len(samples) < 10:
        return 1.0
    kmax = max(len(l) for l, _ in samples)
    logits = torch.full((len(samples), kmax), -1e4)
    targets = torch.zeros((len(samples), kmax))
    for i, (l, t) in enumerate(samples):
        logits[i, :len(l)] = l
        targets[i, :len(t)] = torch.tensor(t)
    logt = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([logt], lr=0.1, max_iter=100)

    def closure():
        opt.zero_grad()
        loss = -(targets * torch.log_softmax(logits / logt.exp(), -1)).sum(-1).mean()
        loss.backward()
        return loss

    try:
        opt.step(closure)
        return float(torch.clamp(logt.exp(), 0.1, 10.0))
    except Exception:
        return 1.2


def save(model, tok, cfg, path):
    path.mkdir(parents=True, exist_ok=True)
    weights = {k: v.detach().half().cpu().contiguous() for k, v in model.state_dict().items()}
    save_file(weights, str(path / "model.safetensors"))
    model.encoder.config.save_pretrained(path / "encoder")
    tok.save_pretrained(path / "tokenizer")
    (path / "rl_agent_config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def train(args, train_items, tok, cfg):
    device = torch.device("cuda")
    model = build_model(cfg, encoder_dir=str(BASE_DIR / "encoder"))
    model.load_state_dict(load_file(str(BASE_DIR / "model.safetensors")), strict=True)
    model.float().to(device).train()

    rng = random.Random(SEED)
    order = list(range(len(train_items)))
    rng.shuffle(order)
    n_cal = min(300, len(train_items) // 10)
    cal = [train_items[i] for i in order[:n_cal]]
    tr = [train_items[i] for i in order[n_cal:]]

    enc_p = [p for n, p in model.named_parameters() if n.startswith("encoder.")]
    head_p = [p for n, p in model.named_parameters() if not n.startswith("encoder.")]
    opt = torch.optim.AdamW([{"params": enc_p, "lr": args.lr}, {"params": head_p, "lr": args.lr * 4}],
                            weight_decay=0.01)
    steps = max(1, math.ceil(len(tr) / args.batch / args.accum) * args.epochs)
    warm = max(1, steps // 20)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warm) * 0.5 * (1 + math.cos(math.pi * min(1.0, s / steps))))
    print(f"train items={len(tr)} calib={len(cal)} updates={steps}")

    t0 = time.time()
    for epoch in range(args.epochs):
        random.Random(SEED + epoch).shuffle(tr)
        # 비슷한 길이끼리 묶어 패딩 절약
        chunks = [tr[i:i + args.batch] for i in range(0, len(tr), args.batch)]
        sigma = 0.4 + (0.1 - 0.4) * epoch / max(1, args.epochs - 1)
        tot, nb = 0.0, 0
        opt.zero_grad(set_to_none=True)
        for ci, chunk in enumerate(chunks):
            ids, att, pos, mask, tgt, qt = [t.to(device) for t in collate(chunk, tok.pad_token_id)]
            with torch.autocast("cuda", dtype=torch.bfloat16):
                logits, act = model(ids, att, pos, mask, qt)
            logits = logits.float()
            k = mask.sum(-1, keepdim=True).float()
            eps = torch.randn((4,) + logits.shape, device=device) * sigma * mask
            eps = (eps - eps.sum(-1, keepdim=True) / k) * mask
            noisy = logits.detach().unsqueeze(0) + eps
            probs = torch.softmax(noisy.masked_fill(~mask, -1e4), -1)
            with torch.no_grad():
                rew = proper_reward(probs, tgt.unsqueeze(0), qt, mask, w_sph=0.75, w_rps=1.0)
                adv = rew - rew.mean(0, keepdim=True)
                adv = adv / (adv.std() + 1e-6)
            logp = -(((noisy - logits.unsqueeze(0)) ** 2) * mask).sum(-1) / (2 * sigma ** 2)
            loss_rl = -(adv * logp).mean()
            loss_ce = -(tgt * torch.log_softmax(logits.masked_fill(~mask, -1e4), -1)).sum(-1).mean()
            loss = (loss_rl + loss_ce + 0.0 * act.float().sum()) / args.accum
            loss.backward()
            nb += 1
            tot += loss.item() * args.accum
            if nb % args.accum == 0 or ci == len(chunks) - 1:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                sched.step()
                opt.zero_grad(set_to_none=True)
        print(f"epoch {epoch + 1}/{args.epochs} loss={tot / max(1, nb):.4f} ({time.time() - t0:.0f}s)")

    model.eval()
    samples = [[], [], []]
    with torch.no_grad():
        for i in range(0, len(cal), args.batch):
            chunk = cal[i:i + args.batch]
            ids, att, pos, mask, tgt, qt = [t.to(device) for t in collate(chunk, tok.pad_token_id)]
            with torch.autocast("cuda", dtype=torch.bfloat16):
                logits, _ = model(ids, att, pos, mask, qt)
            for j, x in enumerate(chunk):
                samples[x["qtype"]].append((logits[j, :len(x["markers"])].float().cpu(), x["target"]))
    temps = [fit_temperature(s) if s else 1.0 for s in samples]
    cfg = {**cfg, "fine_tuned": True, "model_name": "laya-vn-count-of-ashes", "temperature": temps}
    cfg.pop("temperature_by_options", None)
    cfg["training"] = {"epochs": args.epochs, "items": len(tr), "lr": args.lr,
                       "minutes": round((time.time() - t0) / 60, 1), "base": "convaiinnovations/laya-multilingual"}
    save(model, tok, cfg, OUT_DIR)
    print(f"saved → {OUT_DIR}  temperatures={temps}")
    del model
    torch.cuda.empty_cache()


# ---------------------------------------------------------------- eval

def evaluate(model_dir, rows, events):
    import laya

    agent = laya.load(str(model_dir), device="cuda")
    n = len(rows)
    mae_score = mae_v = mae_n = 0.0
    tier_ok = within1 = 0
    confusion = {}
    t0 = time.time()
    for r in rows:
        a = agent.predict(build_state(events[r["event"]], r["text"]), QUESTIONS)["answers"]
        p = [a["impact"]["probabilities"][str(i)] for i in range(5)]
        pv, pn = a["vengeance"]["noul"], a["nonsense"]["noul"]
        es_pred = sum(i * x for i, x in enumerate(p))
        es_gold = sum(i * x for i, x in enumerate(r["impact"]))
        mae_score += abs(es_pred - es_gold)
        mae_v += abs(pv - r["vengeance"])
        mae_n += abs(pn - r["nonsense"])
        tp = score_answers(p, pv, pn)["tier"]
        tg = score_answers(r["impact"], r["vengeance"], r["nonsense"])["tier"]
        tier_ok += tp == tg
        within1 += abs(round(es_pred) - round(es_gold)) <= 1
        confusion[f"{tg}->{tp}"] = confusion.get(f"{tg}->{tp}", 0) + 1
    return {
        "model": Path(model_dir).name, "n": n,
        "tier_accuracy": round(tier_ok / n, 3),
        "impact_mae": round(mae_score / n, 3),
        "impact_within_one_level": round(within1 / n, 3),
        "vengeance_mae": round(mae_v / n, 3),
        "nonsense_mae": round(mae_n / n, 3),
        "tier_confusion(gold->pred)": dict(sorted(confusion.items())),
        "ms_per_judgement": round((time.time() - t0) * 1000 / n, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--accum", type=int, default=2)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--eval-frac", type=float, default=0.15)
    ap.add_argument("--eval-only", action="store_true")
    ap.add_argument("--full", action="store_true", help="평가 분할 없이 전체 데이터로 학습(배포용)")
    ap.add_argument("--split", choices=["random", "author"], default="random",
                    help="random: 이벤트별 15%% 홀드아웃 / author: a배치 학습, b배치 평가")
    args = ap.parse_args()
    torch.manual_seed(SEED)

    rows, events = load_rows()
    train_rows, test_rows = split_rows(rows, args.eval_frac, args.split)
    if args.full:
        train_rows = rows
    if not args.eval_only:
        _fix_tokenizer_config(str(BASE_DIR))
        cfg = json.loads((BASE_DIR / "rl_agent_config.json").read_text())
        tok = AutoTokenizer.from_pretrained(BASE_DIR / "tokenizer")
        aug = augment(train_rows, events)
        items = build_items(aug, events, tok, cfg)
        print(f"train rows={len(train_rows)} (+aug {len(aug) - len(train_rows)}) → items={len(items)}; test rows={len(test_rows)}")
        train(args, items, tok, cfg)

    report = {"split": args.split, "test_rows": len(test_rows), "full_data_training": args.full}
    report["base_zero_shot"] = evaluate(BASE_DIR, test_rows, events)
    report["finetuned"] = evaluate(OUT_DIR, test_rows, events)
    out = REPORT.with_name(f"report_{'full' if args.full else args.split}.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
