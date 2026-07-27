"""
Tests for the quantize module.

These tests verify that the quantize_notes()
Unit tests for the quantize module.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make src/transcription importable without installing the package.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src" / "transcription"))

from quantize import quantize_notes  # noqa: E402


def test_quantize_notes_returns_new_list():
    """quantize_notes returns a new list; input is not mutated."""
    input_notes = [
        {
            "pitch_name": "C4",
            "midi": 60,
            "start": 0.0,
            "end": 1.0,
            "duration": 1.0,
            "amplitude": 0.8,
        }
    ]
    # Keep a copy to compare later
    original = [n.copy() for n in input_notes]

    output = quantize_notes(input_notes)

    # Output is a different list object
    assert output is not input_notes
    # But has same length
    assert len(output) == len(input_notes)
    # Input list is unchanged
    assert input_notes == original


def test_quantize_notes_preserves_original_fields():
    """All original fields are preserved exactly."""
    input_notes = [
        {
            "pitch_name": "D4",
            "midi": 62,
            "start": 0.5,
            "end": 1.5,
            "duration": 1.0,
            "amplitude": 0.7,
        }
    ]

    output = quantize_notes(input_notes)
    out_note = output[0]

    # Original fields unchanged
    assert out_note["pitch_name"] == "D4"
    assert out_note["midi"] == 62
    assert out_note["start"] == 0.5
    assert out_note["end"] == 1.5
    assert out_note["duration"] == 1.0
    assert out_note["amplitude"] == 0.7


def test_quantize_notes_adds_placeholder_fields_with_explicit_bpm():
    """New fields are added with correct values when BPM is explicitly provided."""
    # Use a known BPM to make test deterministic
    input_notes = [
        {
            "pitch_name": "E4",
            "midi": 64,
            "start": 1.0,
            "end": 2.0,
            "duration": 1.0,
            "amplitude": 0.9,
        }
    ]

    # With BPM=120.0: 1 second = 2 beats (since 120 BPM = 2 beats per second)
    output = quantize_notes(input_notes, bpm=120.0)
    out_note = output[0]

    # New fields exist
    assert "beat_start" in out_note
    assert "beat_duration" in out_note
    assert "quantized_duration" in out_note

    # With BPM=120.0: beat = seconds * (BPM/60) = seconds * 2
    assert out_note["beat_start"] == 2.0  # 1.0 * 2
    assert out_note["beat_duration"] == 2.0  # 1.0 * 2
    assert out_note["quantized_duration"] == "unknown"


def test_quantize_notes_handles_empty_list():
    """Empty input returns empty list."""
    assert quantize_notes([]) == []


def test_quantize_notes_multiple_notes_with_explicit_bpm():
    """Works with multiple notes when BPM is explicitly provided."""
    # Use a known BPM to make test deterministic
    input_notes = [
        {
            "pitch_name": "C4",
            "midi": 60,
            "start": 0.0,
            "end": 1.0,
            "duration": 1.0,
            "amplitude": 0.8,
        },
        {
            "pitch_name": "D4",
            "midi": 62,
            "start": 1.0,
            "end": 2.0,
            "duration": 1.0,
            "amplitude": 0.9,
        },
    ]

    # With BPM=60.0: 1 second = 1 beat (since 60 BPM = 1 beat per second)
    output = quantize_notes(input_notes, bpm=60.0)
    assert len(output) == 2

    # First note
    assert output[0]["pitch_name"] == "C4"
    assert output[0]["beat_start"] == 0.0  # 0.0 * 1
    assert output[0]["beat_duration"] == 1.0  # 1.0 * 1
    assert output[0]["quantized_duration"] == "unknown"

    # Second note
    assert output[1]["pitch_name"] == "D4"
    assert output[1]["beat_start"] == 1.0  # 1.0 * 1
    assert output[1]["beat_duration"] == 1.0  # 1.0 * 1
    assert output[1]["quantized_duration"] == "unknown"


def test_quantize_notes_uses_provided_bpm_over_estimate():
    """When bpm is provided, it is used instead of estimating."""
    input_notes = [
        {
            "pitch_name": "C4",
            "midi": 60,
            "start": 1.0,  # Non-zero start to test BPM effect
            "end": 2.0,
            "duration": 1.0,
            "amplitude": 0.8,
        }
    ]

    # With a single note, estimate_bpm() returns 120.0 (default)
    # But if we provide bpm=60.0, it should use 60.0 instead
    estimated_bpm_result = quantize_notes(input_notes, bpm=None)  # Should estimate ~120.0
    provided_bpm_result = quantize_notes(input_notes, bpm=60.0)  # Should use 60.0

    # The beat values should be different due to different BPM
    assert estimated_bpm_result[0]["beat_start"] != provided_bpm_result[0]["beat_start"]
    assert estimated_bpm_result[0]["beat_duration"] != provided_bpm_result[0]["beat_duration"]

    # With bpm=60.0: 1 second = 1 beat
    assert provided_bpm_result[0]["beat_start"] == 1.0  # 1.0 * 1
    assert provided_bpm_result[0]["beat_duration"] == 1.0  # 1.0 * 1


def test_quantize_notes_bpm_parameter_behavior():
    """Test that bpm parameter is used when provided, otherwise estimated."""
    input_notes = [
        {
            "pitch_name": "F4",
            "midi": 65,
            "start": 0.0,
            "end": 1.0,
            "duration": 1.0,
            "amplitude": 0.5,
        }
    ]

    # With single note, estimation returns default 120.0
    # Test explicit values
    out_60 = quantize_notes(input_notes, bpm=60.0)   # 1 sec = 1 beat
    out_120 = quantize_notes(input_notes, bpm=120.0) # 1 sec = 2 beats
    out_none = quantize_notes(input_notes, bpm=None) # Should estimate ~120.0

    # With bpm=60.0: beat = seconds * 1
    assert out_60[0]["beat_start"] == 0.0   # 0.0 * 1
    assert out_60[0]["beat_duration"] == 1.0 # 1.0 * 1

    # With bpm=120.0: beat = seconds * 2
    assert out_120[0]["beat_start"] == 0.0   # 0.0 * 2
    assert out_120[0]["beat_duration"] == 2.0 # 1.0 * 2

    # With bpm=None: should estimate ~120.0 (single note -> default 120.0)
    assert out_none[0]["beat_start"] == 0.0   # 0.0 * 2
    assert out_none[0]["beat_duration"] == 2.0 # 1.0 * 2

    # 60 and 120 should give different results
    assert out_60[0]["beat_duration"] != out_120[0]["beat_duration"]