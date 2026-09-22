"""
Tests for the monophonic cleanup stage.
"""

from __future__ import annotations

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from transcription.monophonic_cleanup import cleanup_monophonic, detect_overlaps


def test_no_overlaps():
    """Test with non-overlapping notes."""
    notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 1.0, "duration": 1.0, "amplitude": 0.8},
        {"pitch_name": "D4", "midi": 62, "start": 1.0, "end": 2.0, "duration": 1.0, "amplitude": 0.9},
        {"pitch_name": "E4", "midi": 64, "start": 2.0, "end": 3.0, "duration": 1.0, "amplitude": 0.7},
    ]
    
    cleaned = cleanup_monophonic(notes)
    assert len(cleaned) == 3
    assert cleaned[0]["end"] == 1.0
    assert cleaned[1]["end"] == 2.0
    assert cleaned[2]["end"] == 3.0
    
    overlaps = detect_overlaps(cleaned)
    assert len(overlaps) == 0


def test_overlap_truncate_previous():
    """Test that overlapping notes trigger truncation of the previous note."""
    notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 2.0, "duration": 2.0, "amplitude": 0.8},
        {"pitch_name": "D4", "midi": 62, "start": 1.0, "end": 1.5, "duration": 0.5, "amplitude": 0.9},
    ]
    
    cleaned = cleanup_monophonic(notes)
    # Should truncate first note at onset of second
    assert len(cleaned) == 2
    assert cleaned[0]["end"] == 1.0  # Truncated to start of second note
    assert cleaned[0]["duration"] == 1.0
    assert cleaned[1]["start"] == 1.0  # Unchanged
    assert cleaned[1]["end"] == 1.5    # Unchanged
    
    overlaps = detect_overlaps(cleaned)
    assert len(overlaps) == 0


def test_short_embedded_artifact():
    """Test removal of short embedded artifacts (likely reverb)."""
    notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 2.0, "duration": 2.0, "amplitude": 0.8},
        {"pitch_name": "E4", "midi": 64, "start": 0.5, "end": 0.6, "duration": 0.1, "amplitude": 0.3},  # Very short, low amplitude
        {"pitch_name": "G4", "midi": 67, "start": 1.5, "end": 2.5, "duration": 1.0, "amplitude": 0.7},
    ]
    
    cleaned = cleanup_monophonic(notes)
    # Should remove the short embedded note
    assert len(cleaned) == 2
    assert cleaned[0]["pitch_name"] == "C4"
    assert cleaned[1]["pitch_name"] == "G4"
    
    # First note should be truncated to avoid overlap with second note
    assert cleaned[0]["start"] == 0.0  # Start time unchanged
    assert cleaned[0]["end"] == 1.5    # Truncated to start of second note
    assert cleaned[0]["duration"] == 1.5
    
    # Second note should be unchanged
    assert cleaned[1]["start"] == 1.5  # Start time unchanged
    assert cleaned[1]["end"] == 2.5    # End time unchanged
    assert cleaned[1]["duration"] == 1.0
    
    overlaps = detect_overlaps(cleaned)
    assert len(overlaps) == 0


def test_legitimate_short_note():
    """Test that legitimate short notes (like sixteenths) are preserved."""
    notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 0.5, "duration": 0.5, "amplitude": 0.8},  # Eighth note
        {"pitch_name": "D4", "midi": 62, "start": 0.5, "end": 0.75, "duration": 0.25, "amplitude": 0.9},  # Sixteenth note - legitimate
        {"pitch_name": "E4", "midi": 64, "start": 0.75, "end": 1.25, "duration": 0.5, "amplitude": 0.7},  # Eighth note
    ]
    
    cleaned = cleanup_monophonic(notes)
    # Should preserve all three notes
    assert len(cleaned) == 3
    assert cleaned[0]["end"] == 0.5
    assert cleaned[1]["start"] == 0.5
    assert cleaned[1]["end"] == 0.75
    assert cleaned[2]["start"] == 0.75
    
    overlaps = detect_overlaps(cleaned)
    assert len(overlaps) == 0


