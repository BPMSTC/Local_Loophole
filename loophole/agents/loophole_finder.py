from __future__ import annotations

from typing import Any

from loophole.agents.base import BaseAgent
from loophole.models import Case, CaseType, SessionState
from loophole.parsing import parse_scenarios
from loophole.prompts import LOOPHOLE_FINDER_SYSTEM, LOOPHOLE_FINDER_USER


def _format_prior_cases(cases: list[Case]) -> str:
    if not cases:
        return "(none yet)"
    parts = []
    for c in cases:
        parts.append(f"Case #{c.id} ({c.case_type.value}): {c.scenario}")
    return "\n".join(parts)


class LoopholeFinder(BaseAgent):
    def __init__(self, *args: Any, cases_per_agent: int = 3, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.cases_per_agent = cases_per_agent

    def _build_system_prompt(self, **kwargs: Any) -> str:
        return LOOPHOLE_FINDER_SYSTEM.format(cases_per_agent=self.cases_per_agent)

    def _build_user_message(self, state: SessionState, **kwargs: Any) -> str:
        return LOOPHOLE_FINDER_USER.format(
            moral_principles=state.moral_principles,
            user_clarifications="\n".join(state.user_clarifications) or "(none)",
            code_version=state.current_code.version,
            legal_code=state.current_code.text,
            prior_cases_text=_format_prior_cases(state.cases),
            cases_per_agent=self.cases_per_agent,
        )

    def find(self, state: SessionState) -> list[Case]:
        raw = self.run(state)
        parsed = parse_scenarios(raw)
        if not parsed:
            repaired = self.repair_output(
                raw,
                "<scenario><description>...</description><explanation>...</explanation></scenario>",
            )
            parsed = parse_scenarios(repaired)
        return _build_cases(parsed, state, CaseType.LOOPHOLE)


def _build_cases(parsed: list[tuple[str, str]], state: SessionState, case_type: CaseType) -> list[Case]:
    cases: list[Case] = []
    for description, explanation in parsed:
        cases.append(
            Case(
                id=state.next_case_id + len(cases),
                round=state.current_round,
                case_type=case_type,
                scenario=description,
                explanation=explanation,
            )
        )
    return cases
