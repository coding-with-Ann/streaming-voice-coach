from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoachingContext:
    goal: str = "Speak clearly, confidently, and concisely."


class VoiceCoach:
    def __init__(self, context: CoachingContext | None = None) -> None:
        self._context = context or CoachingContext()

    async def respond(self, transcript: str) -> str:
        cleaned = " ".join(transcript.split())
        if not cleaned:
            return "I did not catch that. Try again with one short sentence."

        filler_count = sum(cleaned.lower().split().count(word) for word in ("um", "uh", "like"))
        if filler_count:
            return (
                f"I heard: {cleaned}. Reduce filler words and pause briefly before key points."
            )

        return (
            f"I heard: {cleaned}. Strong start. Make the next version a little more specific "
            f"and keep the goal in mind: {self._context.goal}"
        )
