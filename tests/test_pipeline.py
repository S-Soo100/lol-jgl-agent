"""파이프라인 배선 테스트 (가짜 RiotClient, 조언 생략)."""
import lol_jgl_agent.pipeline as pipeline
from lol_jgl_agent.config import Settings


def _settings() -> Settings:
    return Settings(
        riot_api_key="RGAPI-test", default_riot_id="", platform="kr", region="asia",
        advisor_backend="subscription", anthropic_api_key=None, claude_cli_path=None,
    )


def _match_timeline():
    match = {"info": {
        "gameDuration": 600,
        "participants": [
            {"puuid": "ME", "participantId": 1, "teamId": 100, "teamPosition": "JUNGLE",
             "championName": "LeeSin", "kills": 3, "deaths": 1, "assists": 4,
             "totalMinionsKilled": 20, "neutralMinionsKilled": 60, "win": True,
             "visionScore": 15, "wardsPlaced": 4, "wardsKilled": 2,
             "challenges": {"killParticipation": 0.7, "dragonTakedowns": 1}},
            {"puuid": "ENEMY", "participantId": 2, "teamId": 200, "teamPosition": "JUNGLE",
             "championName": "Elise", "kills": 0, "deaths": 0, "assists": 0,
             "totalMinionsKilled": 0, "neutralMinionsKilled": 0, "win": False},
        ],
    }}
    frames = [{"timestamp": m * 60000, "participantFrames": {
        "1": {"minionsKilled": m, "jungleMinionsKilled": m, "totalGold": 100 * m,
              "position": {"x": 0, "y": 0}},
        "2": {"minionsKilled": 0, "jungleMinionsKilled": 0, "totalGold": 90 * m,
              "position": {"x": 0, "y": 0}},
    }, "events": []} for m in range(3)]
    return match, {"info": {"frameInterval": 60000, "frames": frames}}


class _FakeRiot:
    def __init__(self, match, timeline):
        self._m, self._t = match, timeline

    def match(self, _mid):
        return self._m

    def timeline(self, _mid):
        return self._t


def test_analyze_match_writes_report(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REPORTS_DIR", tmp_path)
    match, timeline = _match_timeline()
    result = pipeline.analyze_match(
        _settings(), _FakeRiot(match, timeline),
        riot_id="이름#KR1", puuid="ME", match_id="KR_TEST", no_advice=True,
    )
    assert result.report_path.exists()
    assert result.metrics.champion == "LeeSin"
    assert result.advice is None
    assert "LeeSin" in result.report_path.read_text(encoding="utf-8")
