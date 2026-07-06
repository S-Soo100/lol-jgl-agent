"""환경설정 로딩 및 전역 상수."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 경로
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / ".cache"

# 소환사의 협곡 타임라인 좌표계 (Riot 좌표: 약 0 ~ 15000)
MAP_MIN = 0
MAP_MAX = 15000

# 랭크 큐 ID (분석 대상: 랭크만)
QUEUE_SOLO = 420
QUEUE_FLEX = 440
RANKED_QUEUE_IDS = (QUEUE_SOLO, QUEUE_FLEX)


@dataclass(frozen=True)
class Settings:
    """`.env`에서 로드되는 실행 설정."""

    riot_api_key: str
    default_riot_id: str
    platform: str  # 예: "kr"
    region: str  # 예: "asia"
    advisor_backend: str  # "subscription" | "api"
    anthropic_api_key: str | None
    claude_cli_path: str | None

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            riot_api_key=os.environ.get("RIOT_API_KEY", ""),
            default_riot_id=os.environ.get("DEFAULT_RIOT_ID", ""),
            platform=os.environ.get("RIOT_PLATFORM", "kr"),
            region=os.environ.get("RIOT_REGION", "asia"),
            advisor_backend=os.environ.get("ADVISOR_BACKEND", "subscription"),
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
            claude_cli_path=os.environ.get("CLAUDE_CLI_PATH") or None,
        )
