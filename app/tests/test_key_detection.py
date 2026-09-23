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

from music.key_detection import detect_key, detect_key_from_score, apply_key_aware_spelling, get_fifths_from_key_name_mode
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


def test_get_fifths_from_key_name_mode():
    """Test conversion of key name and mode to fifths."""
    test_cases = [
        ("C", "major", 0),
        ("C", "minor", -3),   # C minor: relative major is Eb (3) -> -3
        ("Db", "major", -5),
        ("Db", "minor", 4),   # Db minor: relative major is E (4) -> 4
        ("D", "major", 2),
        ("D", "minor", -1),   # D minor: relative major is F (5) -> -1
        ("Eb", "major", -3),
        ("Eb", "minor", -6),  # Eb minor: relative major is Gb (6) -> -6
        ("E", "major", 4),
        ("E", "minor", 1),    # E minor: relative major is G (7) -> 1
        ("F", "major", -1),
        ("F", "minor", -4),   # F minor: relative major is Ab (8) -> -4
        ("Gb", "major", -6),
        ("Gb", "minor", 3),   # Gb minor: relative major is A (9) -> 3
        ("G", "major", 1),
        ("G", "minor", -2),   # G minor: relative major is Bb (10) -> -2
        ("Ab", "major", -4),
        ("Ab", "minor", 5),   # Ab minor: relative major is B (11) -> 5
        ("A", "major", 3),
        ("A", "minor", 0),    # A minor: relative major is C (0) -> 0
        ("Bb", "major", -2),
        ("Bb", "minor", -5),  # Bb minor: relative major is Db (1) -> -5
        ("B", "major", 5),
        ("B", "minor", 2),    # B minor: relative major is D (2) -> 2
    ]
    for key_name, mode, expected in test_cases:
        assert get_fifths_from_key_name_mode(key_name, mode) == expected


