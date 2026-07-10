# CLAUDE.md — lol-jgl-agent

리그오브레전드 정글러 경기 후 피드백/조언 도구. Claude가 이 프로젝트에서 작업할 때의 컨텍스트.

## 프로젝트 요지
- 게임 종료 후 **최근 랭크 1판**을 Riot API로 받아 정글 지표 분석 → 간결한 조언 리포트.
- 기획: `기획서.md` / 설계: `DESIGN.md` (변경 시 함께 업데이트).

## 확정된 방향 (바꾸려면 먼저 논의)
- 언어: **Python 3.11+**, 플랫폼: **Windows 전용**.
- 분석 대상: **소환사의 협곡 랭크만** (queue 420/440). 일반·칼바람 제외.
- 분석 범위: **최근 1판** (N판 추세는 2단계).
- 리포트 톤: **간결 요약** (핵심 지표 + 실행 가능한 조언, 군더더기 X).

## 핵심 워크플로우 (중요)
- 도구는 **지표 수집기**다. 사용자가 몇 판 하고 와서 "분석해줘" 하면:
  1. `lol-jgl-agent --count N` 으로 최근 N판 지표를 `reports/history.json`에 **누적**(match_id 중복 제거).
  2. **Claude Code(나)가 `reports/history.json` 전체를 읽고** 새 판 + 그동안 쌓인 데이터를 함께 보고 **채팅으로** 피드백. 여러 판 걸친 반복 습관을 짚는 게 핵심.
- `claude -p` 자동 조언은 `--advice` 옵션으로만(부가). 메인은 채팅 피드백이라 OAuth 토큰 의존을 피한다.
- 워처(`lol-jgl-watch`)는 새 경기를 자동 감지해 history에 조용히 적립만 한다.

## 피드백 루프 (전략 → 플레이 → 리뷰)
- **전략 처방전**: `reports/strategy_<날짜>.md` — 세션 전에 목표(측정 가능)·추천 챔프·Do/Don't를 데이터 기반으로 처방.
- **리뷰**: 세션 후 사용자가 "리뷰해줘" 하면, 가장 최근 `reports/strategy_*.md`의 목표와 새 경기 실제 지표를 비교해 달성 여부를 피드백한다.
- 이 사용자의 핵심 레버·추천 챔프는 메모리 `lol-jgl-player-profile` 참고 (데스·드래곤이 승패, 자르반/비가 고승률).

## 개발 명령어
```powershell
.\.venv\Scripts\Activate.ps1        # 가상환경 (Python 3.12, .venv)
pip install -e ".[dev]"             # 개발 설치
pytest                              # 테스트
lol-jgl-agent --count 5             # 최근 5판 수집 → history.json 누적
lol-jgl-watch                       # 백그라운드 자동 적립
```
- 파이썬은 반드시 `.venv`의 것을 사용. 전역 `python`은 MS Store 스텁이라 동작 안 함.
- 비밀키는 `.env` (git 제외). 예시는 `.env.example`.

## 구조
- `src/lol_jgl_agent/config.py` — 설정/상수
- `riot/` — Riot API 클라이언트·모델
- `analysis/` — 정글 지표 계산: pathing·jungle·benchmarks·**insights**(규칙 기반 자동 분석, LLM 없음)
- `pipeline.py` — 수집→지표(→조언) 로직 (CLI/워처 공용)
- `history.py` — 지표 누적 저장소 (reports/history.json)
- `advisor/` — `--advice` 옵션용 claude -p 조언 (부가)
- `report/renderer.py` — `--advice` 시 마크다운 리포트
- `cli.py` — 수집 진입점(`--insights`로 규칙 분석 출력) · `watch.py` — 자동 적립 워처

## 2단계 피드백 구조
- **Tier 1 (LLM 없음):** `analysis/insights.py` 규칙 엔진 — 검증된 코칭(데스·초반과욕·드래곤·리드환전·불리할때과욕·챔프적합성·함정지표)을 결정론 규칙으로 적용. `--insights`로 즉시 출력. 정량 패턴만.
- **Tier 2 (채팅):** Claude Code가 history 읽고 정성·맥락 코칭. insights의 상위 계층.
- 로드맵: ②룰엔진(완료) → ③HTML 대시보드(insights+history 시각화, LLM 0) → ①유튜브 지식(knowledge/, 룰·채팅 강화).

## 마일스톤
M0 세팅 ✅ → M1 데이터수집 → M2 지표엔진 → M3 조언+리포트 → M4 도그푸딩 → **M5 규칙 엔진(insights) ✅** → M6 대시보드 → M7 지식베이스

## 작업 원칙
- 전역 스킬 **karpathy-guidelines**를 따른다: 가정은 명시하고, 최소 코드로, 외과적 변경, 검증 가능한 목표.
- 스캐폴딩의 `NotImplementedError` 스텁은 해당 마일스톤에서 구현. 임의로 앞서 구현하지 말 것.
- Riot 응답은 `.cache/`에 저장해 rate limit 절약 (경기 데이터는 불변).
