"""자동 감시 워처 (Level 1 폴링).

백그라운드로 상주하며 주기적으로 "새 랭크 경기가 올라왔는지" 확인하고,
새 경기가 감지되면 지표를 계산해 누적 히스토리(history.json)에 조용히 적립한다.
피드백은 나중에 Claude Code에게 "분석해줘" 하면 누적 데이터로 받는다.

사용법:
    lol-jgl-watch                 # .env의 DEFAULT_RIOT_ID, 30초 간격
    lol-jgl-watch --interval 20 --riot-id "이름#KR1"
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from . import history
from .config import CACHE_DIR, Settings
from .pipeline import collect_metrics, metrics_to_record
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
        description="게임 종료를 자동 감지해 지표를 누적 적립하는 워처 (폴링)",
    )
    p.add_argument("--riot-id", help="감시할 Riot ID. 생략 시 .env의 DEFAULT_RIOT_ID.")
    p.add_argument("--interval", type=int, default=30, help="폴링 간격(초). 기본 30.")
    return p


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

            # 첫 실행이면 현재 최신 경기를 기준선으로만 기록 (재적립 방지)
            if riot_id not in state:
                latest = riot.recent_ranked_match_ids(puuid, count=1)
                state[riot_id] = latest[0] if latest else ""
                _save_state(state)
                print(f"[기준선] 현재 최신 경기 = {state[riot_id] or '없음'}")

            print(f"■ 감시 시작 — {riot_id}, {args.interval}초 간격. "
                  f"게임 끝나면 자동 적립. (Ctrl+C 종료)")
            _watch_loop(riot, riot_id, puuid, state, args.interval)
    except RiotApiError as e:
        print(f"[!] Riot API 오류: {e}")
    except KeyboardInterrupt:
        print("\n감시 종료.")


def _watch_loop(riot: RiotClient, riot_id: str, puuid: str, state: dict, interval: int) -> None:
    while True:
        time.sleep(interval)
        try:
            latest = riot.recent_ranked_match_ids(puuid, count=1)
        except RiotApiError as e:
            print(f"[!] 폴링 실패(계속 재시도): {e}")
            continue

        match_id = latest[0] if latest else ""
        if not match_id or match_id == state.get(riot_id):
            continue  # 새 경기 없음

        try:
            m = collect_metrics(riot, puuid, match_id)
        except RiotApiError as e:
            print(f"[!] 적립 실패: {e}")
            continue

        _, total, _ = history.merge([metrics_to_record(m, match_id)])
        state[riot_id] = match_id
        _save_state(state)
        print(f"▶ 새 경기 적립: {m.champion} ({m.position}) "
              f"{'승' if m.win else '패'} {m.kills}/{m.deaths}/{m.assists} · 누적 {total}판")


if __name__ == "__main__":
    main()
