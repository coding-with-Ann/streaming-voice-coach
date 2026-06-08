import asyncio

from voice_coach.coach import VoiceCoach


def test_voice_coach_handles_empty_transcript():
    response = asyncio.run(VoiceCoach().respond("   "))

    assert "did not catch" in response


def test_voice_coach_flags_fillers():
    response = asyncio.run(VoiceCoach().respond("Um I would like to improve"))

    assert "Reduce filler words" in response
