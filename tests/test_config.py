"""설정 로딩 스모크 테스트."""
from lol_jgl_agent.config import RANKED_QUEUE_IDS, Settings


def test_settings_load_defaults(monkeypatch):
    monkeypatch.delenv("RIOT_PLATFORM", raising=False)
    monkeypatch.delenv("RIOT_REGION", raising=False)
    s = Settings.load()
    assert s.platform == "kr"
    assert s.region == "asia"
    assert s.advisor_backend in {"subscription", "api"}


def test_ranked_queue_ids():
    assert 420 in RANKED_QUEUE_IDS  # 솔로랭크
    assert 440 in RANKED_QUEUE_IDS  # 자유랭크
