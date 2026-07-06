"""조언 생성 백엔드 (교체 가능한 인터페이스).

- SubscriptionAdvisor: 구독 Claude(Claude Code CLI, `claude -p`) 호출.  ← MVP 기본
- ApiAdvisor:          anthropic SDK + API 키.  (배포용, 추후)

두 백엔드 모두 동일한 generate_advice(metrics_json) -> str 시그니처를 갖는다.
"""
from __future__ import annotations

import shutil
import subprocess
from abc import ABC, abstractmethod

from ..config import Settings
from .prompt import SYSTEM_PROMPT, build_user_prompt


class Advisor(ABC):
    @abstractmethod
    def generate_advice(self, metrics_json: str) -> str:
        """지표 JSON -> 자연어 조언."""


class SubscriptionAdvisor(Advisor):
    """구독 중인 Claude를 `claude -p`(headless)로 호출.

    별도 API 키 없이 Claude Code 구독 인증을 그대로 사용한다.
    claude 실행 파일은 PATH에서 찾거나 settings.claude_cli_path로 지정.
    """

    def __init__(self, settings: Settings) -> None:
        self.cli = settings.claude_cli_path or shutil.which("claude")
        if not self.cli:
            raise RuntimeError(
                "claude CLI를 찾을 수 없습니다. PATH에 추가하거나 "
                ".env의 CLAUDE_CLI_PATH를 설정하세요."
            )

    def generate_advice(self, metrics_json: str) -> str:
        prompt = build_user_prompt(metrics_json)
        result = subprocess.run(
            [self.cli, "-p", prompt, "--append-system-prompt", SYSTEM_PROMPT],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(f"claude CLI 오류: {result.stderr.strip()}")
        return result.stdout.strip()


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