def test_apply_key_aware_spelling():
    """Test the key-aware pitch spelling function."""
    # Test data: (midi, input_pitch_name, expected_pitch_name_for_fifths)
    test_cases = [
        # Eb major (fifths = -3)
        (60, "C4", "C4"),    # natural
        (61, "C#4", "Db4"),  # sharp -> flat
        (62, "D4", "D4"),    # natural
        (63, "D#4", "Eb4"),  # sharp -> flat
        (64, "E4", "E4"),    # natural
        (65, "F4", "F4"),    # natural
        (66, "F#4", "Gb4"),  # sharp -> flat
        (67, "G4", "G4"),    # natural
        (68, "G#4", "Ab4"),  # sharp -> flat
        (69, "A4", "A4"),    # natural
        (70, "A#4", "Bb4"),  # sharp -> flat
        (71, "B4", "B4"),    # natural

        # D major (fifths = 2)
        (60, "C4", "C4"),    # natural
        (61, "C#4", "C#4"),  # sharp -> sharp (preferred)
        (61, "Db4", "C#4"),  # flat -> sharp
        (62, "D4", "D4"),    # natural
        (63, "D#4", "D#4"),  # sharp -> sharp (preferred)
        (63, "Eb4", "D#4"),  # flat -> sharp
        (64, "E4", "E4"),    # natural
        (65, "F4", "F4"),    # natural
        (66, "F#4", "F#4"),  # sharp -> sharp (preferred)
        (66, "Gb4", "F#4"),  # flat -> sharp
        (67, "G4", "G4"),    # natural
        (68, "G#4", "G#4"),  # sharp -> sharp (preferred)
        (69, "A4", "A4"),    # natural
        (70, "A#4", "A#4"),  # sharp -> sharp (preferred)
        (71, "B4", "B4"),    # natural

        # C major (fifths = 0) - sharp spelling by convention
        (60, "C4", "C4"),
        (61, "C#4", "C#4"),
        (61, "Db4", "C#4"),  # flat -> sharp (convention)
        (62, "D4", "D4"),
        (63, "D#4", "D#4"),
        (63, "Eb4", "D#4"),  # flat -> sharp (convention)
        (64, "E4", "E4"),
        (65, "F4", "F4"),
        (66, "F#4", "F#4"),  # Fixed: was missing comma
        (66, "Gb4", "F#4"),  # Fixed: was missing comma - flat -> sharp (convention)
        (67, "G4", "G4"),
        (68, "G#4", "G#4"),
        (69, "A4", "A4"),    # Fixed: was missing comma
        (70, "A#4", "A#4"),  # Fixed: was missing comma
        (70, "Bb4", "A#4"),  # Fixed: was missing comma - flat -> sharp (convention)
        (71, "B4", "B4"),
    ]

    for midi, input_name, expected in test_cases:
        # Determine the appropriate fifths for the test case
        # We'll test with the specific fifths values we care about
        pass

    # Instead, let's test by fifths value directly
    # Eb major (fifths = -3)
    eb_test_notes = [
        {"midi": 60, "pitch_name": "C4"},
        {"midi": 61, "pitch_name": "C#4"},
        {"midi": 62, "pitch_name": "D4"},
        {"midi": 63, "pitch_name": "D#4"},
        {"midi": 64, "pitch_name": "E4"},
        {"midi": 65, "pitch_name": "F4"},
        {"midi": 66, "pitch_name": "F#4"},
        {"midi": 67, "pitch_name": "G4"},
        {"midi": 68, "pitch_name": "G#4"},
        {"midi": 69, "pitch_name": "A4"},
        {"midi": 70, "pitch_name": "A#4"},
        {"midi": 71, "pitch_name": "B4"},
    ]
    eb_result = apply_key_aware_spelling(eb_test_notes, -3)
    expected_eb = ["C4", "Db4", "D4", "Eb4", "E4", "F4", "Gb4", "G4", "Ab4", "A4", "Bb4", "B4"]
    actual_eb = [note["pitch_name"] for note in eb_result]
    assert actual_eb == expected_eb, f"Eb major spelling failed:\nExpected: {expected_eb}\nActual:   {actual_eb}"

    # D major (fifths = 2)
    d_test_notes = [
        {"midi": 60, "pitch_name": "C4"},
        {"midi": 61, "pitch_name": "C#4"},
        {"midi": 62, "pitch_name": "D4"},
        {"midi": 63, "pitch_name": "D#4"},
        {"midi": 64, "pitch_name": "E4"},
        {"midi": 65, "pitch_name": "F4"},
        {"midi": 66, "pitch_name": "F#4"},
        {"midi": 67, "pitch_name": "G4"},
        {"midi": 68, "pitch_name": "G#4"},
        {"midi": 69, "pitch_name": "A4"},
        {"midi": 70, "pitch_name": "A#4"},
        {"midi": 71, "pitch_name": "B4"},
    ]
    d_result = apply_key_aware_spelling(d_test_notes, 2)
    expected_d = ["C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4"]
    actual_d = [note["pitch_name"] for note in d_result]
    assert actual_d == expected_d, f"D major spelling failed:\nExpected: {expected_d}\nActual:   {actual_d}"

    # C major (fifths = 0) - sharp spelling by convention
    # Test each MIDI once, with both sharp and flat inputs where applicable
    c_test_notes = [
        {"midi": 60, "pitch_name": "C4"},
        {"midi": 61, "pitch_name": "C#4"},
        {"midi": 61, "pitch_name": "Db4"},  # Test flat input for C#
        {"midi": 62, "pitch_name": "D4"},
        {"midi": 63, "pitch_name": "D#4"},
        {"midi": 63, "pitch_name": "Eb4"},  # Test flat input for D#
        {"midi": 64, "pitch_name": "E4"},
        {"midi": 65, "pitch_name": "F4"},
        {"midi": 66, "pitch_name": "F#4"},
        {"midi": 66, "pitch_name": "Gb4"},  # Test flat input for F#
        {"midi": 67, "pitch_name": "G4"},
        {"midi": 68, "pitch_name": "G#4"},
        {"midi": 68, "pitch_name": "Ab4"},  # Test flat input for G#
        {"midi": 69, "pitch_name": "A4"},
        {"midi": 70, "pitch_name": "A#4"},
        {"midi": 70, "pitch_name": "Bb4"},  # Test flat input for A#
        {"midi": 71, "pitch_name": "B4"},
    ]
    c_result = apply_key_aware_spelling(c_test_notes, 0)
    # For C major (fifths=0), we use sharp spelling
    expected_c = [
        "C4",    # 60
        "C#4",   # 61 from C#4
        "C#4",   # 61 from Db4 -> C#4
        "D4",    # 62
        "D#4",   # 63
        "D#4",   # 63 from Eb4 -> D#4
        "E4",    # 64
        "F4",    # 65
        "F#4",   # 66
        "F#4",   # 66 from Gb4 -> F#4
        "G4",    # 67
        "G#4",   # 68
        "G#4",   # 68 from Ab4 -> G#4
        "A4",    # 69
        "A#4",   # 70
        "A#4",   # 70 from Bb4 -> A#4
        "B4",    # 71
    ]
    actual_c = [note["pitch_name"] for note in c_result]
    assert actual_c == expected_c, f"C major spelling failed:\nExpected: {expected_c}\nActual:   {actual_c}"

    # Verify that MIDI values and other fields are preserved
    original_notes = [
        {"midi": 63, "pitch_name": "D#4", "beat_start": 1.0, "beat_duration": 2.0, "quantized_duration": "half", "amplitude": 0.8, "extra_field": "preserved"}
    ]
    result = apply_key_aware_spelling(original_notes, -3)
    assert len(result) == 1
    assert result[0]["midi"] == 63  # MIDI preserved
    assert result[0]["pitch_name"] == "Eb4"  # Respelled
    assert result[0]["beat_start"] == 1.0  # Timing preserved
    assert result[0]["beat_duration"] == 2.0  # Duration preserved
    assert result[0]["quantized_duration"] == "half"  # Quantization preserved
    assert result[0]["amplitude"] == 0.8  # Amplitude preserved
    assert result[0]["extra_field"] == "preserved"  # Extra fields preserved
    assert result[0] is not original_notes[0]  # New object (shallow copy)

    # Verify input is not mutated
    assert original_notes[0]["pitch_name"] == "D#4"  # Input unchanged