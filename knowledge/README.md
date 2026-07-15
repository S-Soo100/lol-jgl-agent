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

## 원리 색인 (principles/)
정글 VOD 코칭 영상에서 증류. 각 파일 끝에 **이 플레이어에게 적용** 절이 있음.
- [01 정글 기본기](principles/01-jungle-fundamentals.md) — 풀캠·1.5캠 루틴·파밍 중 맵읽기·카메라 단축키·렌즈
- [02 맵읽기 & 상대 정글러](principles/02-reading-map-and-enemy-jungler.md) — 우리팀 라인 우선·상대 예측·조우 3분기점·교전형vs성장형·주도권
- [03 유리한 라인 굴리기 & 시팅](principles/03-snowball-and-sitting.md) — 따라오게 하기·시팅(뒤봐주기)·역갱·지는 라인 버리기·턴 반대편
- [04 중반 15~25분 굴리기](principles/04-midgame-closing-15-25.md) — 뇌정지 구간·타워 목표·유리/불리 운영·10분 후 바텀
- [05 시간대별 수싸움 & 선턴](principles/05-timing-and-tempo.md) — 4:00/5:20/6:30 수싸움·XP 스파이크·선턴(템포)·정크무빙 제거
- [06 드래곤 타이밍](principles/06-dragon-timing.md) — 초반=바텀 주도권·후반=미드푸시 먼저·안 되는 용은 포기
- [07 운영 & 덧셈(인원수)](principles/07-operating-and-numbers.md) — 덧셈(인원수)·스타트/첫캠·상대정글 유추·미드1차 사수·유리할때 선푸시+빈쪽 이득
- [08 후반 위치잡기 & 역전](principles/08-late-positioning-and-comeback.md) — **밀었으면 앞 X 옆 O**·쫓지마·유리할땐 일방적 이득·지고있을때 역전·교전형vs성장형 운영

출처 영상: [7BGt25QW2UQ](https://youtu.be/7BGt25QW2UQ) · [3b1QJ6pShBA](https://youtu.be/3b1QJ6pShBA) · [DpZIBN3St9I](https://youtu.be/DpZIBN3St9I)
재생목록 9편: [mnQQC19IUw4](https://youtu.be/mnQQC19IUw4) · [W4HPRvGpnVw](https://youtu.be/W4HPRvGpnVw) · [g5Jb3nPjZSI](https://youtu.be/g5Jb3nPjZSI) · [K-JIjThki7A](https://youtu.be/K-JIjThki7A) · [K1YwnJaxtCs](https://youtu.be/K1YwnJaxtCs) · [wC0Qqwg9GfM](https://youtu.be/wC0Qqwg9GfM) · [fhAQ8WVTaQc](https://youtu.be/fhAQ8WVTaQc) · [V2G1Q-JipLk](https://youtu.be/V2G1Q-JipLk) · [07HM4p8AJL4](https://youtu.be/07HM4p8AJL4)

## 주의
- 자막 있는 영상만. 자동자막은 품질 편차 있어 증류(LLM 1회)가 필요.
- 유튜브가 데이터센터 IP를 차단 → 로컬(가정 IP)에서 추출.
