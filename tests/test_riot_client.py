"""RiotClient 오프라인 테스트 (네트워크 미사용)."""
import pytest

from lol_jgl_agent.config import Settings
from lol_jgl_agent.riot.client import RiotApiError, RiotClient


def _settings(**over) -> Settings:
    base = dict(
        riot_api_key="RGAPI-test",
        default_riot_id="",
        platform="kr",
        region="asia",
        advisor_backend="subscription",
        anthropic_api_key=None,
        claude_cli_path=None,
    )
    base.update(over)
    return Settings(**base)


def test_missing_key_raises():
    with pytest.raises(RiotApiError):
        RiotClient(_settings(riot_api_key=""))


def test_bad_riot_id_format_raises():
    with RiotClient(_settings()) as riot:
        with pytest.raises(RiotApiError):
            riot.puuid_by_riot_id("태그없음")


def test_regional_base_uses_region():
    with RiotClient(_settings(region="asia")) as riot:
        assert riot._regional("/x") == "https://asia.api.riotgames.com/x"
