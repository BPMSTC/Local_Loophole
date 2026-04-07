from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from loophole.agents.base import BaseAgent
from loophole.models import Case, SessionState
from loophole.parsing import extract_tag, parse_bool_tag, parse_choice_tag
from loophole.prompts import JUDGE_RESOLVE, JUDGE_SYSTEM, JUDGE_VALIDATE


def _format_resolved_cases(cases: list[Case]) -> str:
    if not cases:
        return "(none yet)"
    parts = []
    for c in cases:
        parts.append(
            f"Case #{c.id} ({c.case_type.value})\n"
            f"  Scenario: {c.scenario}\n"
            f"  Problem: {c.explanation}\n"
            f"  Resolution: {c.resolution}\n"
            f"  Resolved by: {c.resolved_by}"
        )
    return "\n\n".join(parts)


@dataclass
class JudgeResult:
    resolvable: bool
    reasoning: str
    proposed_revision: str | None = None
    resolution_summary: str | None = None
    conflict_explanation: str | None = None


@dataclass
class ValidationResult:
    passes: bool
    details: str


class Judge(BaseAgent):
    def _build_system_prompt(self, **kwargs: Any) -> str:
        return JUDGE_SYSTEM

    def _build_user_message(self, state: SessionState, **kwargs: Any) -> str:
        case: Case = kwargs["case"]
        return JUDGE_RESOLVE.format(
            moral_principles=state.moral_principles,
            user_clarifications="\n".join(state.user_clarifications) or "(none)",
            code_version=state.current_code.version,
            legal_code=state.current_code.text,
            case_type=case.case_type.value,
            case_scenario=case.scenario,
            case_explanation=case.explanation,
            resolved_cases_text=_format_resolved_cases(state.resolved_cases),
        )

    def evaluate(self, state: SessionState, case: Case) -> JudgeResult:
        raw = self.run(state, case=case)

        verdict = parse_choice_tag(raw, "verdict", {"resolvable", "unresolvable"})
        reasoning = extract_tag(raw, "reasoning") or ""

        if verdict is None:
            repaired = self.repair_output(
                raw,
                "<reasoning>...</reasoning>\n<verdict>resolvable OR unresolvable</verdict>\n"
                "<proposed_revision>...</proposed_revision>\n<resolution_summary>...</resolution_summary>\n"
                "<conflict_explanation>...</conflict_explanation>",
            )
            raw = repaired
            verdict = parse_choice_tag(raw, "verdict", {"resolvable", "unresolvable"})
            reasoning = extract_tag(raw, "reasoning") or reasoning

        verdict = verdict or "unresolvable"

        if verdict == "resolvable":
            return JudgeResult(
                resolvable=True,
                reasoning=reasoning,
                proposed_revision=extract_tag(raw, "proposed_revision"),
                resolution_summary=extract_tag(raw, "resolution_summary"),
            )
        return JudgeResult(
            resolvable=False,
            reasoning=reasoning,
            conflict_explanation=extract_tag(raw, "conflict_explanation") or raw,
        )

    def validate(self, state: SessionState, proposed_code: str) -> ValidationResult:
        resolved = state.resolved_cases
        if not resolved:
            return ValidationResult(passes=True, details="No prior cases to validate against.")

        user_msg = JUDGE_VALIDATE.format(
            proposed_code=proposed_code,
            resolved_cases_text=_format_resolved_cases(resolved),
        )
        raw = self.llm.call(JUDGE_SYSTEM, user_msg, temperature=self.temperature)

        passes = parse_bool_tag(raw, "passes")
        details = extract_tag(raw, "details")

        if passes is None:
            repaired = self.repair_output(
                raw,
                "<validation><passes>true OR false</passes><details>...</details></validation>",
            )
            passes = parse_bool_tag(repaired, "passes")
            details = details or extract_tag(repaired, "details")

        return ValidationResult(passes=bool(passes), details=details or raw)
