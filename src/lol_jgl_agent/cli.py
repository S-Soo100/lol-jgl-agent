"""CLI 진입점.

사용법:
    lol-jgl-agent --riot-id "이름#KR1"

M1~M3에서 각 단계를 연결한다. 지금은 설정 로딩 확인용 스켈레톤.
"""
from __future__ import annotations

import argparse

from .config import Settings


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
    args = build_parser().parse_args()
    settings = Settings.load()
    riot_id = args.riot_id or settings.default_riot_id

    if not settings.riot_api_key:
        print("[!] RIOT_API_KEY가 설정되지 않았습니다. .env를 확인하세요.")
        return
    if not riot_id:
        print("[!] Riot ID가 없습니다. --riot-id 또는 .env의 DEFAULT_RIOT_ID를 설정하세요.")
        return

    # TODO(M1~M3): 수집 -> 지표 계산 -> 조언 -> 리포트 파이프라인 연결
    print(f"설정 로드 완료. 대상: {riot_id} (platform={settings.platform}, region={settings.region})")
    print("파이프라인은 M1~M3에서 구현됩니다.")


if __name__ == "__main__":
    main()
