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
    for token in ("요약", "데스 추세", "드래곤 추세", "리드 환전", "챔프별 성적", "게임별 피드백"):
        assert token in html
    # 챔프명 노출
    assert "Sylas" in html and "JarvanIV" in html


def test_game_feed_per_game_capped():
    # 각 게임 카드는 헤더 1줄 + 발견 ≤4줄 (총 ≤5줄)
    from lol_jgl_agent.report.dashboard import FEED_FINDINGS
    recs = [_rec(champion="Vi", win=False, deaths=9,
                 death_minutes=[6.5, 8.8, 12.7], dragon_takedowns=1)]
    html = render_dashboard(recs)
    # 게임 카드 존재 + 발견 줄 수 상한
    assert '<div class="gcard">' in html
    assert html.count('<div class="fl">') <= FEED_FINDINGS
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


def test_static_mode_has_no_script():
    # 정적 파일(update_url 없음)은 JS 주입 안 함
    html = render_dashboard([_rec()])
    assert "<script" not in html
    assert "업데이트" not in html


def test_interactive_mode_injects_button():
    html = render_dashboard([_rec()], update_url="/update")
    assert "<script" in html
    assert "업데이트" in html          # 버튼 라벨
    assert "/update?count=" in html    # POST 엔드포인트
    assert 'id="cnt"' in html           # 판수 입력


def test_write_dashboard(tmp_path):
    out = write_dashboard([_rec()], tmp_path / "sub" / "dashboard.html", riot_id="X#1")
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")
