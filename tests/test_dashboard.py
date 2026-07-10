"""HTML 대시보드 렌더링 테스트."""
from lol_jgl_agent.report.dashboard import render_dashboard, write_dashboard


def _rec(**over) -> dict:
    rec = {
        "champion": "JarvanIV", "win": True, "duration_min": 28.0,
        "deaths": 4, "death_minutes": [16.0, 22.0], "dragon_takedowns": 3,
        "gold_diff_vs_enemy_jgl_at_15": 600, "kill_participation": 0.6,
        "baron_takedowns": 1,
    }
    rec.update(over)
    return rec


def test_empty_history():
    html = render_dashboard([])
    assert "데이터 없음" in html
    assert html.startswith("<!doctype html>")


def test_renders_sections_and_selfcontained():
    recs = [_rec(champion="Sylas", win=True), _rec(champion="JarvanIV", win=False, deaths=10)]
    html = render_dashboard(recs, riot_id="테스터#KR1")
    # 자체완결: 외부 요청 없음
    assert "http://" not in html and "https://" not in html
    assert "<script" not in html  # 런타임 JS 없음
    # 핵심 섹션
    for token in ("요약", "데스 추세", "드래곤 추세", "리드 환전", "챔프별 성적", "자동 분석"):
        assert token in html
    # 챔프명 노출
    assert "Sylas" in html and "JarvanIV" in html
    # 테마 대응
    assert "prefers-color-scheme:dark" in html


def test_lead_conversion_uses_win_loss_colors():
    recs = [_rec(win=False, gold_diff_vs_enemy_jgl_at_15=2834)]
    html = render_dashboard(recs)
    assert "var(--loss)" in html  # 패는 loss 색


def test_win_rate_tile():
    recs = [_rec(win=True), _rec(win=True), _rec(win=False)]
    html = render_dashboard(recs)
    assert "67%" in html  # 2/3 승률


def test_write_dashboard(tmp_path):
    out = write_dashboard([_rec()], tmp_path / "sub" / "dashboard.html", riot_id="X#1")
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")
