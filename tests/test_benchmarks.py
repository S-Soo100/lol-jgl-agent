"""벤치마크 등급화 테스트 (higher/lower better)."""
from lol_jgl_agent.analysis.benchmarks import grade


def test_higher_better():
    assert grade("cs_per_min", 7.0) == "good"
    assert grade("cs_per_min", 6.0) == "ok"
    assert grade("cs_per_min", 5.0) == "bad"


def test_lower_better_deaths():
    assert grade("deaths", 3) == "good"   # 승 평균(4.3) 이하
    assert grade("deaths", 6) == "ok"     # 패 평균(6.7) 이하
    assert grade("deaths", 9) == "bad"    # 초과


def test_dragon_win_driver():
    assert grade("dragon_takedowns", 3) == "good"
    assert grade("dragon_takedowns", 1) == "bad"


def test_unknown():
    assert grade("does_not_exist", 5) == "unknown"
    assert grade("deaths", None) == "unknown"
