"""Riot API 클라이언트 (Account / Match / Timeline).

M1에서 구현. rate limit 처리, 로컬 캐시, 지역 라우팅 포함 예정.
"""
from __future__ import annotations

from ..config import Settings


class RiotClient:
    """Riot API 호출 래퍼.

    - Account-V1:  Riot ID(이름#태그) -> PUUID
    - Match-V5:    PUUID -> 최근 매치 ID 목록 -> 매치 상세
    - Match-V5 Timeline: 60초 단위 위치/이벤트
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def puuid_by_riot_id(self, riot_id: str) -> str:
        """`이름#태그` -> PUUID. (region 라우팅 사용)"""
        raise NotImplementedError("M1: Account-V1 구현 예정")

    def recent_ranked_match_ids(self, puuid: str, count: int = 1) -> list[str]:
        """최근 랭크 매치 ID 목록 (queue 필터: config.RANKED_QUEUE_IDS)."""
        raise NotImplementedError("M1: Match-V5 매치 목록 구현 예정")

    def match(self, match_id: str) -> dict:
        """매치 상세(결과) JSON. 로컬 캐시 우선."""
        raise NotImplementedError("M1: Match-V5 상세 구현 예정")

    def timeline(self, match_id: str) -> dict:
        """매치 타임라인 JSON (프레임/이벤트). 로컬 캐시 우선."""
        raise NotImplementedError("M1: Match-V5 Timeline 구현 예정")
