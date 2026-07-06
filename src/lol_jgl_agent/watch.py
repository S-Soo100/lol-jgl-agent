"""자동 감시 워처 (Level 1 폴링).

백그라운드로 상주하며 주기적으로 "새 랭크 경기가 올라왔는지" Riot API에 확인한다.
새 경기가 감지되면 파이프라인을 실행해 리포트를 저장하고 자동으로 열어준다.

사용법:
    lol-jgl-watch                 # .env의 DEFAULT_RIOT_ID, 30초 간격
    lol-jgl-watch --interval 20 --riot-id "이름#KR1"
    lol-jgl-watch --no-open       # 리포트 자동 열기 끄기
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from .config import CACHE_DIR, Settings
from .pipeline import analyze_match
from .riot.client import RiotApiError, RiotClient

_STATE_PATH = CACHE_DIR / "watch_state.json"


def _load_state() -> dict:
    if _STATE_PATH.exists():
        return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_state(state: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lol-jgl-watch",
        description="게임 종료를 자동 감지해 리포트를 생성하는 워처 (폴링)",
    )
    p.add_argument("--riot-id", help="감시할 Riot ID. 생략 시 .env의 DEFAULT_RIOT_ID.")
    p.add_argument("--interval", type=int, default=30, help="폴링 간격(초). 기본 30.")
    p.add_argument("--no-advice", action="store_true", help="조언 생성 건너뛰기.")
    p.add_argument("--no-open", action="store_true", help="리포트 자동 열기 끄기.")
    return p


def _open_report(path: str) -> None:
    try:
        os.startfile(path)  # type: ignore[attr-defined]  # Windows 전용
    except OSError:
        pass


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

    args = build_parser().parse_args()
    settings = Settings.load()
    riot_id = args.riot_id or settings.default_riot_id

    if not settings.riot_api_key or not riot_id:
        print("[!] RIOT_API_KEY 또는 Riot ID가 없습니다. .env를 확인하세요.")
        return

    state = _load_state()
    try:
        with RiotClient(settings) as riot:
            puuid = riot.puuid_by_riot_id(riot_id)

            # 첫 실행이면 현재 최신 경기를 기준선으로만 기록 (재분석 방지)
            if riot_id not in state:
                latest = riot.recent_ranked_match_ids(puuid, count=1)
                state[riot_id] = latest[0] if latest else ""
                _save_state(state)
                print(f"[기준선] 현재 최신 경기 = {state[riot_id] or '없음'} "
                      f"(직전 경기를 지금 분석하려면 `lol-jgl-agent` 실행)")

            print(f"■ 감시 시작 — {riot_id}, {args.interval}초 간격. 게임 끝나면 자동 리포트. (Ctrl+C 종료)")
            _watch_loop(settings, riot, riot_id, puuid, state, args)
    except RiotApiError as e:
        print(f"[!] Riot API 오류: {e}")
    except KeyboardInterrupt:
        print("\n감시 종료.")


def _watch_loop(settings, riot, riot_id, puuid, state, args) -> None:
    while True:
        time.sleep(args.interval)
        try:
            latest = riot.recent_ranked_match_ids(puuid, count=1)
        except RiotApiError as e:
            print(f"[!] 폴링 실패(계속 재시도): {e}")
            continue

        match_id = latest[0] if latest else ""
        if not match_id or match_id == state.get(riot_id):
            continue  # 새 경기 없음

        print(f"\n▶ 새 경기 감지: {match_id} — 분석 중...")
        try:
            result = analyze_match(
                settings, riot, riot_id=riot_id, puuid=puuid,
                match_id=match_id, no_advice=args.no_advice,
            )
        except RiotApiError as e:
            print(f"[!] 분석 실패: {e}")
            continue

        state[riot_id] = match_id
        _save_state(state)
        m = result.metrics
        print(f"  {m.champion} ({m.position}) {'승' if m.win else '패'} "
              f"{m.kills}/{m.deaths}/{m.assists} → {result.report_path}")
        if result.advice_error:
            print(f"  [!] 조언 생략: {result.advice_error}")
        if not args.no_open:
            _open_report(str(result.report_path))


if __name__ == "__main__":
    main()
