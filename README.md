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

# 4) 실행 (스켈레톤)
lol-jgl-agent --riot-id "이름#KR1"

# 5) 테스트
pytest
```

## 진행 상태 (마일스톤)

- [x] **M0** — 환경/저장소 세팅, 프로젝트 스캐폴딩
- [ ] **M1** — Riot API 데이터 수집 (Match + Timeline)
- [ ] **M2** — 정글 지표 계산 엔진
- [ ] **M3** — 조언 생성 + 마크다운 리포트
- [ ] **M4** — 실경기 도그푸딩

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
