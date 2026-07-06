"""CLI 진입점.

사용법:
    lol-jgl-agent --riot-id "이름#KR1"

현재(M1): 최근 랭크 1판을 Riot API로 받아 캐시하고, 수집 결과를 요약 출력.
지표 계산(M2)·조언(M3)은 이후 단계에서 연결한다.
"""
from __future__ import annotations

import argparse
import sys

from .config import Settings
from .riot.client import RiotApiError, RiotClient


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lol-jgl-agent",
        description="리그오브레전드 정글러 경기 후 피드백/조언",
    )
    p.add_argument(
        "--riot-id",
        help="분석할 소환사 Riot ID (예: '이름#KR1'). 생략 시 .env의 DEFAULT_RIOT_ID.",
    )
    return p


def main() -> None:
    # Windows 콘솔에서 한글 출력 깨짐 방지
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = build_parser().parse_args()
    settings = Settings.load()
    riot_id = args.riot_id or settings.default_riot_id

    if not settings.riot_api_key:
        print("[!] RIOT_API_KEY가 설정되지 않았습니다. .env를 확인하세요.")
        return
    if not riot_id:
        print("[!] Riot ID가 없습니다. --riot-id 또는 .env의 DEFAULT_RIOT_ID를 설정하세요.")
        return

    try:
        with RiotClient(settings) as riot:
            puuid = riot.puuid_by_riot_id(riot_id)
            match_ids = riot.recent_ranked_match_ids(puuid, count=1)
            if not match_ids:
                print(f"[!] {riot_id}의 최근 랭크 경기를 찾지 못했습니다.")
                return
            match_id = match_ids[0]
            match = riot.match(match_id)
            timeline = riot.timeline(match_id)
    except RiotApiError as e:
        print(f"[!] Riot API 오류: {e}")
        return

    _print_collection_summary(riot_id, match_id, match, timeline, puuid)


def _print_collection_summary(
    riot_id: str, match_id: str, match: dict, timeline: dict, puuid: str
) -> None:
    """M1 수집 검증용 요약 (지표 계산 전)."""
    me = next(
        (p for p in match["info"]["participants"] if p["puuid"] == puuid),
        None,
    )
    frames = timeline["info"]["frames"]
    print(f"수집 완료 — {riot_id}  (match {match_id})")
    print(f"  경기 시간: {match['info']['gameDuration'] // 60}분, 큐: {match['info']['queueId']}")
    print(f"  타임라인 프레임: {len(frames)}개")
    if me:
        cs = me["totalMinionsKilled"] + me["neutralMinionsKilled"]
        print(
            f"  나: {me['championName']} ({me['teamPosition']}) "
            f"{me['kills']}/{me['deaths']}/{me['assists']}, CS {cs}, "
            f"{'승리' if me['win'] else '패배'}"
        )
    print("  (지표 분석은 M2, 조언은 M3에서 연결됩니다.)")


if __name__ == "__main__":
    main()
