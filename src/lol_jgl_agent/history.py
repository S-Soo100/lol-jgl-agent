"""경기 지표 누적 저장소 (계정별 분리).

- 기본 계정(.env의 DEFAULT_RIOT_ID) → `reports/history.json` (하위호환)
- 다른 계정(부캐 등)      → `reports/history_<슬러그>.json`

계정을 섞으면 데스·드래곤 레버, 챔프 승률, 추세가 전부 무의미해지므로
파일 자체를 분리한다. 판마다 match_id로 중복 제거해 누적한다.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .config import REPORTS_DIR

HISTORY_PATH = REPORTS_DIR / "history.json"  # 기본 계정


def _slug(riot_id: str) -> str:
    """Riot ID → 파일명 안전 슬러그 ('이름#태그' → '이름-태그')."""
    return re.sub(r"[^\w가-힣-]", "-", riot_id.replace("#", "-")).strip("-")


def history_path(riot_id: str | None = None) -> Path:
    """계정별 히스토리 경로. 기본 계정/생략 시 history.json."""
    if not riot_id:
        return HISTORY_PATH
    from .config import Settings

    default = (Settings.load().default_riot_id or "").strip().lower()
    if default and riot_id.strip().lower() == default:
        return HISTORY_PATH
    return REPORTS_DIR / f"history_{_slug(riot_id)}.json"


def load_history(riot_id: str | None = None) -> list[dict]:
    p = history_path(riot_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return []


def merge(new_games: list[dict], riot_id: str | None = None) -> tuple[int, int, list[str]]:
    """새 경기 지표를 해당 계정 저장소에 병합.

    반환: (새로 추가된 수, 누적 총 수, 새로 추가된 match_id 목록).
    """
    p = history_path(riot_id)
    by_id = {g["match_id"]: g for g in load_history(riot_id)}
    added: list[str] = [g["match_id"] for g in new_games if g["match_id"] not in by_id]
    for g in new_games:
        by_id[g["match_id"]] = g

    merged = sorted(by_id.values(), key=lambda g: g["match_id"], reverse=True)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(added), len(merged), added
