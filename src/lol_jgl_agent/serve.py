"""로컬 대시보드 서버 — 페이지 안 '업데이트' 버튼으로 수집 → 자동 새로고침.

    lol-jgl-serve                 # 서버 시작 + 브라우저 자동 열기
    lol-jgl-serve --port 8770

정적 파일(--dashboard)과 달리, 이 모드는 페이지에서 클릭 한 번으로 최근 N판을
수집(POST /update)하고 갱신한다. 서버는 127.0.0.1에만 바인딩(로컬 전용).
"""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import history
from .config import Settings
from .pipeline import collect_recent
from .report.dashboard import render_dashboard

UPDATE_PATH = "/update"


def _make_handler(settings: Settings, riot_id: str):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body, ctype: str = "text/html; charset=utf-8") -> None:
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802
            if urlparse(self.path).path in ("/", "/index.html"):
                html = render_dashboard(history.load_history(riot_id), riot_id=riot_id,
                                        subtitle="로컬 서버 · 업데이트 버튼 사용 가능",
                                        update_url=UPDATE_PATH)
                self._send(200, html)
            else:
                self._send(404, "not found", "text/plain; charset=utf-8")

        def do_POST(self):  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != UPDATE_PATH:
                self._send(404, "not found", "text/plain; charset=utf-8")
                return
            count = int((parse_qs(parsed.query).get("count", ["5"])[0]) or 5)
            records, err = collect_recent(settings, riot_id, count)
            if err:
                self._send(200, json.dumps({"ok": False, "error": err}), "application/json")
                return
            added, total, _ = history.merge(records, riot_id)
            self._send(200, json.dumps({"ok": True, "added": added, "total": total}),
                       "application/json")

        def log_message(self, *args):  # 접속 로그 숨김
            pass

    return Handler


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(prog="lol-jgl-serve", description="로컬 대시보드 서버(업데이트 버튼)")
    p.add_argument("--riot-id", help="생략 시 .env의 DEFAULT_RIOT_ID.")
    p.add_argument("--port", type=int, default=8770)
    p.add_argument("--no-open", action="store_true", help="브라우저 자동 열기 안 함")
    args = p.parse_args()

    settings = Settings.load()
    riot_id = args.riot_id or settings.default_riot_id
    if not riot_id:
        print("[!] Riot ID가 없습니다. --riot-id 또는 .env의 DEFAULT_RIOT_ID를 설정하세요.")
        return

    url = f"http://127.0.0.1:{args.port}/"
    server = ThreadingHTTPServer(("127.0.0.1", args.port), _make_handler(settings, riot_id))
    print(f"대시보드 서버: {url}  (Ctrl+C로 종료)")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
