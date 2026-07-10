# lol-jgl-agent — 설계 문서

리그오브레전드 경기를 플레이한 후, 결과와 타임라인 데이터를 분석해
**정글러 관점의 피드백과 조언**을 생성하는 프로젝트.

- 언어: **Python**
- 플랫폼: Windows 10+ (전용)
- MVP: **경기 후 리포트** (게임 종료 후 최근 경기 분석 → 텍스트/이미지 리포트 + LLM 조언)

---

## 1. 데이터 소스

| 소스 | 내용 | MVP 사용 |
|---|---|---|
| Riot API — Match-V5 | 경기 최종 결과 (KDA, CS, 골드, 딜량, 아이템, 룬) | ✅ |
| Riot API — Match Timeline | 60초 단위 챔피언 위치·골드·레벨 + 전체 이벤트 | ✅ (핵심) |
| LCU API | 로컬 클라이언트에서 최근 경기 자동 감지 | ⏳ 2단계 |
| Live Client Data (`:2999`) | 게임 중 실시간 데이터 | ⏳ 실시간 코칭 단계 |
| `.rofl` 리플레이 파일 | 암호화됨 — 파싱 비현실적 | ❌ |

> **핵심 인사이트:** "리플레이를 본다"는 실제로 **Match Timeline API**로 구현한다.
> 60초마다 모든 챔피언의 좌표 + 이벤트를 주므로 정글 동선/갱킹/오브젝트 분석이 가능하다.

### API 키 / 인증
- **Riot 개발용 키**: 24시간마다 갱신, rate limit 낮음 → MVP 개발에 충분 (연결 완료)
- 지역 라우팅: 소환사/매치ID는 `asia` (KR 포함), 플랫폼은 `kr`
- **조언 생성 (LLM)**: MVP는 **구독 중인 Claude(Claude Code CLI, `claude -p`)** 사용
  — 별도 Anthropic API 키 비용 없이 테스트. 추후 배포 시 API 키 백엔드로 교체 가능하도록
  `advisor/backend.py`에서 인터페이스 추상화.

---

## 2. 파이프라인

```
Riot ID (gameName#tagLine) 입력
   ↓ PUUID 조회
최근 매치 ID 목록 → 분석할 경기 선택
   ↓
Match + Timeline 데이터 수집 (+ 로컬 캐시)
   ↓
정글 지표 계산 (동선·갱킹·오브젝트·시야·CS·데스)
   ↓
티어별 벤치마크와 비교 → 강점/약점 도출
   ↓
Claude API: 지표 → 자연어 조언 생성
   ↓
리포트 출력 (Markdown → HTML/이미지 옵션)
```

---

## 3. 정글 특화 지표 (MVP)

- **동선 효율**: 첫 정글 클리어 완료 시각, 풀클리어 여부, 첫 갱 타이밍
- **CS/성장**: CS@10 / CS@15, 분당 CS, 상대 정글러 대비 골드·경험치 격차
- **갱킹**: 라인별 킬/어시스트 관여, 갱 성공률(관여 대비), 시간대별 분포
- **오브젝트**: 드래곤/전령/바론 스폰 30초 전 위치, 오브젝트 참여율, 선점률
- **시야**: 와드 설치/제거 수, 제어와드, 오브젝트 주변 시야 장악
- **데스 분석**: 데스 위치 히트맵, 카정 데스, 데스 타이밍(오브젝트와 연관 여부)
- **팀 비교**: 팀 내 딜량·골드·시야 점유율

각 지표는 티어별 벤치마크(`analysis/benchmarks.py`)와 비교해 색상/등급 부여.

---

## 4. 프로젝트 구조

```
lol-jgl-agent/
  pyproject.toml
  .env.example              # RIOT_API_KEY, ANTHROPIC_API_KEY
  README.md
  DESIGN.md
  src/lol_jgl_agent/
    config.py               # 환경변수, 맵 좌표 상수
    riot/
      client.py             # Riot API 클라이언트 (rate limit, 캐시)
      models.py             # Match / Timeline 데이터 모델
    analysis/
      pathing.py            # 좌표 → 맵 구역 변환, 동선 분석
      jungle.py             # 정글 지표 계산
      benchmarks.py         # 개인 캘리브레이션 기준값 (90판 분포)
      insights.py           # 규칙 기반 자동 분석 (Tier 1, LLM 없음)
    advisor/
      prompt.py             # Claude 프롬프트 템플릿
      backend.py            # 조언 생성 백엔드 (추상 인터페이스)
        # - SubscriptionAdvisor: `claude -p` CLI 호출 (구독 Claude, MVP/테스트)
        # - ApiAdvisor: anthropic SDK + API 키 (추후/배포용)
    report/
      renderer.py           # Markdown/HTML 리포트 렌더링
    cli.py                  # 진입점
  tests/
```

