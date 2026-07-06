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
- 조언 백엔드: **구독 Claude(`claude -p`)** 기본. API 키 백엔드는 추후 교체용.

## 개발 명령어
```powershell
.\.venv\Scripts\Activate.ps1        # 가상환경 (Python 3.12, .venv)
pip install -e ".[dev]"             # 개발 설치
pytest                              # 테스트
lol-jgl-agent --riot-id "이름#KR1"  # 실행
```
- 파이썬은 반드시 `.venv`의 것을 사용. 전역 `python`은 MS Store 스텁이라 동작 안 함.
- 비밀키는 `.env` (git 제외). 예시는 `.env.example`.

## 구조
- `src/lol_jgl_agent/config.py` — 설정/상수 (동작함)
- `riot/` — Riot API 클라이언트·모델 (M1)
- `analysis/` — 정글 지표 계산: pathing·jungle·benchmarks (M2)
- `advisor/` — 조언 생성: prompt·backend (backend 구독CLI는 구현됨)
- `report/renderer.py` — 마크다운 리포트 (M3)
- `cli.py` — 진입점 (동작함)

## 마일스톤
M0 세팅 ✅ → M1 데이터수집 → M2 지표엔진 → M3 조언+리포트 → M4 도그푸딩

## 작업 원칙
- 전역 스킬 **karpathy-guidelines**를 따른다: 가정은 명시하고, 최소 코드로, 외과적 변경, 검증 가능한 목표.
- 스캐폴딩의 `NotImplementedError` 스텁은 해당 마일스톤에서 구현. 임의로 앞서 구현하지 말 것.
- Riot 응답은 `.cache/`에 저장해 rate limit 절약 (경기 데이터는 불변).
