"""CLI 진입점 — 최근 랭크 1판을 분석해 지표·조언 리포트를 만든다.

사용법:
    lol-jgl-agent --riot-id "이름#KR1"
    lol-jgl-agent --no-advice
"""
from __future__ import annotations

import argparse
import sys

from .analysis.jungle import JungleMetrics
from .config import Settings
from .pipeline import analyze_match
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
    p.add_argument(
        "--no-advice",
        action="store_true",
        help="Claude 조언 생성을 건너뛰고 지표 리포트만 저장.",
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
            if not args.no_advice:
                print("분석 및 조언 생성 중 (구독 Claude)...")
            result = analyze_match(
                settings, riot, riot_id=riot_id, puuid=puuid,
                match_id=match_ids[0], no_advice=args.no_advice,
            )
    except RiotApiError as e:
        print(f"[!] Riot API 오류: {e}")
        return

    if result.metrics.position != "JUNGLE":
        print("[!] 참고: 이 경기의 포지션은 정글이 아닙니다. 정글 지표는 참고용으로만 보세요.")
    _print_metrics(riot_id, result.match_id, result.metrics)

    if result.advice_error:
        print(f"\n[!] 조언 생략: {result.advice_error}")
    print(f"\n리포트 저장: {result.report_path}")
    if result.advice:
        print("\n=== 조언 ===")
        print(result.advice)


def _print_metrics(riot_id: str, match_id: str, m: JungleMetrics) -> None:
    """정글 지표 요약 출력."""
    r = "승리" if m.win else "패배"
    print(f"■ {riot_id} — {m.champion} ({m.position})  {r}  ({m.duration_min}분)  match {match_id}")
    print(f"  KDA {m.kills}/{m.deaths}/{m.assists}  킬관여율 {_pct(m.kill_participation)}")
    print("  [성장]")
    print(f"    CS@10 {m.cs_at_10}  CS@15 {m.cs_at_15}  분당CS {m.cs_per_min}  "
          f"10분전정글CS {m.jungle_cs_before_10}")
    print(f"    상대 정글러 대비 15분 골드차 {_signed(m.gold_diff_vs_enemy_jgl_at_15)}")
    print("  [오브젝트]")
    print(f"    드래곤 {m.dragon_takedowns}  전령 {m.rift_herald_takedowns}  바론 {m.baron_takedowns}"
          f"  스폰30초내처치 {m.epic_kills_within_30s_of_spawn}  스틸 {m.epic_monster_steals}")
    print("  [카정/시야]")
    print(f"    적정글CS {m.enemy_jungle_cs}  카정차 {_signed(m.counter_jungle_diff)}"
          f"  |  시야점수 {m.vision_score}  제어와드 {m.control_wards_placed}"
          f"  설치 {m.wards_placed}  제거 {m.wards_killed}")
    print("  [데스]")
    print(f"    {m.deaths}회 @ {', '.join(f'{t}분' for t in m.death_minutes) or '없음'}")


def _pct(v: float | None) -> str:
    return f"{v*100:.0f}%" if v is not None else "-"


def _signed(v: float | None) -> str:
    return "-" if v is None else (f"+{v}" if v > 0 else str(v))


if __name__ == "__main__":
    main()
