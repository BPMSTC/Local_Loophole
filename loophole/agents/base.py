from __future__ import annotations

from typing import Any

from loophole.llm import LLMClient
from loophole.models import SessionState


class BaseAgent:
    def __init__(self, llm: LLMClient, temperature: float = 0.5):
        self.llm = llm
        self.temperature = temperature

    def _build_system_prompt(self, **kwargs: Any) -> str:
        raise NotImplementedError

    def _build_user_message(self, state: SessionState, **kwargs: Any) -> str:
        raise NotImplementedError

    def run(self, state: SessionState, **kwargs: Any) -> str:
        system = self._build_system_prompt(**kwargs)
        user_msg = self._build_user_message(state, **kwargs)
        return self.llm.call(system, user_msg, temperature=self.temperature)

    def repair_output(self, raw_output: str, required_format: str) -> str:
        system = (
            "You are a strict formatter. Reformat the user's content to match the requested "
            "tag structure exactly. Preserve the meaning. Return only the reformatted output."
        )
        user_msg = (
            "Required format:\n"
            f"{required_format}\n\n"
            "Content to reformat:\n"
            f"{raw_output}"
        )
        return self.llm.call(system, user_msg, temperature=0)
