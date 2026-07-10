"""history.json → 자체완결 HTML 대시보드 (Tier 1 시각화, 런타임 LLM/외부요청 0).

인라인 SVG로 차트를 그려 오프라인에서 그대로 열린다. 색은 검증된 팔레트를 쓰고
(상태 good/warn/bad, 승/패 카테고리), 값 라벨을 병기해 색 단독 인코딩을 피한다.
규칙 발견은 `analysis/insights.py`를 재사용한다.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

from ..analysis.insights import _SEVERITY_ORDER, DRAGON_GOAL, analyze_game

MAX_TREND_GAMES = 16  # 추세 차트에 표시할 최근 경기 수
DEATH_GOAL = 5

# 상태색(고정) + 승/패 카테고리(테마별). 팔레트 references/palette.md 준거.
_STYLE = """
:root{
  --surface:#fcfcfb; --page:#f9f9f7; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
  --grid:#e1e0d9; --baseline:#c3c2b7; --border:rgba(11,11,11,.10);
  --good:#0ca30c; --warn:#fab219; --bad:#d03b3b; --win:#2a78d6; --loss:#e34948;
}
@media (prefers-color-scheme:dark){:root{
  --surface:#1a1a19; --page:#0d0d0d; --ink:#fff; --ink2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --baseline:#383835; --border:rgba(255,255,255,.10);
  --win:#3987e5; --loss:#e66767;
}}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5}
.wrap{max-width:920px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:22px;margin:0 0 2px}
.sub{color:var(--ink2);font-size:13px;margin-bottom:24px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;
  padding:18px 20px;margin-bottom:18px}
.card h2{font-size:15px;margin:0 0 14px;color:var(--ink)}
.tiles{display:flex;flex-wrap:wrap;gap:12px}
.tile{flex:1 1 140px;background:var(--surface);border:1px solid var(--border);
  border-radius:12px;padding:16px 18px}
.tile .n{font-size:30px;font-weight:700;letter-spacing:-.5px}
.tile .l{font-size:12px;color:var(--ink2);margin-top:2px}
.chart{overflow-x:auto}
svg{display:block;max-width:100%;height:auto}
.v{fill:var(--ink2);font-size:10px;font-variant-numeric:tabular-nums}
.x{fill:var(--muted);font-size:9px}
.goal{stroke:var(--baseline);stroke-width:1;stroke-dasharray:3 3}
.goal-lbl{fill:var(--muted);font-size:9px}
.baseline{stroke:var(--baseline);stroke-width:1}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:right;padding:7px 8px;border-bottom:1px solid var(--grid);
  font-variant-numeric:tabular-nums}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;font-size:11px}
