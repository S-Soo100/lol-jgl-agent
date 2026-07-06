"""경기 지표 누적 저장소 (reports/history.json).

판마다 지표를 append/merge 하며 match_id로 중복 제거한다.
"분석해줘" 시 Claude가 이 파일 전체를 읽어 트렌드를 파악하는 것이 핵심 워크플로우.
"""
from __future__ import annotations

import json

from .config import REPORTS_DIR

HISTORY_PATH = REPORTS_DIR / "history.json"


def load_history() -> list[dict]:
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    return []


def merge(new_games: list[dict]) -> tuple[int, int, list[str]]:
    """새 경기 지표를 누적 저장소에 병합.

    반환: (새로 추가된 수, 누적 총 수, 새로 추가된 match_id 목록).
    """
    by_id = {g["match_id"]: g for g in load_history()}
    added: list[str] = [g["match_id"] for g in new_games if g["match_id"] not in by_id]
    for g in new_games:
        by_id[g["match_id"]] = g

    merged = sorted(by_id.values(), key=lambda g: g["match_id"], reverse=True)
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(
        json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return len(added), len(merged), added
