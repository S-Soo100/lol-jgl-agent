"""타임라인 좌표 -> 맵 구역 변환 및 동선 분석.

M2에서 구현. 타임라인 프레임의 (x, y)를 맵 구역(블루/레드 정글, 라인, 강 등)으로
매핑하고, 시간대별 동선을 재구성한다.
"""
from __future__ import annotations

# 소환사의 협곡 구역 구분(러프). M2에서 좌표 경계를 실측/보정.
ZONES = (
    "TOP_LANE",
    "MID_LANE",
    "BOT_LANE",
    "BLUE_JUNGLE",
    "RED_JUNGLE",
    "RIVER",
    "BASE",
)


def locate(x: int, y: int) -> str:
    """좌표를 맵 구역 이름으로 변환."""
    raise NotImplementedError("M2: 구역 경계 매핑 구현 예정")
