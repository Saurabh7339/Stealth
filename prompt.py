# prompt_patterns.py
"""A small utility module to turn structured input lists into full‑sentence prompts
according to several popular prompt‑engineering patterns (RTF, TAG, BAB, CARE,
APO, RACCCA, PGTC) plus a simple KEYWORDS helper.

Each *render* method now wraps the raw fields in a short, explicit instruction
addressed to an AI assistant so the downstream model receives fuller context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Type

__all__ = [
    "PromptPattern",
    "generate_prompt",
]


class PromptPattern(ABC):
    """Base class for all prompt‑pattern helpers."""

    name: str = ""  # pattern code (upper‑case)
    fields: List[str] = []  # ordered field names
    max_items: int | None = None

    def __init__(self, items: List[str]):
        self.items = items
        self._validate()

    # ------------------------------------------------------------------
    @abstractmethod
    def render(self) -> str:  # pragma: no cover
        """Return the fully‑formatted prompt string."""

    # ------------------------------------------------------------------
    def _validate(self) -> None:  # basic length checks
        if self.max_items is not None and len(self.items) > self.max_items:
            raise ValueError(
                f"{self.name}: expects at most {self.max_items} items; "
                f"got {len(self.items)}"
            )
        if self.fields and len(self.items) != len(self.fields):
            raise ValueError(
                f"{self.name}: expects exactly {len(self.fields)} items ("
                f"{', '.join(self.fields)}) but got {len(self.items)}"
            )

    def __str__(self) -> str:  # convenience
        return self.render()


# -------------------------------------------------------------------------
# Concrete pattern helpers
# -------------------------------------------------------------------------


class RTFPattern(PromptPattern):
    name = "RTF"
    fields = ["Role", "Task", "Format"]

    def render(self) -> str:
        role, task, fmt = self.items
        return (
            "You are an AI assistant. "
            f"{role.strip()}. Your task is to {task.strip()}. "
            f"Provide your answer in the following format: {fmt.strip()}"
        )


class TAGPattern(PromptPattern):
    name = "TAG"
    fields = ["Task", "Action", "Goal"]

    def render(self) -> str:
        task, action, goal = self.items
        return (
            "You are an AI assistant. "
            f"Task: {task.strip()}. "
            f"Action to take: {action.strip()}. "
            f"Overall goal: {goal.strip()}."
        )


class BABPattern(PromptPattern):
    name = "BAB"
    fields = ["Before", "After", "Bridge"]

    def render(self) -> str:
        before, after, bridge = self.items
        return (
            "You are an AI assistant. "
            f"Current situation (Before): {before.strip()}. "
            f"Desired outcome (After): {after.strip()}. "
            f"Provide a detailed plan to bridge the gap: {bridge.strip()}"
        )


class CAREPattern(PromptPattern):
    name = "CARE"
    fields = ["Context", "Action", "Result", "Example"]

    def render(self) -> str:
        context, action, result, example = self.items
        return (
            "You are an AI assistant. "
            f"Context: {context.strip()}. "
            f"Required action: {action.strip()}. "
            f"Expected result: {result.strip()}. "
            f"Illustrative example: {example.strip()}."
        )


class APOPattern(PromptPattern):
    name = "APO"
    fields = ["Action", "Purpose", "Outcome"]

    def render(self) -> str:
        action, purpose, outcome = self.items
        return (
            "You are an AI assistant. "
            f"Please {action.strip()}. "
            f"Purpose: {purpose.strip()}. "
            f"Desired outcome: {outcome.strip()}."
        )


class RACCCAPattern(PromptPattern):
    name = "RACCCA"
    fields = ["Role", "Audience", "Context", "Constraints", "Actions"]

    def render(self) -> str:
        role, audience, context, constraints, actions = self.items
        return (
            f"You are {role.strip()} acting as an AI assistant for {audience.strip()}. "
            f"Context: {context.strip()}. "
            f"Please observe the following constraints: {constraints.strip()}. "
            f"Perform these actions: {actions.strip()}."
        )


class PGTCPattern(PromptPattern):
    name = "PGTC"
    fields = ["Position", "Goal", "Task", "Constraints"]

    def render(self) -> str:
        position, goal, task, constraints = self.items
        return (
            "You are an AI assistant. "
            f"Position: {position.strip()}. "
            f"Goal: {goal.strip()}. "
            f"Task: {task.strip()}. "
            f"Constraints: {constraints.strip()}."
        )


class KeywordsPattern(PromptPattern):
    """Join ≤10 keywords plus an instruction line."""

    name = "KEYWORDS"
    max_items = 10

    def render(self) -> str:
        keywords = ", ".join(kw.strip() for kw in self.items)
        return (
            "You are an AI assistant. Craft a high‑quality prompt that naturally "
            f"incorporates the following keywords: {keywords}."
        )


# -------------------------------------------------------------------------
# Registry & factory
# -------------------------------------------------------------------------

_PATTERN_REGISTRY: Dict[str, Type[PromptPattern]] = {
    cls.name: cls
    for cls in [
        RTFPattern,
        TAGPattern,
        BABPattern,
        CAREPattern,
        APOPattern,
        RACCCAPattern,
        PGTCPattern,
        KeywordsPattern,
    ]
}


def generate_prompt(pattern_type: str, items: List[str]) -> str:
    """Return a fully rendered prompt for *pattern_type* using *items*."""

    key = pattern_type.strip().upper()
    if key not in _PATTERN_REGISTRY:
        raise ValueError(
            f"Unknown pattern type '{pattern_type}'. Supported types: "
            f"{', '.join(_PATTERN_REGISTRY)}"
        )
    return _PATTERN_REGISTRY[key](items).render()
