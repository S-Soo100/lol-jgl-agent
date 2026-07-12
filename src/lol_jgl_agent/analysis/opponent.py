"""상대 정글러 요약 — 내 지표 옆에 나란히 저장해 "나 vs 상대"를 학습.

match+timeline에서 상대 팀 정글러를 찾아 핵심 지표 + 갱 라인 분포 +
초반 동선(1~10분) + 나를 잡은 횟수를 뽑는다. (LLM 없음, 결정론)
"""
from __future__ import annotations

from .jungle import compute_jungle_metrics
from .pathing import gank_lane, ko, locate


def _find(match: dict, puuid: str) -> dict | None:
    for p in match["info"]["participants"]:
        if p["puuid"] == puuid:
            return p
    return None


def _enemy_jungler(match: dict, me: dict) -> dict | None:
    for p in match["info"]["participants"]:
        if p["teamId"] != me["teamId"] and p.get("teamPosition") == "JUNGLE":
            return p
    return None


def enemy_jungler_summary(match: dict, timeline: dict, my_puuid: str) -> dict | None:
    """상대 정글러 요약 dict. 상대 정글이 없으면(포지션 이상) None."""
    me = _find(match, my_puuid)
    if me is None:
        return None
    enemy = _enemy_jungler(match, me)
    if enemy is None:
        return None

    em = compute_jungle_metrics(match, timeline, enemy["puuid"])
    epid = enemy["participantId"]
    mpid = me["participantId"]

    # 갱 라인/루트는 "초반(15분 전) 관여 킬"만 — 후반 한타 위치는 갱 루트가 아님
    GANK_WINDOW = 15.0
    names = {p["participantId"]: p["championName"] for p in match["info"]["participants"]}
    gank_lanes = {"TOP": 0, "MID": 0, "BOT": 0}
    gank_events: list[dict] = []  # 초반 갱 루트 (분·라인·희생자)
    first_gank = None
    my_deaths_involved = 0
    for fr in timeline["info"]["frames"]:
        for e in fr["events"]:
            if e.get("type") != "CHAMPION_KILL":
                continue
            involved = e.get("killerId") == epid or epid in e.get("assistingParticipantIds", [])
            if not involved:
                continue
            t = round(e["timestamp"] / 60000, 1)
            if t < GANK_WINDOW:
                pos = e.get("position", {})
                lane = gank_lane(pos.get("x", 0), pos.get("y", 0))
                gank_lanes[lane] += 1
                gank_events.append({
                    "min": t, "lane": ko(lane),
                    "victim": names.get(e.get("victimId"), "?"),
                    "allies": 1 + len(e.get("assistingParticipantIds", [])),
                })
            if first_gank is None:
                first_gank = t
            if e.get("victimId") == mpid:
                my_deaths_involved += 1

    frames = timeline["info"]["frames"]
    early_path = []
    for minute in range(1, 11):
        if minute < len(frames):
            pf = frames[minute]["participantFrames"].get(str(epid))
            if pf:
                early_path.append(locate(pf["position"]["x"], pf["position"]["y"]))

    return {
        "champion": em.champion,
        "kills": em.kills, "deaths": em.deaths, "assists": em.assists,
        "kill_participation": em.kill_participation,
        "cs_at_10": em.cs_at_10, "cs_per_min": em.cs_per_min,
        "dragon_takedowns": em.dragon_takedowns,
        "gold_lead_over_me_at_15": em.gold_diff_vs_enemy_jgl_at_15,  # 상대 - 나
        "gank_lanes": gank_lanes,
        "gank_events": gank_events,
        "early_path": early_path,
        "first_gank_min": first_gank,
        "my_deaths_involved": my_deaths_involved,
    }
