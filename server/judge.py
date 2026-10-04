"""플레이어 대사 판정기: 파인튜닝 Laya → (없으면) 기본 laya-multilingual → (없으면) 휴리스틱."""

import os
import re
import time
from pathlib import Path

from laya_prompt import IMPACT_LEVELS, QUESTIONS, build_state, score_answers

ROOT = Path(__file__).resolve().parent.parent
MODEL_CANDIDATES = [
    os.environ.get("LAYA_VN_MODEL", ""),
    str(ROOT / "models" / "laya-vn"),
    str(ROOT / "models" / "laya-multilingual"),
]


class Judge:
    def __init__(self, device=None):
        self.agent = None
        self.model_name = "heuristic"
        self.error = None
        for path in MODEL_CANDIDATES:
            if path and (Path(path) / "model.safetensors").exists():
                try:
                    import laya

                    self.agent = laya.load(path, device=device)
                    self.model_name = Path(path).name
                    # 첫 호출 워밍업
                    self.agent.predict(build_state({"situation": "워밍업"}, "안녕"), QUESTIONS)
                    break
                except Exception as exc:  # 모델이 깨졌으면 다음 후보로
                    self.error = f"{path}: {exc}"
                    self.agent = None

    def judge(self, event: dict, text: str) -> dict:
        start = time.perf_counter()
        if self.agent is not None:
            answers = self.agent.predict(build_state(event, text), QUESTIONS)["answers"]
            probs = [float(answers["impact"]["probabilities"][str(i)]) for i in range(len(IMPACT_LEVELS))]
            vengeance = float(answers["vengeance"]["noul"])
            nonsense = float(answers["nonsense"]["noul"])
        else:
            probs, vengeance, nonsense = heuristic(text)
        result = score_answers(probs, vengeance, nonsense)
        result.update({
            "impact": probs,
            "impact_score": sum(i * p for i, p in enumerate(probs)),
            "vengeance": vengeance,
            "nonsense": nonsense,
            "model": self.model_name,
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
        })
        return result


_HOSTILE = re.compile(r"닥쳐|꺼져|죽어|병신|씨발|시발|좆|멍청|한심|불쌍|네 탓|니 탓|알 바|상관없")
_WARM = re.compile(r"미안|고마|괜찮|곁에|같이|함께|믿어|진심|네 잘못|니 잘못이 아|들을게|말해줘|기다릴")
_REVENGE = re.compile(r"복수|무너뜨|짓밟|대가|갚아|끝장|파멸|이용")


def heuristic(text: str):
    """모델이 없을 때만 쓰는 최소한의 대체 판정."""
    t = text.strip()
    if len(t) < 2 or not re.search(r"[가-힣]", t):
        return [0.3, 0.5, 0.2, 0.0, 0.0], 0.1, 0.9
    hostile, warm = len(_HOSTILE.findall(t)), len(_WARM.findall(t))
    if hostile > warm:
        probs = [0.55, 0.3, 0.1, 0.05, 0.0]
    elif warm >= 2 and len(t) > 25:
        probs = [0.0, 0.05, 0.15, 0.45, 0.35]
    elif warm:
        probs = [0.0, 0.1, 0.3, 0.45, 0.15]
    else:
        probs = [0.05, 0.25, 0.5, 0.15, 0.05]
    vengeance = min(0.95, 0.1 + 0.35 * len(_REVENGE.findall(t)))
    return probs, vengeance, 0.0
