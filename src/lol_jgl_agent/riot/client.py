"""Riot API 클라이언트 (Account / Match / Timeline).

경기 데이터(Match/Timeline)는 종료 후 불변이므로 `.cache/matches/`에 저장해
반복 분석 시 재요청하지 않는다. dev 키의 낮은 rate limit을 고려해 429/5xx는 재시도한다.

지역 라우팅: Account-V1과 Match-V5는 모두 regional 라우팅(예: KR -> asia)을 쓴다.
"""
from __future__ import annotations

import json
import time
from urllib.parse import quote

import httpx

from ..config import CACHE_DIR, Settings


class RiotApiError(RuntimeError):
    """Riot API 호출 실패."""


class RiotClient:
    """Riot API 호출 래퍼.

    with RiotClient(settings) as riot:
        puuid = riot.puuid_by_riot_id("이름#KR1")
        match_id = riot.recent_ranked_match_ids(puuid, count=1)[0]
        match = riot.match(match_id)
        timeline = riot.timeline(match_id)
    """

    def __init__(self, settings: Settings, *, timeout: float = 15.0) -> None:
        if not settings.riot_api_key:
            raise RiotApiError("RIOT_API_KEY가 없습니다. .env를 확인하세요.")
        self.settings = settings
        self._client = httpx.Client(
            headers={"X-Riot-Token": settings.riot_api_key},
            timeout=timeout,
        )
        self._cache = CACHE_DIR / "matches"
        self._cache.mkdir(parents=True, exist_ok=True)

    def __enter__(self) -> "RiotClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # --- 내부 헬퍼 -----------------------------------------------------------

    def _regional(self, path: str) -> str:
        return f"https://{self.settings.region}.api.riotgames.com{path}"

    def _get(self, url: str, params: dict | None = None, *, retries: int = 5) -> dict:
        for attempt in range(retries):
            resp = self._client.get(url, params=params)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:  # rate limit
                wait = int(resp.headers.get("Retry-After", "1"))
                time.sleep(wait)
                continue
            if resp.status_code >= 500:  # 일시적 서버 오류
                time.sleep(1 + attempt)
                continue
            if resp.status_code == 401:
                raise RiotApiError("401 Unauthorized — API 키가 만료/무효합니다 (dev 키는 24h).")
            if resp.status_code == 404:
                raise RiotApiError(f"404 Not Found — {url}")
            raise RiotApiError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        raise RiotApiError(f"재시도 초과({retries}회): {url}")

    def _cached_match_doc(self, match_id: str, timeline: bool) -> dict:
        suffix = "_timeline" if timeline else ""
        path = self._cache / f"{match_id}{suffix}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        sub = "/timeline" if timeline else ""
        data = self._get(self._regional(f"/lol/match/v5/matches/{match_id}{sub}"))
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    # --- 공개 API ------------------------------------------------------------

    def puuid_by_riot_id(self, riot_id: str) -> str:
        """`이름#태그` -> PUUID."""
        if "#" not in riot_id:
            raise RiotApiError(f"Riot ID 형식 오류(이름#태그 필요): {riot_id!r}")
        game_name, tag_line = riot_id.rsplit("#", 1)
        url = self._regional(
            f"/riot/account/v1/accounts/by-riot-id/{quote(game_name)}/{quote(tag_line)}"
        )
        return self._get(url)["puuid"]

    def recent_ranked_match_ids(self, puuid: str, count: int = 1) -> list[str]:
        """최근 랭크(솔로+자유) 매치 ID 목록. 최신순. 100판 초과 시 페이지네이션."""
        url = self._regional(f"/lol/match/v5/matches/by-puuid/{quote(puuid)}/ids")
        ids: list[str] = []
        start = 0
        while len(ids) < count:
            batch = min(100, count - len(ids))
            page = self._get(url, params={"type": "ranked", "start": start, "count": batch})
            if not page:
                break
            ids.extend(page)
            if len(page) < batch:
                break
            start += batch
        return ids[:count]

    def match(self, match_id: str) -> dict:
        """매치 상세(결과) JSON. 로컬 캐시 우선."""
        return self._cached_match_doc(match_id, timeline=False)

    def timeline(self, match_id: str) -> dict:
        """매치 타임라인 JSON. 로컬 캐시 우선."""
        return self._cached_match_doc(match_id, timeline=True)
