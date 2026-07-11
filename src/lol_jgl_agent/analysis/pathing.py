"""타임라인 좌표 → 맵 구역 변환 (상대 정글 동선·갱 위치 분석용).

소환사의 협곡은 대략 0~14870 정사각. 주 대각선(블루베이스→레드베이스)이 미드,
좌/상단 경계가 탑, 하단/우측 경계가 바텀. 그 사이가 정글이다. (러프 매핑)
"""
from __future__ import annotations

MAXC = 14870
_SQRT2 = 1.41421356
LANE_BAND = 1900  # 라인으로 볼 경계 거리
BASE = 3000       # 베이스 코너 반경

ZONES = ("BASE", "TOP", "MID", "BOT", "TOP_JG", "BOT_JG")

_KO = {"BASE": "베이스", "TOP": "탑", "MID": "미드", "BOT": "바텀",
       "TOP_JG": "탑정글", "BOT_JG": "바텀정글"}


def _dists(x: float, y: float) -> tuple[float, float, float]:
    """(미드 대각선, 탑 라인, 바텀 라인) 까지의 대략 거리."""
    d_mid = abs(x - y) / _SQRT2
    d_top = min(x, MAXC - y)   # 좌측 또는 상단 경계
    d_bot = min(y, MAXC - x)   # 하단 또는 우측 경계
    return d_mid, d_top, d_bot


def gank_lane(x: float, y: float) -> str:
    """좌표에서 가장 가까운 라인(TOP/MID/BOT). 갱·킬 위치 분류용."""
    d_mid, d_top, d_bot = _dists(x, y)
    return min((("MID", d_mid), ("TOP", d_top), ("BOT", d_bot)), key=lambda t: t[1])[0]


def locate(x: float, y: float) -> str:
    """좌표를 맵 구역으로 변환 (BASE/TOP/MID/BOT/TOP_JG/BOT_JG)."""
    if (x < BASE and y < BASE) or (x > MAXC - BASE and y > MAXC - BASE):
        return "BASE"
    d_mid, d_top, d_bot = _dists(x, y)
    if min(d_mid, d_top, d_bot) < LANE_BAND:
        return gank_lane(x, y)
    return "TOP_JG" if y > x else "BOT_JG"  # 대각선 위=탑쪽, 아래=바텀쪽


def ko(zone: str) -> str:
    """구역 코드 → 한글."""
    return _KO.get(zone, zone)
