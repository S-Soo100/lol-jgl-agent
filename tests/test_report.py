"""리포트 렌더링 스모크 테스트."""
from lol_jgl_agent.analysis.jungle import JungleMetrics
from lol_jgl_agent.report.renderer import render_markdown


def _metrics() -> JungleMetrics:
    return JungleMetrics(
        champion="LeeSin", position="JUNGLE", win=True, duration_min=25.0,
        cs_at_10=70, cs_at_15=110, cs_per_min=6.0, kills=8, deaths=3, assists=10,
        kill_participation=0.6, dragon_takedowns=2, death_minutes=[10.0, 20.0],
    )


def test_render_contains_sections():
    md = render_markdown(_metrics(), advice="포지셔닝을 개선하세요.",
                         match_id="KR_1", riot_id="이름#KR1")
    assert "# 정글 리포트 — LeeSin" in md
    assert "## 성장" in md
    assert "## 조언" in md
    assert "포지셔닝을 개선하세요." in md
    assert "KR_1" in md


def test_render_without_advice_has_placeholder():
    md = render_markdown(_metrics(), advice=None, match_id="KR_1", riot_id="이름#KR1")
    assert "조언 생성 안 함" in md
