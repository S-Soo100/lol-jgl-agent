"""벤치마크 기준값 — 최근 랭크 90 정글판 분포로 개인 캘리브레이션.

기준의 근거(2026-07, 90판):
- 파밍·카정은 승패와 무관 → CS는 개인 분포(p25/p75)로 완만하게 평가.
- 승패를 가르는 지표는 **데스와 드래곤** → 실제 승/패 평균을 분기점으로 사용.
  (승 데스 4.3 vs 패 6.7,  승 드래곤 2.4 vs 패 1.3)
값이 클수록 좋은 지표는 HIGHER_BETTER, 작을수록 좋은 지표는 LOWER_BETTER.
"""
from __future__ import annotations

# (ok 하한, good 하한) — 값이 클수록 좋음
HIGHER_BETTER: dict[str, tuple[float, float]] = {
    "cs_per_min": (5.7, 6.8),            # p25 / p75
    "jungle_cs_before_10": (52, 65),     # p25 / p75
    "cs_at_10": (52, 65),                # jg_cs10 근사 (timeline용 참고)
    "vision_score": (20, 35),            # p25 / p75
    "kill_participation": (0.40, 0.55),
    "dragon_takedowns": (1.3, 2.4),      # 승패 분기점(패 평균 / 승 평균)
}

# (good 상한, ok 상한) — 값이 작을수록 좋음
LOWER_BETTER: dict[str, tuple[float, float]] = {
    "deaths": (4.3, 6.7),                # 승 평균 이하=good, 패 평균 초과=bad
}


def grade(metric: str, value: float | None) -> str:
    """지표값을 good/ok/bad/unknown으로 등급화."""
    if value is None:
        return "unknown"
    if metric in HIGHER_BETTER:
        ok, good = HIGHER_BETTER[metric]
        if value >= good:
            return "good"
        return "ok" if value >= ok else "bad"
    if metric in LOWER_BETTER:
        good, ok = LOWER_BETTER[metric]
        if value <= good:
            return "good"
        return "ok" if value <= ok else "bad"
    return "unknown"
