"""
Smoke tests for the quantize module API contract.

These tests verify the interface of quantize_notes() without checking
musical correctness. They reuse the existing melody test infrastructure.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make src/transcription importable without installing the package.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src" / "transcription"))

from detect_notes import detect_notes  # noqa: E402
from quantize import quantize_notes  # noqa: E402

MELODIES = [
    "melody_001/D_major",
    "melody_002/Eb_major",
    "melody_003/E_major",
]


@pytest.fixture(scope="module", params=MELODIES)
def melody_dir(request):
    """Fixture providing the path to a melody directory."""
    d = REPO_ROOT / "tests" / "melodies" / request.param
    if not (d / "audio.wav").exists():
        pytest.skip(f"missing audio for {request.param}")
    return d


def test_quantize_notes_api_contract(melody_dir):
    """
    Test the API contract of quantize_notes using real detected notes.

    Verifies:
    - Output is a list
    - Length matches input
    - Original note fields are preserved
    - New quantization fields exist
    - Input list is not mutated
    """
    # Get real notes from the detector (using the audio file)
    input_notes = detect_notes(melody_dir / "audio.wav")
    assert isinstance(input_notes, list), "detect_notes should return a list"
    assert len(input_notes) > 0, "we expect some notes to be detected"

    # Keep a deep copy of the input to verify immutability later
    import copy
    input_notes_copy = copy.deepcopy(input_notes)

    # Call the function under test
    output_notes = quantize_notes(input_notes, bpm=120.0)  # bpm value doesn't matter for the stub

    # 1. Output is a list
    assert isinstance(output_notes, list), "quantize_notes should return a list"

    # 2. Length matches input
    assert len(output_notes) == len(input_notes), "output length should match input length"

    # 3. Each output note has the expected fields
    required_original_fields = {"pitch_name", "midi", "start", "end", "duration", "amplitude"}
    required_new_fields = {"beat_start", "beat_duration", "quantized_duration"}

    for i, (in_note, out_note) in enumerate(zip(input_notes, output_notes)):
        # Original fields are preserved exactly
        for field in required_original_fields:
            assert field in out_note, f"missing original field '{field}' in note {i}"
            assert out_note[field] == in_note[field], (
                f"original field '{field}' changed in note {i}: "
                f"expected {in_note[field]}, got {out_note[field]}"
            )

        # New fields exist
        for field in required_new_fields:
            assert field in out_note, f"missing new field '{field}' in note {i}"

        # Specific placeholder values (as per the stub implementation)
        assert out_note["beat_start"] == out_note["start"], (
            f"beat_start should equal start in note {i}"
        )
        assert out_note["beat_duration"] == out_note["duration"], (
            f"beat_duration should equal duration in note {i}"
        )
        assert out_note["quantized_duration"] == "unknown", (
            f"quantized_duration should be 'unknown' in note {i}"
        )

    # 4. Input list is unchanged (we compare the deep copy)
    assert input_notes == input_notes_copy, "input list should not be mutated"