"""
Unit tests for the key detection module (Milestone 2D).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make src importable without installing the package.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from music.key_detection import detect_key, detect_key_from_score
from score.score import Note, Measure, Score, Rest


def test_major_key_detection():
    """Test detection of a major key from a C major melody."""
    # Create a simple C major scale: C4, D4, E4, F4, G4, A4, B4, C5
    notes = [
        Note("C4", 60, 0.0, 1.0),
        Note("D4", 62, 1.0, 1.0),
        Note("E4", 64, 2.0, 1.0),
        Note("F4", 65, 3.0, 1.0),
        Note("G4", 67, 4.0, 1.0),
        Note("A4", 69, 5.0, 1.0),
        Note("B4", 71, 6.0, 1.0),
        Note("C5", 72, 7.0, 1.0),
    ]

    key_name, mode, confidence = detect_key(notes)

    assert key_name == "C"
    assert mode == "major"
    assert confidence == 0.0  # Ambiguity with relative minor (A minor) => confidence 0.0


def test_minor_key_detection():
    """Test detection of a minor key from an A minor melody."""
    # Create an A minor scale: A4, B4, C4, D4, E4, F4, G4, A5
    notes = [
        Note("A4", 69, 0.0, 1.0),
        Note("B4", 71, 1.0, 1.0),
        Note("C4", 60, 2.0, 1.0),  # Note: C4 is midi 60
        Note("D4", 62, 3.0, 1.0),
        Note("E4", 64, 4.0, 1.0),
        Note("F4", 65, 5.0, 1.0),
        Note("G4", 67, 6.0, 1.0),
        Note("A5", 81, 7.0, 1.0),
    ]

    key_name, mode, confidence = detect_key(notes)

    assert key_name == "A"
    assert mode == "minor"
    # Ambiguity with relative major (C major) => confidence 0.0
    assert confidence == 0.0


def test_score_integration():
    """Test that detect_key_from_score matches direct detection."""
    # Create a simple C major melody
    notes = [
        Note("C4", 60, 0.0, 1.0),
        Note("E4", 64, 1.0, 1.0),
        Note("G4", 67, 2.0, 1.0),
        Note("C5", 72, 3.0, 1.0),
    ]

    # Direct detection
    expected_key, expected_mode, expected_conf = detect_key(notes)

    # Create a score with one measure containing these notes
    measure = Measure(number=1, events=notes)
    score = Score()
    score.add_measure(measure)

    # Detection via score
    key_name, mode, confidence = detect_key_from_score(score)

    assert key_name == expected_key
    assert mode == expected_mode
    assert confidence == expected_conf


def test_rest_handling():
    """Test that rests are ignored and do not affect key detection."""
    # Create a C major melody with rests in between
    notes_and_rests = [
        Note("C4", 60, 0.0, 1.0),
        Rest(start_time=1.0, duration=1.0),  # rest for 1 second
        Note("E4", 64, 2.0, 1.0),
        Rest(start_time=3.0, duration=2.0),  # rest for 2 seconds
        Note("G4", 67, 5.0, 1.0),
    ]

    # Extract only the notes for expected result
    notes_only = [n for n in notes_and_rests if isinstance(n, Note)]
    expected_key, expected_mode, expected_conf = detect_key(notes_only)

    # Create a score with the mixed events
    measure = Measure(number=1, events=notes_and_rests)
    score = Score()
    score.add_measure(measure)

    # Detection via score (should ignore rests)
    key_name, mode, confidence = detect_key_from_score(score)

    assert key_name == expected_key
    assert mode == expected_mode
    assert confidence == expected_conf


def test_empty_input():
    """Test handling of empty input (no notes)."""
    # Direct call with empty list
    key_name, mode, confidence = detect_key([])
    assert key_name == "C"
    assert mode == "major"
    assert confidence == 0.0

    # Call with an empty score
    score = Score()
    key_name, mode, confidence = detect_key_from_score(score)
    assert key_name == "C"
    assert mode == "major"
    assert confidence == 0.0


def test_ambiguous_key_confidence_zero():
    """Test that ambiguous key selection yields zero confidence."""
    # Notes C and D: C major and D minor both score 2 (C,D fit both scales)
    notes = [
        Note("C4", 60, 0.0, 1.0),  # pitch class 0
        Note("D4", 62, 1.0, 1.0),  # pitch class 2
    ]

    key_name, mode, confidence = detect_key(notes)

    # Due to tie-breaking, the key with tonic matching first note's PC (C) should be chosen:
    # C major (tonic 0, major) vs D minor (tonic 2, minor). First note is C4 -> PC 0,
    # so we expect C major.
    assert key_name == "C"
    assert mode == "major"
    # Ambiguity => confidence should be 0.0
    assert confidence == 0.0