.legend{display:flex;gap:16px;font-size:12px;color:var(--ink2);margin-bottom:8px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
.finds{list-style:none;padding:0;margin:0;font-size:13px}
.finds li{padding:5px 0;border-bottom:1px solid var(--grid)}
.finds li:last-child{border:0}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;vertical-align:middle}
.d-good{background:var(--good)}.d-warn{background:var(--warn)}
.d-bad{background:var(--bad)}.d-info{background:var(--muted)}
.det{color:var(--ink2)}
.empty{color:var(--ink2);text-align:center;padding:40px}
"""

_SEV_CLASS = {"good": "d-good", "warn": "d-warn", "bad": "d-bad", "info": "d-info"}


def _death_role(deaths: int) -> str:
    return "good" if deaths <= DEATH_GOAL else ("warn" if deaths <= 7 else "bad")


def _bars(items: list[tuple[str, float, str, str]], *, goal: float | None,
          goal_text: str = "") -> str:
    """비음수 세로 막대. items=(x라벨, 값, 색역할, 값라벨). 선택적 목표선."""
    n = len(items)
    if n == 0:
        return ""
    plot_h, pad_top, pad_bot, bar_w, gap, left = 150, 18, 22, 26, 12, 8
    width = left * 2 + n * bar_w + (n - 1) * gap
    height = plot_h + pad_top + pad_bot
    maxv = max([v for _, v, _, _ in items] + ([goal] if goal else []) + [1])

    def y(v: float) -> float:
        return pad_top + plot_h * (1 - v / maxv)

    p = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    if goal is not None:
        gy = y(goal)
        p.append(f'<line class="goal" x1="{left}" x2="{width - left}" y1="{gy:.1f}" y2="{gy:.1f}"/>')
        if goal_text:
            p.append(f'<text class="goal-lbl" x="{width - left}" y="{gy - 3:.1f}" text-anchor="end">{goal_text}</text>')
    x = left
    for xl, v, role, vt in items:
        bh = plot_h * (v / maxv)
        by = pad_top + plot_h - bh
        p.append(f'<rect x="{x}" y="{by:.1f}" width="{bar_w}" height="{bh:.1f}" rx="3" fill="var(--{role})"/>')
        p.append(f'<text class="v" x="{x + bar_w / 2:.1f}" y="{by - 4:.1f}" text-anchor="middle">{vt}</text>')
        p.append(f'<text class="x" x="{x + bar_w / 2:.1f}" y="{height - 8}" text-anchor="middle">{escape(xl)}</text>')
        x += bar_w + gap
    p.append("</svg>")
    return "".join(p)


def _signed_bars(items: list[tuple[str, float, str, str]]) -> str:
    """0 기준 세로 막대(양수 위/음수 아래). items=(x라벨, 부호값, 색역할, 값라벨)."""
    n = len(items)
    if n == 0:
        return ""
    plot_h, pad_top, pad_bot, bar_w, gap, left = 150, 16, 26, 26, 12, 8
    width = left * 2 + n * bar_w + (n - 1) * gap
    height = plot_h + pad_top + pad_bot
    maxabs = max([abs(v) for _, v, _, _ in items] + [1])
    zero_y = pad_top + plot_h / 2
    half = plot_h / 2
    p = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    p.append(f'<line class="baseline" x1="{left}" x2="{width - left}" y1="{zero_y:.1f}" y2="{zero_y:.1f}"/>')
    x = left
    for xl, v, role, vt in items:
        bh = half * (abs(v) / maxabs)
        by = zero_y - bh if v >= 0 else zero_y
        p.append(f'<rect x="{x}" y="{by:.1f}" width="{bar_w}" height="{bh:.1f}" rx="3" fill="var(--{role})"/>')
        ty = by - 4 if v >= 0 else by + bh + 11
        p.append(f'<text class="v" x="{x + bar_w / 2:.1f}" y="{ty:.1f}" text-anchor="middle">{vt}</text>')
        p.append(f'<text class="x" x="{x + bar_w / 2:.1f}" y="{height - 8}" text-anchor="middle">{escape(xl)}</text>')
        x += bar_w + gap
    p.append("</svg>")
    return "".join(p)


def _tiles(records: list[dict]) -> str:
    n = len(records)
    wins = sum(1 for r in records if r.get("win"))
    wr = round(wins / n * 100) if n else 0
    death_ok = round(sum(1 for r in records if r.get("deaths", 0) <= DEATH_GOAL) / n * 100) if n else 0
    drag_ok = round(sum(1 for r in records if r.get("dragon_takedowns", 0) >= DRAGON_GOAL) / n * 100) if n else 0
    tiles = [
        (f"{wins}승 {n - wins}패", "전적"),
        (f"{wr}%", "승률"),
        (f"{death_ok}%", f"데스 목표 달성 (≤{DEATH_GOAL})"),
        (f"{drag_ok}%", f"드래곤 목표 달성 (≥{DRAGON_GOAL})"),
    ]
    cells = "".join(f'<div class="tile"><div class="n">{escape(v)}</div><div class="l">{escape(l)}</div></div>'
                    for v, l in tiles)
    return f'<div class="tiles">{cells}</div>'


def _champ_table(records: list[dict]) -> str:
    agg: dict[str, dict] = {}
    for r in records:
        c = r.get("champion", "?")
        a = agg.setdefault(c, {"g": 0, "w": 0, "d": 0, "dr": 0})
        a["g"] += 1
        a["w"] += 1 if r.get("win") else 0
        a["d"] += r.get("deaths", 0)
        a["dr"] += r.get("dragon_takedowns", 0)
    rows = []
    for c, a in sorted(agg.items(), key=lambda kv: -kv[1]["g"]):
        wr = round(a["w"] / a["g"] * 100)
        rows.append(
            f"<tr><td>{escape(c)}</td><td>{a['g']}</td><td>{a['w']}</td>"
            f"<td>{wr}%</td><td>{a['d'] / a['g']:.1f}</td><td>{a['dr'] / a['g']:.1f}</td></tr>"
        )
    head = ("<tr><th>챔프</th><th>판</th><th>승</th><th>승률</th>"
            "<th>평균데스</th><th>평균드래곤</th></tr>")
    return f"<table>{head}{''.join(rows)}</table>"


def _findings_list(rec: dict) -> str:
    findings = sorted(analyze_game(rec), key=lambda f: _SEVERITY_ORDER.get(f.severity, 9))
    items = []
    for f in findings:
        cls = _SEV_CLASS.get(f.severity, "d-info")
        det = f' <span class="det">— {escape(f.detail)}</span>' if f.detail else ""
        items.append(f'<li><span class="dot {cls}"></span>{escape(f.title)}{det}</li>')
    return f'<ul class="finds">{"".join(items)}</ul>'


def render_dashboard(records: list[dict], *, riot_id: str = "", subtitle: str = "") -> str:
    """전체 히스토리 레코드 → 자체완결 HTML 문자열."""
    title = f"🐉 정글 대시보드{f' — {escape(riot_id)}' if riot_id else ''}"
    if not records:
        body = '<div class="card"><div class="empty">데이터 없음 — 먼저 <code>lol-jgl-agent --count N</code>으로 수집하세요.</div></div>'
        return _page(title, subtitle, body)

    # 최신순 저장 → 추세는 시간순(왼→오른쪽=과거→최신)
    trend = list(reversed(records[:MAX_TREND_GAMES]))
    death_items = [(str(i + 1), r.get("deaths", 0), _death_role(r.get("deaths", 0)), str(r.get("deaths", 0)))
                   for i, r in enumerate(trend)]
    drag_items = [(str(i + 1), r.get("dragon_takedowns", 0),
                   "good" if r.get("dragon_takedowns", 0) >= DRAGON_GOAL else "warn",
                   str(r.get("dragon_takedowns", 0))) for i, r in enumerate(trend)]
    lead = [(str(i + 1), (r.get("gold_diff_vs_enemy_jgl_at_15") or 0),
             "win" if r.get("win") else "loss",
             f"{(r.get('gold_diff_vs_enemy_jgl_at_15') or 0) / 1000:+.1f}k")
            for i, r in enumerate(trend)]

    note = "" if len(records) <= MAX_TREND_GAMES else f'<div class="sub">추세 차트는 최근 {MAX_TREND_GAMES}판만 표시 (누적 {len(records)}판).</div>'
    legend = ('<div class="legend"><span><i style="background:var(--win)"></i>승</span>'
              '<span><i style="background:var(--loss)"></i>패</span></div>')

    body = (
        f'<div class="card"><h2>요약</h2>{_tiles(records)}</div>'
        f'{note}'
        f'<div class="card"><h2>데스 추세 (승패 1순위 · 목표 ≤{DEATH_GOAL})</h2>'
        f'<div class="chart">{_bars(death_items, goal=DEATH_GOAL, goal_text=f"목표 {DEATH_GOAL}")}</div></div>'
        f'<div class="card"><h2>드래곤 추세 (승패 2순위 · 목표 ≥{DRAGON_GOAL})</h2>'
        f'<div class="chart">{_bars(drag_items, goal=DRAGON_GOAL, goal_text=f"목표 {DRAGON_GOAL}")}</div></div>'
        f'<div class="card"><h2>리드 환전 (15분 상대 정글러 대비 골드차 · 색=승패)</h2>{legend}'
        f'<div class="chart">{_signed_bars(lead)}</div>'
        f'<div class="sub">양수 막대인데 <b>패(빨강)</b> = 리드 못 굴린 판. 낮은 막대라도 <b>승(파랑)</b>이면 잘 굴린 판.</div></div>'
        f'<div class="card"><h2>챔프별 성적</h2>{_champ_table(records)}</div>'
        f'<div class="card"><h2>최신 경기 자동 분석 — {escape(records[0].get("champion", "?"))} '
        f'{"승" if records[0].get("win") else "패"}</h2>{_findings_list(records[0])}</div>'
    )
    return _page(title, subtitle, body)


def write_dashboard(records: list[dict], path: Path, *, riot_id: str = "",
                    subtitle: str = "") -> Path:
    """대시보드 HTML을 파일로 저장하고 경로를 반환."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dashboard(records, riot_id=riot_id, subtitle=subtitle),
                    encoding="utf-8")
    return path


def _page(title: str, subtitle: str, body: str) -> str:
    sub = f'<div class="sub">{escape(subtitle)}</div>' if subtitle else ""
    return (
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title}</title><style>{_STYLE}</style></head>"
        f'<body><div class="wrap"><h1>{title}</h1>{sub}{body}</div></body></html>'
    )
