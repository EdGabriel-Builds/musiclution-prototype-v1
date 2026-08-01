"""
Unit tests for the score module.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make src importable without installing the package.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from score.score import Note, Measure, Score, Rest  # noqa: E402


def test_note_creation():
    """Test creating a basic note."""
    note = Note(
        pitch_name="C4",
        midi=60,
        start_time=0.0,
        duration=1.0,
        velocity=0.8
    )

    assert note.pitch_name == "C4"
    assert note.midi == 60
    assert note.start_time == 0.0
    assert note.duration == 1.0
    assert note.velocity == 0.8


def test_note_defaults():
    """Test note creation with default values."""
    note = Note(
        pitch_name="D5",
        midi=62,
        start_time=2.5,
        duration=0.5
    )

    assert note.velocity == 1.0  # default value


def test_note_validation():
    """Test that note validation works correctly."""
    # Test MIDI validation
    with pytest.raises(ValueError):
        Note("C4", -1, 0.0, 1.0)

    with pytest.raises(ValueError):
        Note("C4", 128, 0.0, 1.0)

    # Test start time validation
    with pytest.raises(ValueError):
        Note("C4", 60, -1.0, 1.0)

    # Test duration validation
    with pytest.raises(ValueError):
        Note("C4", 60, 0.0, 0.0)

    with pytest.raises(ValueError):
        Note("C4", 60, 0.0, -1.0)

    # Test velocity validation
    with pytest.raises(ValueError):
        Note("C4", 60, 0.0, 1.0, 1.5)

    with pytest.raises(ValueError):
        Note("C4", 60, 0.0, 1.0, -0.1)


def test_measure_creation():
    """Test creating a measure with notes."""
    note1 = Note("C4", 60, 0.0, 1.0)
    note2 = Note("E4", 64, 1.0, 1.0)

    measure = Measure(
        number=1,
        events=[note1, note2],
        time_signature_top=4,
        time_signature_bottom=4
    )

    assert measure.number == 1
    assert len(measure.notes) == 2
    assert measure.time_signature_top == 4
    assert measure.time_signature_bottom == 4


def test_measure_defaults():
    """Test measure creation with default time signature."""
    measure = Measure(number=1)

    assert measure.number == 1
    assert measure.time_signature_top == 4
    assert measure.time_signature_bottom == 4
    assert len(measure.notes) == 0


def test_measure_validation():
    """Test that measure validation works correctly."""
    # Test measure number validation
    with pytest.raises(ValueError):
        Measure(0)

    # Test time signature validation
    with pytest.raises(ValueError):
        Measure(1, time_signature_top=0)

    with pytest.raises(ValueError):
        Measure(1, time_signature_bottom=-1)


def test_score_creation():
    """Test creating a score."""
    score = Score(
        title="Test Piece",
        composer="Test Composer",
        tempo_bpm=90.0
    )

    assert score.title == "Test Piece"
    assert score.composer == "Test Composer"
    assert score.tempo_bpm == 90.0
    assert len(score.measures) == 0


def test_score_defaults():
    """Test score creation with default values."""
    score = Score()

    assert score.title == ""
    assert score.composer == ""
    assert score.tempo_bpm == 120.0
    assert len(score.measures) == 0


def test_score_validation():
    """Test that score validation works correctly."""
    with pytest.raises(ValueError):
        Score(tempo_bpm=0)

    with pytest.raises(ValueError):
        Score(tempo_bpm=-10)


def test_add_measure():
    """Adding measures to a score."""
    score = Score()

    measure1 = Measure(number=1)
    measure2 = Measure(number=2)

    score.add_measure(measure1)
    score.add_measure(measure2)

    assert len(score.measures) == 2
    assert score.measures[0].number == 1
    assert score.measures[1].number == 2


def test_get_total_duration():
    """Test calculating total duration."""
    score = Score()

    # Empty score
    assert score.get_total_duration() == 0.0

    # Add a measure with 4/4 time (4 beats)
    measure1 = Measure(number=1, time_signature_top=4, time_signature_bottom=4)
    score.add_measure(measure1)
    assert score.get_total_duration() == 4.0

    # Add a measure with 3/4 time (3 beats)
    measure2 = Measure(number=2, time_signature_top=3, time_signature_bottom=4)
    score.add_measure(measure2)
    assert score.get_total_duration() == 7.0  # 4 + 3

    # Add a measure with 6/8 time (6 eighth notes = 3 quarter note beats)
    measure3 = Measure(number=3, time_signature_top=6, time_signature_bottom=8)
    score.add_measure(measure3)
    assert score.get_total_duration() == 10.0  # 4 + 3 + 3


def test_get_all_notes():
    """Test getting all notes from a score."""
    score = Score()

    # Create some notes
    note1 = Note("C4", 60, 0.0, 1.0)
    note2 = Note("D4", 62, 1.0, 1.0)
    note3 = Note("E4", 64, 2.0, 1.0)

    # Add them to measures
    measure1 = Measure(number=1, events=[note1, note2])
    measure2 = Measure(number=2, events=[note3])

    score.add_measure(measure1)
    score.add_measure(measure2)

    all_notes = score.get_all_notes()
    assert len(all_notes) == 3
    assert all_notes[0].pitch_name == "C4"
    assert all_notes[1].pitch_name == "D4"
    assert all_notes[2].pitch_name == "E4"


def test_measure_only_rests():
    """Test creating a measure with only rests."""
    rest1 = Rest(start_time=0.0, duration=2.0)
    rest2 = Rest(start_time=2.0, duration=2.0)

    measure = Measure(
        number=1,
        events=[rest1, rest2],
        time_signature_top=4,
        time_signature_bottom=4
    )

    assert measure.number == 1
    assert len(measure.rests) == 2
    assert measure.rests[0].start_time == 0.0
    assert measure.rests[0].duration == 2.0
    assert measure.rests[1].start_time == 2.0
    assert measure.rests[1].duration == 2.0
    assert measure.time_signature_top == 4
    assert measure.time_signature_bottom == 4


def test_measure_mixed_notes_and_rests():
    """Test creating a measure with both notes and rests."""
    note = Note("C4", 60, 0.0, 1.0)
    rest = Rest(start_time=1.0, duration=2.0)
    note2 = Note("E4", 64, 3.0, 1.0)

    # Intentionally create them out of order to test sorting
    measure = Measure(
        number=1,
        events=[note2, rest, note],  # note2 (3.0), rest (1.0), note (0.0)
        time_signature_top=4,
        time_signature_bottom=4
    )

    assert measure.number == 1
    # Total events: 2 notes + 1 rest
    assert len(measure.events) == 3
    assert len(measure.notes) == 2
    assert len(measure.rests) == 1
    # After sorting by start_time, the order should be: note (0.0), rest (1.0), note2 (3.0)
    assert isinstance(measure.events[0], Note)
    assert measure.events[0].start_time == 0.0
    assert isinstance(measure.events[1], Rest)
    assert measure.events[1].start_time == 1.0
    assert measure.events[1].duration == 2.0
    assert isinstance(measure.events[2], Note)
    assert measure.events[2].pitch_name == "E4"
    assert measure.events[2].start_time == 3.0


def test_events_sorted_by_start_time():
    """Test that events in a measure are sorted by start_time."""
    # Create events with out-of-order start times
    event1 = Rest(start_time=3.0, duration=1.0)
    event2 = Note("D4", 62, 1.0, 1.0)
    event3 = Rest(start_time=0.0, duration=2.0)
    event4 = Note("F4", 65, 2.0, 1.0)

    measure = Measure(
        number=1,
        events=[event1, event2, event3, event4],
        time_signature_top=4,
        time_signature_bottom=4
    )

    # Check that the events are sorted by start_time
    assert len(measure.events) == 4
    assert isinstance(measure.events[0], Rest)
    assert measure.events[0].start_time == 0.0  # event3
    assert isinstance(measure.events[1], Note)
    assert measure.events[1].start_time == 1.0  # event2
    assert isinstance(measure.events[2], Note)
    assert measure.events[2].start_time == 2.0  # event4
    assert isinstance(measure.events[3], Rest)
    assert measure.events[3].start_time == 3.0  # event1


if __name__ == "__main__":
    pytest.main([__file__])