"""정글 지표 계산 로직 테스트 (합성 데이터)."""
from lol_jgl_agent.analysis.jungle import compute_jungle_metrics


def _frame(minute, cs1, jg1, gold1, gold2, events=None):
    return {
        "timestamp": minute * 60000,
        "participantFrames": {
            "1": {"minionsKilled": cs1, "jungleMinionsKilled": jg1,
                  "totalGold": gold1, "position": {"x": 0, "y": 0}},
            "2": {"minionsKilled": 0, "jungleMinionsKilled": 0,
                  "totalGold": gold2, "position": {"x": 0, "y": 0}},
        },
        "events": events or [],
    }


def _fixture():
    match = {"info": {
        "gameDuration": 900,  # 15분
        "participants": [
            {"puuid": "ME", "participantId": 1, "teamId": 100, "teamPosition": "JUNGLE",
             "championName": "LeeSin", "kills": 2, "deaths": 1, "assists": 1,
             "totalMinionsKilled": 10, "neutralMinionsKilled": 90, "win": True,
             "visionScore": 20, "wardsPlaced": 5, "wardsKilled": 3,
             "challenges": {"jungleCsBefore10Minutes": 40.0, "killParticipation": 0.5,
                            "dragonTakedowns": 1, "baronTakedowns": 0,
                            "enemyJungleMonsterKills": 8, "moreEnemyJungleThanOpponent": 3.0,
                            "controlWardsPlaced": 2}},
            {"puuid": "ENEMY", "participantId": 2, "teamId": 200, "teamPosition": "JUNGLE",
             "championName": "Elise", "kills": 0, "deaths": 0, "assists": 0,
             "totalMinionsKilled": 0, "neutralMinionsKilled": 0, "win": False},
        ],
    }}
    frames = [_frame(m, cs1=m, jg1=m * 3, gold1=500 * m, gold2=400 * m) for m in range(16)]
    # 이벤트: 5분 내 죽음, 6분 킬, 7분 리프트헤럴드 관여
    frames[5]["events"].append(
        {"type": "CHAMPION_KILL", "timestamp": 5 * 60000, "victimId": 1,
         "killerId": 2, "position": {"x": 100, "y": 200}, "assistingParticipantIds": []})
    frames[6]["events"].append(
        {"type": "CHAMPION_KILL", "timestamp": 6 * 60000, "victimId": 2,
         "killerId": 1, "position": {"x": 0, "y": 0}, "assistingParticipantIds": []})
    frames[7]["events"].append(
        {"type": "ELITE_MONSTER_KILL", "timestamp": 7 * 60000, "monsterType": "RIFTHERALD",
         "killerId": 1, "assistingParticipantIds": []})
    timeline = {"info": {"frameInterval": 60000, "frames": frames}}
    return match, timeline


def test_growth_and_gold_diff():
    match, timeline = _fixture()
    mt = compute_jungle_metrics(match, timeline, "ME")
    # 10분 CS = minionsKilled(10) + jungleMinionsKilled(30)
    assert mt.cs_at_10 == 10 + 30
    # 15분 골드차 = 500*15 - 400*15 = 1500
    assert mt.gold_diff_vs_enemy_jgl_at_15 == 1500
    assert mt.jungle_cs_before_10 == 40.0


def test_events_extracted():
    match, timeline = _fixture()
    mt = compute_jungle_metrics(match, timeline, "ME")
    assert mt.death_minutes == [5.0]
    assert mt.death_positions[0].x == 100
    assert mt.takedown_minutes == [6.0]  # 내가 킬한 것만
    assert mt.rift_herald_takedowns == 1
    assert mt.dragon_takedowns == 1
    assert mt.kill_participation == 0.5
