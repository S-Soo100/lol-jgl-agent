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


@dataclass
class Phase:
    """한 게임의 초반/후반 역할 분류 + 정석 포인터."""

    name: str      # "초반 (≤15분)" / "후반 (25분+)"
    severity: str  # good|warn|bad|info
    role: str      # "말림 (갱형)" 등
    stats: str     # 핵심 지표 한 줄
    tip: str = ""  # "정석: ... → [03]"


def _signed(v) -> str:
    if v is None:
        return "-"
    return f"+{v}" if v > 0 else str(v)


def phase_breakdown(rec: dict) -> list[Phase]:
    """초반(≤15분)·후반(25분+) 역할을 지표로 결정론 분류. [early, late] 반환.

    맥락 있는 "이 판은 이렇게 했어야" 코칭은 채팅(Tier 2)의 몫이고,
    여기서는 지표로 판별 가능한 역할 + knowledge/principles 포인터만 준다.
    """
    dur = rec.get("duration_min") or 0.0
    dmins = rec.get("death_minutes") or []
    tdmins = rec.get("takedown_minutes") or []
    gd15 = rec.get("gold_diff_vs_enemy_jgl_at_15")
    cs10 = rec.get("cs_at_10")
    won = bool(rec.get("win"))
    baron = rec.get("baron_takedowns", 0)

    # --- 초반 (≤15분) ---
    early_d = [t for t in dmins if t < EARLY_WINDOW_MIN]
    td15 = [t for t in tdmins if t < 15]
    style = "갱형" if len(td15) >= 5 else ("파밍형" if (cs10 or 0) >= 55 else "")
    suffix = f" ({style})" if style else ""
    e_stats = (f"CS@10 {cs10 if cs10 is not None else '-'} · "
               f"초반 데스 {len(early_d)} · 15분 골드 {_signed(gd15)}")
    if len(early_d) >= EARLY_DEATH_BAD or (gd15 is not None and gd15 <= -1500):
        early = Phase("초반 (≤15분)", "bad" if len(early_d) >= EARLY_DEATH_BAD else "warn",
                      "말림" + suffix, e_stats,
                      "정석: 밀리면 파밍·시야로 버티고 무리한 교전 금지 → [03]")
    elif len(early_d) <= 1 and (gd15 is None or gd15 >= 0):
        early = Phase("초반 (≤15분)", "good", "안정" + suffix, e_stats,
                      "정석: 좋은 초반 — 리드는 오브젝트로 환전 → [04]")
    else:
        early = Phase("초반 (≤15분)", "warn", "기복" + suffix, e_stats,
                      "정석: 6렙 전 무리한 갱 자제, 각 없으면 파밍 → [01][02]")

    # --- 후반 (25분+) ---
    if dur <= 25:
        late = Phase("후반 (25분+)", "good" if won else "info",
                     "빠른 종료" if won else "단기전", f"{dur}분 종료",
                     "정석: 리드 빠른 환전 성공 → [04]" if won else "")
    else:
        late_d = [t for t in dmins if t >= 25]
        l_stats = f"바론 {baron} · 25분+ 데스 {len(late_d)} · {dur}분"
        if gd15 is not None and gd15 >= BIG_LEAD_GOLD and not won:
            late = Phase("후반 (25분+)", "bad", "리드 못 굴림", l_stats,
                         "정석: 15~25분 타워를 목표로 닫기 → [04]")
        elif len(late_d) >= 3:
            late = Phase("후반 (25분+)", "warn", "후반 짤림", l_stats,
                         "정석: 25분+ '사냥꾼→문지기', 혼자 짤리지 말 것 → [03]")
        else:
            late = Phase("후반 (25분+)", "good" if won else "info", "무난", l_stats, "")

    return [early, late]


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