---

## 5. 단계별 로드맵

1. **수집기 + 채팅 피드백 (현재)**: `--count N`으로 지표를 `history.json`에 누적,
   Claude Code 채팅으로 정성 피드백. (§7 참조 — 초기 "LLM 리포트 MVP"에서 피벗)
2. **② 규칙 엔진 (완료)**: `analysis/insights.py` — LLM 없이 검증된 코칭을 자동 적용.
3. **③ 대시보드**: `history.json` + insights → 자체완결 HTML 시각화 (LLM 0).
4. **① 지식베이스**: 정글 강의 유튜브 자막 → 정제 원리 `knowledge/` → 룰·채팅 강화.
5. **자동화/실시간**: LCU 자동 감지, Live Client 오버레이 코칭.

---

## 6. 주요 의존성

- `httpx` — Riot API 호출
- `pydantic` — 데이터 모델 검증
- `python-dotenv` — `.env` 로딩
- `jinja2` — 리포트 템플릿
- `anthropic` — API 백엔드(선택, `--advice` 배포용)
- `matplotlib` / `Pillow` — 히트맵 이미지 (선택)
- `pytest` — 테스트

---

## 7. 피드백 2단계 구조 (2026-07 피벗)

초기 기획은 "지표 → LLM이 리포트 생성"이 MVP였으나, 실사용에서 **도구는 지표
수집기로 두고 피드백은 Claude Code 채팅으로 받는 방식**이 더 강력함을 확인해 피벗했다.
여러 판에 걸친 반복 습관을 짚는 게 코칭의 핵심이고, OAuth 토큰 의존도 피할 수 있다.

```
Layer 0  수집기            Riot API → 정글 지표 → reports/history.json 누적
Layer 1  규칙 엔진 (②)     insights.py: 결정론 규칙 → 발견(Finding) 목록      [LLM 0]
Layer 2  대시보드 (③)      history + insights → 자체완결 HTML 시각화          [LLM 0]
지식     지식베이스 (①)    유튜브 자막 → 정제 원리 → 룰 설계 + 채팅 컨텍스트   [LLM 1회]
Layer 2+ 채팅 코칭          Claude Code가 history 읽고 정성·맥락 피드백        [채팅]
```

| | Tier 1 (LLM 없음) | Tier 2 (채팅) |
|---|---|---|
| 구성 | insights 규칙 + 대시보드 | Claude Code + 지식베이스 |
| 성격 | 즉시·항상, **정량** 패턴 | 깊은·맥락, **정성** 코칭 |
| 예 | "리드 환전 실패(바론0)", "초반 과욕 3데스" | "왜 그 한타를 졌나", 챔프별 운영 |

### 7.1 규칙 엔진 (`insights.py`)
- 입력: `history.json`의 경기 레코드(dict) 하나. 출력: `Finding(severity, category, title, detail)` 목록.
- 규칙(도그푸딩으로 검증된 개인 코칭): 데스(승패 1순위)·초반 과욕·드래곤(2순위)·
  **리드 환전 실패/성공**·불리할 때 과욕·챔프 적합성·함정 지표 무관 승리·단축 경기.
- 임계값은 90~100판 벤치마크 기준(`BIG_LEAD_GOLD=1500`, `DEATH_GOAL=5`, `DRAGON_GOAL=2` 등),
  데이터가 쌓이면 재캘리브레이션.
- CLI: `lol-jgl-agent --count N --insights` (opt-in). `render_findings`가 심각도순 출력.
- **한계:** 정량 패턴만. "왜 한타를 졌나" 같은 정성/맥락은 Tier 2(채팅)의 몫.

### 7.2 대시보드 (③, 예정)
- `history.json` + `insights` 출력 → 정적 HTML 1파일(자체완결, 외부 요청 0).
- 요소: 데스/드래곤 추세, 챔프별 승률, 리드 환전(골드@15 vs 결과·시간), 처방전 목표
  스코어카드, 발견 목록. 런타임 LLM 호출 없이 기본 피드백 제공.

### 7.3 지식베이스 (①, 예정)
- `youtube-transcript-api`로 자막 수집 → Claude가 1회 정제 → `knowledge/*.md` 원리 파일.
- 용도: (a) 새 규칙 설계 근거, (b) 채팅 코칭 시 컨텍스트. 정량 자동적용은 아님.
