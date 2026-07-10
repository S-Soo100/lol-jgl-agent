# knowledge — 정글 배경지식 베이스 (①)

정글 강의 유튜브를 **정제된 코칭 원리**로 증류해 쌓는 곳. 이 원리는
(a) `analysis/insights.py`의 새 규칙 설계 근거, (b) 채팅 코칭 시 컨텍스트로 쓴다.

## 워크플로우 (추출 → 증류)

1. **추출 — 글로벌 스킬 `youtube-transcript`** (어느 프로젝트에서든 재사용).
   자막을 토큰 효율적인 마크다운으로 뽑아 `knowledge/raw/<video_id>.md`에 저장:
   ```powershell
   # 프로젝트 venv(진짜 파이썬)로 실행. 먼저: pip install -e ".[knowledge]"
   ./.venv/Scripts/python.exe "$env:USERPROFILE\.claude\skills\youtube-transcript\scripts\extract.py" `
     "<유튜브 URL>" --lang ko en --out knowledge/raw/<video_id>.md
   ```
2. **증류 — Claude Code 채팅.** "이 영상 정리해줘" 하면 raw 자막을 읽고
   `knowledge/principles/<주제>.md`로 구조화한다 (예: 동선, 갱 타이밍, 오브젝트 셋업).
   자막 원문은 재배포하지 않고, 정제된 원리만 커밋한다.

## 디렉토리
- `raw/` — 추출한 자막 원문. **gitignore(로컬 전용, 저작권·용량).**
- `principles/` — 증류된 정글 원리(우리 자산). 커밋 대상.

## 주의
- 자막 있는 영상만. 자동자막은 품질 편차 있어 증류(LLM 1회)가 필요.
- 유튜브가 데이터센터 IP를 차단 → 로컬(가정 IP)에서 추출.