def test_notes_with_gap():
    """Test notes with a gap between them are preserved."""
    notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 1.0, "duration": 1.0, "amplitude": 0.8},
        {"pitch_name": "E4", "midi": 64, "start": 1.5, "end": 2.5, "duration": 1.0, "amplitude": 0.9},  # 0.5 sec gap
    ]
    
    cleaned = cleanup_monophonic(notes)
    assert len(cleaned) == 2
    assert cleaned[0]["end"] == 1.0
    assert cleaned[1]["start"] == 1.5
    assert cleaned[1]["end"] == 2.5
    
    overlaps = detect_overlaps(cleaned)
    assert len(overlaps) == 0


def test_consecutive_adjacent_boundaries():
    """Test notes with nearly adjacent boundaries (within jitter threshold)."""
    notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 0.5, "duration": 0.5, "amplitude": 0.8},
        {"pitch_name": "D4", "midi": 62, "start": 0.5, "end": 1.0, "duration": 0.5, "amplitude": 0.9},  # Exactly adjacent
        {"pitch_name": "E4", "midi": 64, "start": 1.0, "end": 1.5, "duration": 0.5, "amplitude": 0.7},  # Exactly adjacent
    ]
    
    cleaned = cleanup_monophonic(notes)
    assert len(cleaned) == 3
    # Should not truncate because overlap is zero (or negative due to floating point)
    assert cleaned[0]["end"] == 0.5
    assert cleaned[1]["start"] == 0.5
    assert cleaned[1]["end"] == 1.0
    assert cleaned[2]["start"] == 1.0
    
    overlaps = detect_overlaps(cleaned)
    assert len(overlaps) == 0


def test_empty_input():
    """Test with empty input."""
    notes = []
    cleaned = cleanup_monophonic(notes)
    assert cleaned == []


def test_single_note():
    """Test with single note."""
    notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 1.0, "duration": 1.0, "amplitude": 0.8},
    ]
    cleaned = cleanup_monophonic(notes)
    assert len(cleaned) == 1
    assert cleaned[0]["end"] == 1.0


def test_overlap_with_timing_jitter():
    """Test very small overlaps (<50ms) are left as-is (timing jitter)."""
    notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 0.5, "duration": 0.5, "amplitude": 0.8},
        {"pitch_name": "D4", "midi": 62, "start": 0.49, "end": 0.99, "duration": 0.5, "amplitude": 0.9},  # 10ms early start
    ]
    
    cleaned = cleanup_monophonic(notes)
    # Should not truncate because overlap < 50ms
    assert len(cleaned) == 2
    assert cleaned[0]["end"] == 0.5
    assert cleaned[1]["start"] == 0.49
    
    overlaps = detect_overlaps(cleaned)
    # May still detect overlap due to floating point, but that's okay for this test
    # The important thing is that notes weren't modified
    assert cleaned[0]["end"] == 0.5
    assert cleaned[1]["start"] == 0.49


def test_high_overlap_ratio_truncation():
    """Test truncation when overlap is significant portion of note."""
    notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 1.0, "duration": 1.0, "amplitude": 0.8},
        {"pitch_name": "D4", "midi": 62, "start": 0.6, "end": 1.2, "duration": 0.6, "amplitude": 0.9},  # Overlap 0.4 sec (40% of first note)
    ]
    
    cleaned = cleanup_monophonic(notes)
    # Should truncate first note (overlap > 30% and second note has good amplitude)
    assert len(cleaned) == 2
    assert cleaned[0]["end"] == 0.6  # Truncated to start of second
    assert cleaned[0]["duration"] == 0.6
    assert cleaned[1]["start"] == 0.6
    assert cleaned[1]["end"] == 1.2
    
    overlaps = detect_overlaps(cleaned)
    assert len(overlaps) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
