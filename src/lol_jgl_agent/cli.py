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
from .pipeline import (
    analyze_match,
    backfill_opponents,
    collect_metrics,
    metrics_to_record,
    opponent_summary,
)
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
    p.add_argument("--dashboard", action="store_true",
                   help="누적 히스토리를 자체완결 HTML 대시보드(reports/dashboard.html)로 생성.")
    p.add_argument("--open", action="store_true",
                   help="대시보드를 기본 브라우저로 자동으로 연다.")
    p.add_argument("--no-collect", action="store_true",
                   help="Riot 수집 없이 기존 히스토리로 --insights/--dashboard만 실행.")
    p.add_argument("--backfill-opponent", action="store_true",
                   help="기존 히스토리에 상대 정글 요약을 캐시 기반으로 소급 채운다.")
    return p


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = build_parser().parse_args()
    settings = Settings.load()
    riot_id = args.riot_id or settings.default_riot_id

    if args.backfill_opponent:
        if not riot_id:
            print("[!] Riot ID가 없습니다.")
            return
        print("상대 정글 소급 채우는 중 (캐시 기반)...")
        updated, err = backfill_opponents(settings, riot_id)
        print(f"[!] {err}" if err else f"{updated}판에 상대 정글 요약 추가 완료.")
        return

    records: list[dict] = []
    if not args.no_collect:
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
                records = []
                for m, mid in zip(metrics, match_ids):
                    rec = metrics_to_record(m, mid)
                    rec["opponent"] = opponent_summary(riot, puuid, mid)
                    records.append(rec)

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

        if advice_result and advice_result.advice:
            print("\n=== 최신 경기 조언 ===")
            print(advice_result.advice)
        elif advice_result and advice_result.advice_error:
            print(f"\n[!] 조언 생략: {advice_result.advice_error}")

    # --insights/--dashboard는 방금 수집분 또는 기존 히스토리로 동작
    newest = records[0] if records else next(iter(history.load_history()), None)

    if args.insights:
        if newest:
            _print_insights(newest)
        else:
            print("[!] 히스토리가 비어 있습니다. 먼저 수집하세요 (--count N).")

    if args.dashboard:
        _write_dashboard(riot_id, open_browser=args.open)
    elif args.open:
        _open_dashboard()


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


def _write_dashboard(riot_id: str, *, open_browser: bool = False) -> None:
    """누적 히스토리를 HTML 대시보드로 저장(선택적으로 브라우저로 연다)."""
    from .config import REPORTS_DIR
    from .report.dashboard import write_dashboard

    path = write_dashboard(history.load_history(), REPORTS_DIR / "dashboard.html",
                           riot_id=riot_id)
    print(f"\n대시보드 생성: {path}")
    if open_browser:
        _open_path(path)
    else:
        print("  브라우저로 열면 LLM 호출 없이 기본 피드백을 볼 수 있어요.")


def _open_dashboard() -> None:
    """이미 생성된 대시보드를 브라우저로 연다."""
    from .config import REPORTS_DIR

    path = REPORTS_DIR / "dashboard.html"
    if path.exists():
        _open_path(path)
    else:
        print(f"[!] 대시보드가 없습니다. --dashboard로 먼저 생성하세요. ({path})")


def _open_path(path) -> None:
    import webbrowser

    webbrowser.open(path.resolve().as_uri())
    print(f"  브라우저로 열었습니다: {path}")


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
