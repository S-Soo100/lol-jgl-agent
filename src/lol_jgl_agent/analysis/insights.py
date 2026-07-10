"""규칙 기반 자동 분석 (LLM 없이) — Tier 1 피드백.

`history.json`의 경기 레코드(dict)를 입력받아, 검증된 코칭 휴리스틱을
결정론적 규칙으로 적용해 발견(Finding) 목록을 낸다. 정량 패턴만 잡으며,
"왜 한타를 졌나" 같은 정성/맥락 코칭은 채팅 피드백(Tier 2)의 몫이다.

근거(2026-07, 90~100판 + 도그푸딩 세션):
- 승패 1순위 = 데스, 2순위 = 드래곤. 파밍·카정·골드차는 함정 지표.
- 최대 누수였던 "초반 과욕"은 교정됨 → 현재 주 과제는 "리드 환전/끝낼 각".
- 지는 판일수록 킬관여↑ = 불리할 때 과욕. 물몸 딜러가 이 성향을 처벌.
"""
from __future__ import annotations

from dataclasses import dataclass

# --- 기준값 (처방전/프로파일에서) -------------------------------------------
DEATH_GOAL = 5              # 판당 데스 목표 (≤5)
EARLY_WINDOW_MIN = 10.0     # "초반" 정의 (분)
EARLY_DEATH_WARN = 2        # 초반 데스 경고 하한
EARLY_DEATH_BAD = 3         # 초반 데스 심각 하한
DRAGON_GOAL = 2             # 판당 드래곤 목표 (≥2)
BIG_LEAD_GOLD = 1500        # 상대 정글러 대비 15분 "큰 리드" 기준
LONG_GAME_MIN = 30.0        # 장기전 기준 (환전 실패 판정용)
FAST_CLOSE_MIN = 28.0       # 빠른 종료 기준 (환전 성공 판정용)
FORCING_KP = 0.60          # 밀리는데 이 이상 킬관여 = 과욕 신호
SHORT_GAME_MIN = 15.0       # 탈주/조기항복 등 단축 경기 기준

# 챔프 적합성 (100판 표본): 물몸 딜러 = 과욕 처벌, 단단/컴포트 = 과욕 용서
SQUISHY_CARRIES = {"Naafiri", "Nocturne", "Graves"}
DURABLE_PICKS = {"JarvanIV", "Vi", "LeeSin", "MonkeyKing", "Sylas"}

SEVERITY_MARK = {"good": "🟢", "warn": "🟡", "bad": "🔴", "info": "⚪"}
_SEVERITY_ORDER = {"bad": 0, "warn": 1, "good": 2, "info": 3}


@dataclass
class Finding:
    """규칙 하나가 낸 발견. severity: good|warn|bad|info."""

    severity: str
    category: str
    title: str
    detail: str = ""


