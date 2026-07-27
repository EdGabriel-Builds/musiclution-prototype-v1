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


def test_quantize_notes_adds_placeholder_fields():
    """Placeholder fields are added with correct values."""
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

    output = quantize_notes(input_notes)
    out_note = output[0]

    # New fields exist
    assert "beat_start" in out_note
    assert "beat_duration" in out_note
    assert "quantized_duration" in out_note

    # Placeholder values
    assert out_note["beat_start"] == 1.0  # copied from start
    assert out_note["beat_duration"] == 1.0  # copied from duration
    assert out_note["quantized_duration"] == "unknown"


def test_quantize_notes_handles_empty_list():
    """Empty input returns empty list."""
    assert quantize_notes([]) == []


def test_quantize_notes_multiple_notes():
    """Works with multiple notes."""
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

    output = quantize_notes(input_notes)
    assert len(output) == 2

    # First note
    assert output[0]["pitch_name"] == "C4"
    assert output[0]["beat_start"] == 0.0
    assert output[0]["beat_duration"] == 1.0
    assert output[0]["quantized_duration"] == "unknown"

    # Second note
    assert output[1]["pitch_name"] == "D4"
    assert output[1]["beat_start"] == 1.0
    assert output[1]["beat_duration"] == 1.0
    assert output[1]["quantized_duration"] == "unknown"


def test_quantize_notes_bpm_argument_ignored():
    """bpm argument is accepted but ignored in this stub."""
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

    # Should not raise and should produce same output regardless of bpm
    out1 = quantize_notes(input_notes, bpm=60.0)
    out2 = quantize_notes(input_notes, bpm=120.0)
    out3 = quantize_notes(input_notes, bpm=None)

    assert out1 == out2 == out3