# lol-jgl-agent

리그오브레전드 경기를 플레이한 후, 경기 데이터를 분석해
**정글러에게 맞춤형 피드백과 조언**을 제공하는 개인 코칭 도구.

- 플랫폼: Windows 10+
- 언어: Python 3.11+
- 조언 생성: 구독 Claude(Claude Code CLI) → 추후 API 교체 가능

자세한 내용은 [기획서.md](기획서.md), [DESIGN.md](DESIGN.md) 참조.

## 개발 환경 세팅

```powershell
# 1) 가상환경 생성 & 활성화
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) 개발 모드로 설치
pip install -e ".[dev]"

# 3) 환경변수 설정
copy .env.example .env
#   -> .env 를 열어 RIOT_API_KEY, DEFAULT_RIOT_ID 입력

# 4) 수집 — 최근 랭크 N판 지표를 누적
lol-jgl-agent --count 5            # 최근 5판 → reports/history.json 누적
lol-jgl-agent --count 1 --advice   # 최신 1판 claude -p 자동 조언까지(부가)

# 5) 자동 감시 — 켜두면 새 경기를 자동으로 히스토리에 적립
lol-jgl-watch --interval 20

# 6) 테스트
pytest
```

## 메인 워크플로우

1. 랭크 몇 판 하고 온다.
2. `lol-jgl-agent --count N` 으로 최근 N판을 `reports/history.json`에 누적한다
   (또는 `lol-jgl-watch`를 켜두면 자동 적립).
3. **Claude Code에게 "분석해줘"** 라고 하면, 누적된 전체 데이터를 읽어
   새 판 + 그동안의 트렌드를 함께 짚어 채팅으로 피드백한다.

## 진행 상태 (마일스톤)

- [x] **M0** — 환경/저장소 세팅, 프로젝트 스캐폴딩
- [x] **M1** — Riot API 데이터 수집 (Match + Timeline)
- [x] **M2** — 정글 지표 계산 엔진
- [x] **M3** — 조언 생성 + 마크다운 리포트 (조언은 claude CLI 인증 필요)
- [x] **자동 감시 (Level 1 폴링)** — `lol-jgl-watch`로 새 경기 자동 감지·리포트
- [ ] **M4** — 실경기 도그푸딩
- [ ] **자동 감시 Level 2/3** — LCU 연동으로 종료 즉시 감지

## 조언 생성 인증 (1회)

조언은 구독 Claude(claude CLI)로 생성한다. 헤드리스 인증을 1회 설정해야 한다:
```powershell
& "$env:APPDATA\Claude\claude-code\<버전>\claude.exe" setup-token
```
설정 후 `lol-jgl-agent` 실행 시 조언이 리포트에 포함된다. 미인증이면 지표 리포트만 저장된다(`--no-advice`와 동일).

## 구조

```
src/lol_jgl_agent/
  config.py        # 환경설정 / 상수
  riot/            # Riot API 클라이언트 & 모델
  analysis/        # 정글 지표 계산 (pathing/jungle/benchmarks)
  advisor/         # 조언 생성 (prompt + backend)
  report/          # 리포트 렌더링
  cli.py           # 진입점
```
