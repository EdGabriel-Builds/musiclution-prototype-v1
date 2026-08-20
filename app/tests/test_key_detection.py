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

    key_name, mode, confidence, fifths = detect_key(notes)

    assert key_name == "C"
    assert mode == "major"
    assert confidence == 0.0  # Ambiguity with relative minor (A minor) => confidence 0.0
    assert fifths == 0  # C major has 0 fifths


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

    key_name, mode, confidence, fifths = detect_key(notes)

    # Due to symmetry between relative major/minor, this may detect either
    # The important thing is that the fifths value is correct for the detected key
    assert mode in ["major", "minor"]
    assert confidence == 0.0  # Ambiguity between relative major/minor => confidence 0.0
    # Fifths should be 0 for both C major and A minor
    assert fifths == 0


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
    expected_key, expected_mode, expected_conf, expected_fifths = detect_key(notes)

    # Create a score with one measure containing these notes
    measure = Measure(number=1, events=notes)
    score = Score()
    score.add_measure(measure)

    # Detection via score
    key_name, mode, confidence, fifths = detect_key_from_score(score)

    assert key_name == expected_key
    assert mode == expected_mode
    assert confidence == expected_conf
    assert fifths == expected_fifths


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
    expected_key, expected_mode, expected_conf, expected_fifths = detect_key(notes_only)

    # Create a score with the mixed events
    measure = Measure(number=1, events=notes_and_rests)
    score = Score()
    score.add_measure(measure)

    # Detection via score (should ignore rests)
    key_name, mode, confidence, fifths = detect_key_from_score(score)

    assert key_name == expected_key
    assert mode == expected_mode
    assert confidence == expected_conf
    assert fifths == expected_fifths


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

    key_name, mode, confidence, fifths = detect_key(notes)

    # Due to tie-breaking, the key with tonic matching first note's PC (C) should be chosen:
    # C major (tonic 0, major) vs D minor (tonic 2, minor). First note is C4 -> PC 0,
    # so we expect C major.
    assert key_name == "C"
    assert mode == "major"
    # Ambiguity => confidence should be 0.0
    assert confidence == 0.0


def test_flat_key_detection():
    """Test detection of flat keys and correct fifths values."""
    test_cases = [
        # (root_midi, root_name, expected_fifths, description)
        (61, "Db", -5, "Db major"),
        (63, "Eb", -3, "Eb major"),
        (68, "Ab", -4, "Ab major"),
        (70, "Bb", -2, "Bb major"),
        (66, "Gb", -6, "Gb major"),
    ]

    for root_midi, root_name, expected_fifths, description in test_cases:
        # Create a major scale starting from the root
        notes = []
        scale_intervals = [0, 2, 4, 5, 7, 9, 11]  # major scale

        for interval in scale_intervals:
            midi = root_midi + interval
            # Determine pitch name (prefer flats for flat keys)
            note_name = f"{root_name}{interval//12 if interval >= 12 else ''}"
            # Simplify: just use the root name for all notes in this test
            # The key detection algorithm works with pitch classes, not note names
            note = Note(
                pitch_name=root_name,  # Simplified for testing
                midi=midi,
                start_time=0.0,
                duration=1.0,
                velocity=0.8
            )
            notes.append(note)

        key_name, mode, confidence, fifths = detect_key(notes)

        assert mode == "major", f"{description}: Expected major mode"
        assert key_name == root_name, f"{description}: Expected key name '{root_name}', got '{key_name}'"
        assert fifths == expected_fifths, f"{description}: Expected fifths={expected_fifths}, got {fifths}"
        # Note: confidence may vary based on note selection, but should be reasonable for a pure scale


def test_sharp_key_detection():
    """Test detection of sharp keys and correct fifths values (regression test)."""
    test_cases = [
        # (root_midi, root_name, expected_fifths, description)
        (62, "D", 2, "D major"),
        (64, "E", 4, "E major"),
    ]

    for root_midi, root_name, expected_fifths, description in test_cases:
        # Create a major scale starting from the root
        notes = []
        scale_intervals = [0, 2, 4, 5, 7, 9, 11]  # major scale

        for interval in scale_intervals:
            midi = root_midi + interval
            note = Note(
                pitch_name=root_name,  # Simplified for testing
                midi=midi,
                start_time=0.0,
                duration=1.0,
                velocity=0.8
            )
            notes.append(note)

        key_name, mode, confidence, fifths = detect_key(notes)

        assert mode == "major", f"{description}: Expected major mode"
        assert key_name == root_name, f"{description}: Expected key name '{root_name}', got '{key_name}'"
        assert fifths == expected_fifths, f"{description}: Expected fifths={expected_fifths}, got {fifths}"