"""티어별 벤치마크 기준값.

초기엔 러프한 하드코딩 기준(중급자 기준 근사). 추후 공개 통계로 보정.
지표값을 기준과 비교해 'good' / 'ok' / 'bad' 등급을 매긴다.
"""
from __future__ import annotations

# 러프 기준 (예시값 — M2/M4에서 실측 보정 필요)
# 각 항목: (하한_ok, 상한_good). 값이 클수록 좋은 지표 기준.
ROUGH_BENCHMARKS: dict[str, tuple[float, float]] = {
    "cs_at_10": (60, 75),
    "cs_at_15": (95, 120),
    "cs_per_min": (5.0, 6.5),
}


def grade(metric: str, value: float | None) -> str:
    """지표값을 good/ok/bad/unknown으로 등급화."""
    if value is None or metric not in ROUGH_BENCHMARKS:
        return "unknown"
    ok, good = ROUGH_BENCHMARKS[metric]
    if value >= good:
        return "good"
    if value >= ok:
        return "ok"
    return "bad"
