"""지표 + 조언 -> 마크다운 리포트."""
from __future__ import annotations

from ..analysis.benchmarks import grade
from ..analysis.jungle import JungleMetrics

_GRADE_MARK = {"good": "🟢", "ok": "🟡", "bad": "🔴", "unknown": "⚪"}


def _g(metric: str, value: float | None) -> str:
    return _GRADE_MARK[grade(metric, value)]


def _signed(v: float | None) -> str:
    if v is None:
        return "-"
    return f"+{v}" if v > 0 else str(v)


def _pct(v: float | None) -> str:
    return f"{v*100:.0f}%" if v is not None else "-"


def render_markdown(m: JungleMetrics, advice: str | None, *, match_id: str, riot_id: str) -> str:
    """정글 지표와 조언을 마크다운 리포트 문자열로 렌더링."""
    result = "승리 ✅" if m.win else "패배 ❌"
    lines: list[str] = []
    lines.append(f"# 정글 리포트 — {m.champion}")
    lines.append("")
    lines.append(f"**{riot_id}** · {m.position} · {result} · {m.duration_min}분 · `{match_id}`")
    lines.append("")
    lines.append(f"KDA **{m.kills}/{m.deaths}/{m.assists}** · 킬관여율 **{_pct(m.kill_participation)}**")
    lines.append("")

    lines.append("## 성장")
    lines.append("| 지표 | 값 | |")
    lines.append("|---|---|---|")
    lines.append(f"| CS@10 | {m.cs_at_10} | {_g('cs_at_10', m.cs_at_10)} |")
    lines.append(f"| CS@15 | {m.cs_at_15} | {_g('cs_at_15', m.cs_at_15)} |")
    lines.append(f"| 분당 CS | {m.cs_per_min} | {_g('cs_per_min', m.cs_per_min)} |")
    lines.append(f"| 10분 전 정글 CS | {m.jungle_cs_before_10} | |")
    lines.append(f"| 상대 정글러 대비 15분 골드차 | {_signed(m.gold_diff_vs_enemy_jgl_at_15)} | |")
    lines.append("")

    lines.append("## 오브젝트 & 카정")
    lines.append(f"- 드래곤 **{m.dragon_takedowns}** {_g('dragon_takedowns', m.dragon_takedowns)}"
                 f" · 전령 **{m.rift_herald_takedowns}** · 바론 **{m.baron_takedowns}**")
    lines.append(f"- 스폰 30초 내 처치 {m.epic_kills_within_30s_of_spawn} · 스틸 {m.epic_monster_steals}")
    lines.append(f"- 적 정글 CS {m.enemy_jungle_cs} · 카정 차이 **{_signed(m.counter_jungle_diff)}**")
    lines.append("")

    lines.append("## 시야")
    lines.append(f"- 시야 점수 **{m.vision_score}** · 제어와드 {m.control_wards_placed}"
                 f" · 설치 {m.wards_placed} · 제거 {m.wards_killed}")
    lines.append("")

    lines.append("## 데스")
    if m.death_minutes:
        lines.append(f"- 총 **{m.deaths}회** {_g('deaths', m.deaths)}: "
                     f"{', '.join(f'{t}분' for t in m.death_minutes)}")
    else:
        lines.append("- 데스 없음 🟢")
    lines.append("")

    lines.append("## 조언")
    lines.append(advice.strip() if advice else "_(조언 생성 안 함 — `--no-advice` 또는 CLI 미인증)_")
    lines.append("")
    return "\n".join(lines)
