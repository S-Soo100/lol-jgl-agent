"""정글 지표 계산 (기획서 §6).

Match + Timeline 원본에서 대상 정글러의 지표를 뽑는다.
- Riot이 사전 계산한 match participant의 `challenges`를 우선 사용.
- 프레임 단위 값(CS@10/15, 상대 정글러 골드차, 데스 좌표/타이밍)은 타임라인에서 계산.
"""
from __future__ import annotations

from pydantic import BaseModel


class DeathEvent(BaseModel):
    minute: float
    x: int
    y: int


class JungleMetrics(BaseModel):
    """한 경기에서 대상 정글러의 지표 묶음 (조언 생성의 입력)."""

    champion: str
    position: str
    win: bool
    duration_min: float

    # 성장
    cs_at_10: int | None = None
    cs_at_15: int | None = None
    cs_per_min: float | None = None
    jungle_cs_before_10: float | None = None
    gold_diff_vs_enemy_jgl_at_15: int | None = None

    # 킬 관여
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    kill_participation: float | None = None
    takedown_minutes: list[float] = []  # 킬/어시 관여 시점(분)

    # 오브젝트
    dragon_takedowns: int = 0
    baron_takedowns: int = 0
    rift_herald_takedowns: int = 0
    epic_kills_within_30s_of_spawn: int = 0
    epic_monster_steals: int = 0

    # 카정
    enemy_jungle_cs: int | None = None
    counter_jungle_diff: float | None = None  # 내 적정글CS - 상대 적정글CS

    # 시야
    vision_score: int | None = None
    control_wards_placed: int | None = None
    wards_placed: int | None = None
    wards_killed: int | None = None

    # 데스
    death_minutes: list[float] = []
    death_positions: list[DeathEvent] = []


# --- 헬퍼 -------------------------------------------------------------------


def _round1(v: float | None) -> float | None:
    return round(v, 1) if v is not None else None


def _participants(match: dict) -> list[dict]:
    return match["info"]["participants"]


def _me(match: dict, puuid: str) -> dict:
    for p in _participants(match):
        if p["puuid"] == puuid:
            return p
    raise ValueError(f"puuid {puuid}가 매치에 없습니다.")


def _enemy_jungler_pid(match: dict, me: dict) -> int | None:
    for p in _participants(match):
        if p["teamId"] != me["teamId"] and p["teamPosition"] == "JUNGLE":
            return p["participantId"]
    return None


def _frame_at(timeline: dict, minute: int) -> dict | None:
    frames = timeline["info"]["frames"]
    return frames[minute] if minute < len(frames) else None


def _cs_at(timeline: dict, pid: int, minute: int) -> int | None:
    frame = _frame_at(timeline, minute)
    if frame is None:
        return None
    pf = frame["participantFrames"][str(pid)]
    return pf["minionsKilled"] + pf["jungleMinionsKilled"]


def _gold_at(timeline: dict, pid: int, minute: int) -> int | None:
    frame = _frame_at(timeline, minute)
    if frame is None:
        return None
    return frame["participantFrames"][str(pid)]["totalGold"]


# --- 메인 -------------------------------------------------------------------


def compute_jungle_metrics(match: dict, timeline: dict, puuid: str) -> JungleMetrics:
    """대상 소환사(puuid)의 정글 지표를 계산."""
    info = match["info"]
    me = _me(match, puuid)
    my_pid = me["participantId"]
    ch = me.get("challenges", {})
    duration_min = info["gameDuration"] / 60

    total_cs = me["totalMinionsKilled"] + me["neutralMinionsKilled"]

    # 상대 정글러 대비 15분 골드차
    enemy_pid = _enemy_jungler_pid(match, me)
    gold_diff_15 = None
    if enemy_pid is not None:
        mine = _gold_at(timeline, my_pid, 15)
        theirs = _gold_at(timeline, enemy_pid, 15)
        if mine is not None and theirs is not None:
            gold_diff_15 = mine - theirs

    # 타임라인 이벤트: 데스 / 관여 / 오브젝트
    death_minutes: list[float] = []
    deaths: list[DeathEvent] = []
    takedown_minutes: list[float] = []
    herald = 0
    for frame in timeline["info"]["frames"]:
        for e in frame["events"]:
            et = e.get("type")
            if et == "CHAMPION_KILL":
                minute = e["timestamp"] / 60000
                if e.get("victimId") == my_pid:
                    death_minutes.append(round(minute, 1))
                    pos = e.get("position", {})
                    deaths.append(DeathEvent(minute=round(minute, 1),
                                             x=pos.get("x", 0), y=pos.get("y", 0)))
                if e.get("killerId") == my_pid or my_pid in e.get("assistingParticipantIds", []):
                    takedown_minutes.append(round(minute, 1))
            elif et == "ELITE_MONSTER_KILL" and e.get("monsterType") == "RIFTHERALD":
                if e.get("killerId") == my_pid or my_pid in e.get("assistingParticipantIds", []):
                    herald += 1

    return JungleMetrics(
        champion=me["championName"],
        position=me["teamPosition"],
        win=me["win"],
        duration_min=round(duration_min, 1),
        cs_at_10=_cs_at(timeline, my_pid, 10),
        cs_at_15=_cs_at(timeline, my_pid, 15),
        cs_per_min=round(total_cs / duration_min, 2) if duration_min else None,
        jungle_cs_before_10=_round1(ch.get("jungleCsBefore10Minutes")),
        gold_diff_vs_enemy_jgl_at_15=gold_diff_15,
        kills=me["kills"],
        deaths=me["deaths"],
        assists=me["assists"],
        kill_participation=round(ch["killParticipation"], 3) if "killParticipation" in ch else None,
        takedown_minutes=takedown_minutes,
        dragon_takedowns=ch.get("dragonTakedowns", 0),
        baron_takedowns=ch.get("baronTakedowns", 0),
        rift_herald_takedowns=herald,
        epic_kills_within_30s_of_spawn=ch.get("epicMonsterKillsWithin30SecondsOfSpawn", 0),
        epic_monster_steals=ch.get("epicMonsterSteals", 0),
        enemy_jungle_cs=ch.get("enemyJungleMonsterKills"),
        counter_jungle_diff=_round1(ch.get("moreEnemyJungleThanOpponent")),
        vision_score=me.get("visionScore"),
        control_wards_placed=ch.get("controlWardsPlaced"),
        wards_placed=me.get("wardsPlaced"),
        wards_killed=me.get("wardsKilled"),
        death_minutes=death_minutes,
        death_positions=deaths,
    )
