"""지표 + 조언 -> 마크다운 리포트.

M3에서 구현. 지표 표 + 등급 + LLM 조언을 하나의 마크다운 문서로 조립.
"""
from __future__ import annotations

from ..analysis.jungle import JungleMetrics


def render_markdown(metrics: JungleMetrics, advice: str) -> str:
    """정글 지표와 조언을 마크다운 리포트 문자열로 렌더링."""
    raise NotImplementedError("M3: 마크다운 리포트 렌더링 구현 예정")
