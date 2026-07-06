"""Riot 응답을 다룰 데이터 모델 (pydantic).

M1에서 실제 응답 스키마에 맞춰 구체화. 우선 분석에 필요한 최소 필드만 스케치.
"""
from __future__ import annotations

from pydantic import BaseModel


class ParticipantSummary(BaseModel):
    """매치 결과에서 한 참가자의 핵심 지표."""

    puuid: str
    champion: str
    team_id: int
    lane: str  # 정글 판별용 (JUNGLE 여부)
    kills: int
    deaths: int
    assists: int
    total_cs: int  # minions + jungle monsters
    gold_earned: int
    vision_score: int
    win: bool


class MatchSummary(BaseModel):
    """분석에 필요한 매치 요약."""

    match_id: str
    queue_id: int
    duration_sec: int
    participants: list[ParticipantSummary]


# NOTE: 타임라인(프레임/이벤트)은 구조가 커서 M2 pathing/jungle 구현 시
#       필요한 부분만 파싱하는 헬퍼로 다룰 예정. 여기선 원본 dict를 그대로 넘긴다.