def analyze_game(rec: dict) -> list[Finding]:
    """경기 레코드 하나를 규칙으로 분석해 발견 목록을 반환."""
    champ = rec.get("champion", "?")
    win = bool(rec.get("win", False))
    dur = rec.get("duration_min") or 0.0
    deaths = rec.get("deaths", 0)
    dmins = rec.get("death_minutes") or []
    dragons = rec.get("dragon_takedowns", 0)
    gd = rec.get("gold_diff_vs_enemy_jgl_at_15")
    kp = rec.get("kill_participation")
    baron = rec.get("baron_takedowns", 0)
    short = dur < SHORT_GAME_MIN

    f: list[Finding] = []

    if short:
        f.append(Finding("info", "short_game", f"단축 경기 {dur}분",
                         "탈주/조기항복 가능 — 지표 해석 주의"))

    # 데스 — 승패 1순위 레버
    if deaths <= DEATH_GOAL:
        f.append(Finding("good", "deaths", f"데스 {deaths} — 목표 달성",
                         "승패 1순위 레버(≤5)"))
    elif deaths <= 7:
        f.append(Finding("warn", "deaths", f"데스 {deaths} — 목표(≤5) 초과",
                         "승패 1순위 레버"))
    else:
        f.append(Finding("bad", "deaths", f"데스 {deaths} — 과다",
                         "승패 1순위 레버, 큰 누수"))

    # 초반 과욕 — 과거 최대 누수
    early = [t for t in dmins if t < EARLY_WINDOW_MIN]
    if len(early) >= EARLY_DEATH_BAD:
        f.append(Finding("bad", "early_aggression", f"초반 10분 데스 {len(early)}개",
                         "과욕 경고 — " + ", ".join(f"{t}분" for t in early)))
    elif len(early) == EARLY_DEATH_WARN:
        f.append(Finding("warn", "early_aggression", "초반 10분 데스 2개",
                         "초반 안정 주의"))
    elif not early and dur >= 12:
        f.append(Finding("good", "early_aggression", "초반 10분 무사",
                         "과욕 억제 성공"))

    # 드래곤 — 승패 2순위 레버
    if dragons >= DRAGON_GOAL:
        f.append(Finding("good", "dragons", f"드래곤 {dragons} — 목표 달성",
                         "승패 2순위 레버(≥2)"))
    else:
        f.append(Finding("warn", "dragons", f"드래곤 {dragons} — 목표(≥2) 미달",
                         "승패 2순위 레버"))

    # 리드 환전 — 현재 주 과제
    if not short and gd is not None:
        if gd >= BIG_LEAD_GOLD and not win and dur > LONG_GAME_MIN:
            detail = f"15분 +{gd}골드 → {dur}분 장기전 패"
            if baron == 0:
                detail += " · 바론 0개(오브젝트 미환전)"
            f.append(Finding("bad", "lead_conversion", "리드 환전 실패", detail))
        elif gd >= BIG_LEAD_GOLD and win and dur <= FAST_CLOSE_MIN:
            f.append(Finding("good", "lead_conversion", "리드 빠른 환전",
                             f"15분 +{gd}골드 → {dur}분 종료"))

    # 불리할 때 과욕 — 프로파일 시그니처
    if (not short and not win and gd is not None and gd < 0
            and kp is not None and kp >= FORCING_KP):
        f.append(Finding("warn", "forcing_behind", f"밀리는데 킬관여 {round(kp * 100)}%",
                         f"골드 {gd} 밀림 — 불리할 때 과욕 신호"))

    # 함정 지표 밀려도 승리 — 재확인/격려
    if not short and win and gd is not None and gd < 0:
        f.append(Finding("good", "trap_metric", f"골드 {gd} 밀렸지만 승리",
                         "함정 지표 무관 — 데스·드래곤·안던지기가 승리 레버"))

    # 챔프 적합성
    if champ in SQUISHY_CARRIES:
        f.append(Finding("warn", "champ_fit", f"{champ} — 물몸 딜러",
                         "과욕 성향 처벌 챔프(표본상 저승률)"))
    elif champ in DURABLE_PICKS:
        f.append(Finding("info", "champ_fit", f"{champ} — 단단한 픽/컴포트",
                         "과욕 용서 챔프"))

    return f


def summarize_recent(records: list[dict], n: int = 5) -> list[Finding]:
    """최근 n판(히스토리는 최신순 정렬)에 대한 가벼운 추세 발견."""
    recent = records[:n]
    if not recent:
        return []

    f: list[Finding] = []
    wins = sum(1 for r in recent if r.get("win"))
    f.append(Finding("info", "record",
                     f"최근 {len(recent)}판 {wins}승 {len(recent) - wins}패", ""))

    if all(r.get("dragon_takedowns", 0) >= DRAGON_GOAL for r in recent):
        f.append(Finding("good", "dragons",
                         f"최근 {len(recent)}판 드래곤 목표 연속 달성", ""))

    recurring = sum(
        1 for r in recent
        if len([t for t in (r.get("death_minutes") or []) if t < EARLY_WINDOW_MIN]) >= EARLY_DEATH_BAD
    )
    if recurring:
        f.append(Finding("warn", "early_aggression",
                         f"최근 {len(recent)}판 중 {recurring}판 초반 과욕", "초반 안정 유지 필요"))

    return f


def render_findings(findings: list[Finding]) -> str:
    """발견 목록을 심각도순(bad→warn→good→info) 텍스트로 렌더링."""
    lines = []
    for fd in sorted(findings, key=lambda x: _SEVERITY_ORDER.get(x.severity, 9)):
        mark = SEVERITY_MARK.get(fd.severity, "·")
        line = f"{mark} {fd.title}"
        if fd.detail:
            line += f" — {fd.detail}"
        lines.append(line)
    return "\n".join(lines)
