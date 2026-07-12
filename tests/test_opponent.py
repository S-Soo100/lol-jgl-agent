"""좌표 구역 변환 + 상대 정글 요약 테스트."""
from lol_jgl_agent.analysis.opponent import enemy_jungler_summary
from lol_jgl_agent.analysis.pathing import gank_lane, ko, locate


def test_gank_lane():
    assert gank_lane(7000, 7000) == "MID"      # 대각선
    assert gank_lane(7000, 800) == "BOT"       # 하단
    assert gank_lane(800, 7000) == "TOP"       # 좌측


def test_locate_zones():
    assert locate(1000, 1000) == "BASE"
    assert locate(7200, 7000) == "MID"
    assert locate(3200, 10000) == "TOP_JG"     # 대각선 위, 라인 아님
    assert locate(10000, 3200) == "BOT_JG"
    assert ko("BOT_JG") == "바텀정글"


def _part(pid, team, champ, puuid):
    return {"puuid": puuid, "participantId": pid, "teamId": team, "teamPosition": "JUNGLE",
            "championName": champ, "win": team == 100, "kills": 3, "deaths": 5, "assists": 9,
            "totalMinionsKilled": 20, "neutralMinionsKilled": 100,
            "challenges": {"killParticipation": 0.4, "dragonTakedowns": 2},
            "visionScore": 30, "wardsPlaced": 10, "wardsKilled": 2}


def _match():
    return {"info": {"gameDuration": 1800,
                     "participants": [_part(1, 100, "LeeSin", "me"),
                                      _part(6, 200, "Amumu", "enemy")]}}


def _timeline():
    frames = []
    for i in range(17):
        pf = {
            "1": {"minionsKilled": i, "jungleMinionsKilled": i * 4, "totalGold": 500 + i * 100,
                  "level": min(1 + i, 18), "position": {"x": 7000, "y": 7000}},
            "6": {"minionsKilled": i, "jungleMinionsKilled": i * 5, "totalGold": 600 + i * 100,
                  "level": min(1 + i, 18), "position": {"x": 9000, "y": 3000}},
        }
        events = []
        if i == 5:  # 5분 아무무가 나를 바텀에서 잡음
            events.append({"type": "CHAMPION_KILL", "timestamp": 5 * 60000,
                           "killerId": 6, "victimId": 1, "assistingParticipantIds": [],
                           "position": {"x": 11000, "y": 2000}})
        frames.append({"participantFrames": pf, "events": events})
    return {"info": {"frames": frames}}


def test_enemy_jungler_summary():
    opp = enemy_jungler_summary(_match(), _timeline(), "me")
    assert opp["champion"] == "Amumu"
    assert opp["my_deaths_involved"] == 1
    assert opp["first_gank_min"] == 5.0
    assert sum(opp["gank_lanes"].values()) == 1        # 15분 전 킬 1개
    assert opp["gank_lanes"]["BOT"] == 1               # 바텀에서
    assert len(opp["early_path"]) == 10                # 1~10분 동선
    assert len(opp["gank_events"]) == 1                # 갱 루트 타임라인
    assert opp["gank_events"][0]["victim"] == "LeeSin"
    assert opp["gank_events"][0]["lane"] == "바텀"


def test_no_enemy_jungler_returns_none():
    m = _match()
    m["info"]["participants"][1]["teamPosition"] = "TOP"  # 상대 정글 없음
    assert enemy_jungler_summary(m, _timeline(), "me") is None
