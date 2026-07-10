"""규칙 기반 자동 분석 테스트."""
from lol_jgl_agent.analysis.insights import (
    Finding,
    analyze_game,
    render_findings,
    summarize_recent,
)


def _cats(findings: list[Finding]) -> dict[str, Finding]:
    return {f.category: f for f in findings}


def _base(**over) -> dict:
    """정상 승리 기준 레코드에 필드를 덮어씀."""
    rec = {
        "champion": "MonkeyKing",
        "win": True,
        "duration_min": 27.0,
        "deaths": 4,
        "death_minutes": [16.0, 22.0],
        "dragon_takedowns": 3,
        "gold_diff_vs_enemy_jgl_at_15": 500,
        "kill_participation": 0.5,
        "baron_takedowns": 1,
    }
    rec.update(over)
    return rec


def test_deaths_good_and_bad():
    assert _cats(analyze_game(_base(deaths=4)))["deaths"].severity == "good"
    assert _cats(analyze_game(_base(deaths=7)))["deaths"].severity == "warn"
    assert _cats(analyze_game(_base(deaths=10)))["deaths"].severity == "bad"


def test_early_aggression_flagged():
    # 초반 10분에 3데스 → 과욕 경고(bad)
    rec = _base(deaths=5, death_minutes=[2.6, 3.8, 4.7, 20.0])
    assert _cats(analyze_game(rec))["early_aggression"].severity == "bad"


def test_early_clean_is_good():
    rec = _base(death_minutes=[16.0, 24.0], duration_min=30.0)
    assert _cats(analyze_game(rec))["early_aggression"].severity == "good"


def test_dragons_goal():
    assert _cats(analyze_game(_base(dragon_takedowns=3)))["dragons"].severity == "good"
    assert _cats(analyze_game(_base(dragon_takedowns=1)))["dragons"].severity == "warn"


def test_lead_conversion_failure():
    # 15분 +2834골드인데 38분 장기전 패 + 바론 0 → 환전 실패(bad)
    rec = _base(win=False, gold_diff_vs_enemy_jgl_at_15=2834,
                duration_min=38.6, baron_takedowns=0, deaths=5,
                death_minutes=[24.3, 27.6])
    conv = _cats(analyze_game(rec))["lead_conversion"]
    assert conv.severity == "bad"
    assert "바론 0개" in conv.detail


def test_lead_conversion_fast_close():
    # 15분 +1600골드를 22분에 종료 승 → 환전 성공(good)
    rec = _base(win=True, gold_diff_vs_enemy_jgl_at_15=1600, duration_min=22.0)
    assert _cats(analyze_game(rec))["lead_conversion"].severity == "good"


def test_trap_metric_win():
    # 골드 밀렸지만 승리 → 함정 지표 무관(good)
    rec = _base(win=True, gold_diff_vs_enemy_jgl_at_15=-1372)
    assert _cats(analyze_game(rec))["trap_metric"].severity == "good"


def test_forcing_when_behind():
    # 밀리는데 킬관여 높음 + 패 → 과욕 신호(warn)
    rec = _base(win=False, gold_diff_vs_enemy_jgl_at_15=-500,
                kill_participation=0.64, deaths=6)
    assert _cats(analyze_game(rec))["forcing_behind"].severity == "warn"


def test_champ_fit():
    assert _cats(analyze_game(_base(champion="Naafiri")))["champ_fit"].severity == "warn"
    assert _cats(analyze_game(_base(champion="JarvanIV")))["champ_fit"].severity == "info"


def test_short_game_noted():
    rec = _base(win=False, duration_min=11.4, deaths=1, death_minutes=[7.2])
    cats = _cats(analyze_game(rec))
    assert "short_game" in cats
    # 단축 경기는 환전/과욕 규칙을 적용하지 않음
    assert "lead_conversion" not in cats
    assert "forcing_behind" not in cats


def test_summarize_recent():
    recs = [_base(dragon_takedowns=3) for _ in range(3)]
    cats = _cats(summarize_recent(recs))
    assert "record" in cats
    assert cats["dragons"].severity == "good"  # 전판 드래곤 목표 달성


def test_render_sorts_bad_first():
    findings = [
        Finding("good", "a", "좋음"),
        Finding("bad", "b", "나쁨"),
    ]
    out = render_findings(findings)
    assert out.index("나쁨") < out.index("좋음")
