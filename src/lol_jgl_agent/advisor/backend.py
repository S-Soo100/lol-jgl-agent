"""조언 생성 백엔드 (교체 가능한 인터페이스).

- SubscriptionAdvisor: 구독 Claude(Claude Code CLI, `claude -p`) 호출.  ← MVP 기본
- ApiAdvisor:          anthropic SDK + API 키.  (배포용, 추후)

두 백엔드 모두 동일한 generate_advice(metrics_json) -> str 시그니처를 갖는다.
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
from abc import ABC, abstractmethod

from ..config import Settings
from .prompt import SYSTEM_PROMPT, build_user_prompt


class AdvisorError(RuntimeError):
    """조언 생성 실패."""


class Advisor(ABC):
    @abstractmethod
    def generate_advice(self, metrics_json: str) -> str:
        """지표 JSON -> 자연어 조언."""


def find_claude_cli(explicit: str | None = None) -> str | None:
    """claude CLI 실행 파일 경로를 찾는다.

    우선순위: 명시 경로 > PATH > 데스크톱 번들 CLI(%APPDATA%\\Claude\\claude-code\\*).
    """
    if explicit and os.path.exists(explicit):
        return explicit
    on_path = shutil.which("claude")
    if on_path:
        return on_path
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        matches = glob.glob(os.path.join(appdata, "Claude", "claude-code", "*", "claude.exe"))
        if matches:
            # 버전 폴더명(예: 2.1.197) 기준 최신 선택
            def ver(p: str) -> tuple:
                name = os.path.basename(os.path.dirname(p))
                parts = []
                for x in name.split("."):
                    parts.append(int(x) if x.isdigit() else 0)
                return tuple(parts)

            return max(matches, key=ver)
    return None


class SubscriptionAdvisor(Advisor):
    """구독 중인 Claude를 `claude -p`(headless)로 호출.

    별도 API 키 없이 Claude 구독 인증을 사용한다. 헤드리스 인증은
    `claude setup-token`(장기 토큰) 또는 `claude` 대화형 `/login`으로 1회 설정.
    """

    def __init__(self, settings: Settings) -> None:
        self.cli = find_claude_cli(settings.claude_cli_path)
        if not self.cli:
            raise AdvisorError(
                "claude CLI를 찾을 수 없습니다. PATH에 추가하거나 .env의 CLAUDE_CLI_PATH를 설정하세요."
            )

    def generate_advice(self, metrics_json: str) -> str:
        prompt = build_user_prompt(metrics_json)
        result = subprocess.run(
            [self.cli, "-p", prompt, "--append-system-prompt", SYSTEM_PROMPT,
             "--output-format", "text"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        out = (result.stdout or "").strip()
        if result.returncode != 0 or not out:
            hint = ""
            if "login" in (out + (result.stderr or "")).lower():
                hint = ("\n  → claude CLI가 로그인되어 있지 않습니다. 터미널에서 "
                        "`claude setup-token`(또는 `claude` 실행 후 /login)으로 구독 인증을 1회 설정하세요.")
            raise AdvisorError(f"claude CLI 조언 생성 실패: {out or result.stderr.strip()}{hint}")
        return out


class ApiAdvisor(Advisor):
    """anthropic API 키를 사용하는 백엔드 (추후 배포용)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_advice(self, metrics_json: str) -> str:
        raise NotImplementedError("추후: anthropic SDK 백엔드 구현 예정")


def make_advisor(settings: Settings) -> Advisor:
    """설정에 따라 백엔드 선택."""
    if settings.advisor_backend == "api":
        return ApiAdvisor(settings)
    return SubscriptionAdvisor(settings)
