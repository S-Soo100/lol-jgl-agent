"""CLI 진입점 — 최근 랭크 N판 지표를 수집해 누적 히스토리에 쌓는다.

피드백은 Claude Code 채팅으로 받는 것이 메인 워크플로우:
    lol-jgl-agent --count 5      # 최근 5판 수집 → history.json 누적
    → 이후 Claude에게 "분석해줘" 하면 누적 데이터로 피드백

    lol-jgl-agent --count 1 --advice   # 구독 Claude(claude -p) 자동 조언까지
"""
from __future__ import annotations

import argparse
import sys

from . import history
from .analysis.jungle import JungleMetrics
from .config import Settings
from .pipeline import analyze_match, collect_metrics, metrics_to_record
from .riot.client import RiotApiError, RiotClient


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lol-jgl-agent",
        description="리그오브레전드 정글러 지표 수집 (피드백은 Claude Code 채팅으로)",
    )
    p.add_argument("--riot-id", help="Riot ID (예: '이름#KR1'). 생략 시 .env의 DEFAULT_RIOT_ID.")
    p.add_argument("--count", type=int, default=3, help="수집할 최근 랭크 경기 수. 기본 3.")
    p.add_argument("--advice", action="store_true",
                   help="최신 경기에 대해 구독 Claude(claude -p) 자동 조언·리포트도 생성.")
    p.add_argument("--insights", action="store_true",
                   help="수집한 최신 경기 + 최근 추세를 규칙 기반으로 자동 분석(LLM 없이) 출력.")
    return p


def main() -> None:
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
            match_ids = riot.recent_ranked_match_ids(puuid, count=args.count)
            if not match_ids:
                print(f"[!] {riot_id}의 최근 랭크 경기를 찾지 못했습니다.")
                return
            print(f"{len(match_ids)}판 수집 중...")
            metrics = [collect_metrics(riot, puuid, mid) for mid in match_ids]
            records = [metrics_to_record(m, mid) for m, mid in zip(metrics, match_ids)]

            advice_result = None
            if args.advice:
                print("최신 경기 조언 생성 중 (구독 Claude)...")
                advice_result = analyze_match(
                    settings, riot, riot_id=riot_id, puuid=puuid, match_id=match_ids[0],
                )
    except RiotApiError as e:
        print(f"[!] Riot API 오류: {e}")
        return

    added, total, _ = history.merge(records)
    _print_table(riot_id, metrics, match_ids)
    print(f"\n새로 {added}판 추가 · 누적 {total}판 → {history.HISTORY_PATH}")
    print("Claude Code에게 \"분석해줘\" 라고 하면 누적 데이터로 피드백해 드립니다.")

    if args.insights and records:
        _print_insights(records[0])

    if advice_result and advice_result.advice:
        print("\n=== 최신 경기 조언 ===")
        print(advice_result.advice)
    elif advice_result and advice_result.advice_error:
        print(f"\n[!] 조언 생략: {advice_result.advice_error}")


def _print_insights(newest: dict) -> None:
    """규칙 기반 자동 분석(LLM 없음)을 출력."""
    from .analysis.insights import analyze_game, render_findings, summarize_recent

    result = "승" if newest.get("win") else "패"
    print("\n=== 자동 분석 (규칙 기반, LLM 없음) ===")
    print(f"[최신 경기] {newest.get('champion')} {result} · {newest.get('duration_min')}분")
    print(render_findings(analyze_game(newest)))

    recent = summarize_recent(history.load_history())
    if recent:
        print("\n[최근 추세]")
        print(render_findings(recent))


def _print_table(riot_id: str, metrics: list[JungleMetrics], match_ids: list[str]) -> None:
    print(f"\n■ {riot_id} — 최근 {len(metrics)}판")
    print(f"  {'챔피언':<10} {'결과':<4} {'시간':>5} {'KDA':>10} {'분당CS':>6} {'15분골드차':>9} {'데스':>4}")
    for m in metrics:
        kda = f"{m.kills}/{m.deaths}/{m.assists}"
        gd = m.gold_diff_vs_enemy_jgl_at_15
        gd_s = ("-" if gd is None else (f"+{gd}" if gd > 0 else str(gd)))
        print(f"  {m.champion:<10} {'승' if m.win else '패':<4} {m.duration_min:>4}분 "
              f"{kda:>10} {m.cs_per_min:>6} {gd_s:>9} {m.deaths:>4}")


if __name__ == "__main__":
    main()
