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
      benchmarks.py         # 티어별 기준값
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

1. **MVP (현재)**: Riot ID 수동 입력 → 경기 후 리포트 + Claude 조언 (CLI/Markdown)
2. **자동화**: LCU 연동으로 게임 종료 자동 감지 → 리포트 자동 생성
3. **시각화**: 동선·데스 히트맵 이미지, 웹 UI(Streamlit/FastAPI)
4. **실시간**: Live Client API 기반 인게임 오버레이 코칭

---

## 6. 주요 의존성 (예정)

- `httpx` — Riot API 비동기 호출
- `pydantic` — 데이터 모델 검증
- `anthropic` — Claude API (조언 생성)
- `jinja2` — 리포트 템플릿
- `matplotlib` / `Pillow` — 히트맵 이미지 (3단계)
- `pytest` — 테스트
