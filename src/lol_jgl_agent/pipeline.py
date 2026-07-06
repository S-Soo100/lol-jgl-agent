"""수집 → 지표 → 조언 → 리포트 파이프라인 (CLI/워처 공용).

콘솔 출력은 하지 않는다(호출자가 담당). 순수하게 리포트를 생성·저장하고 결과를 돌려준다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .advisor.backend import AdvisorError, make_advisor
from .analysis.jungle import JungleMetrics, compute_jungle_metrics
from .config import REPORTS_DIR, Settings
from .report.renderer import render_markdown
from .riot.client import RiotClient


@dataclass
class ReportResult:
    match_id: str
    metrics: JungleMetrics
    advice: str | None
    advice_error: str | None
    report_path: Path


def analyze_match(
    settings: Settings,
    riot: RiotClient,
    *,
    riot_id: str,
    puuid: str,
    match_id: str,
    no_advice: bool = False,
) -> ReportResult:
    """한 경기를 분석해 마크다운 리포트를 저장하고 결과를 반환."""
    match = riot.match(match_id)
    timeline = riot.timeline(match_id)
    metrics = compute_jungle_metrics(match, timeline, puuid)

    advice: str | None = None
    advice_error: str | None = None
    if not no_advice:
        try:
            advice = make_advisor(settings).generate_advice(metrics.model_dump_json())
        except AdvisorError as e:
            advice_error = str(e)

    md = render_markdown(metrics, advice, match_id=match_id, riot_id=riot_id)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{match_id}.md"
    report_path.write_text(md, encoding="utf-8")

    return ReportResult(match_id, metrics, advice, advice_error, report_path)
