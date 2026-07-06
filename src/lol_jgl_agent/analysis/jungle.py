"""정글 지표 계산 (기획서 §6).

M2에서 구현. Match + Timeline 원본을 받아 정글러 관점 지표 dict를 만든다.
"""
from __future__ import annotations

from pydantic import BaseModel


class JungleMetrics(BaseModel):
    """한 경기에서 대상 정글러의 지표 묶음 (조언 생성의 입력)."""

    champion: str
    win: bool

    # 성장
    cs_at_10: int | None = None
    cs_at_15: int | None = None
    cs_per_min: float | None = None
    gold_diff_vs_enemy_jgl_at_15: int | None = None

    # 동선
    first_clear_finished_sec: int | None = None
    first_gank_sec: int | None = None

    # 갱킹 / 오브젝트 / 시야 / 데스 (M2에서 채움)
    gank_involvement: dict | None = None
    objective_participation: dict | None = None
    vision: dict | None = None
    death_summary: dict | None = None


def compute_jungle_metrics(match: dict, timeline: dict, puuid: str) -> JungleMetrics:
    """대상 소환사(puuid)의 정글 지표를 계산."""
    raise NotImplementedError("M2: 정글 지표 계산 구현 예정")
