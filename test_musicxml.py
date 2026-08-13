#!/usr/bin/env python3
"""
Test script for MusicXML exporter.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'src'))

from score.musicxml_exporter import score_to_musicxml
from score.score import Score, Measure, Note, Rest

def test_simple_melody():
    """Test exporting a simple melody with quarter notes."""
    score = Score(title="Test Melody", composer="Test Composer", tempo_bpm=120.0)

    # Measure 1: C4 quarter, D4 quarter, E4 quarter, F4 quarter
    m1 = Measure(number=1, time_signature_top=4, time_signature_bottom=4)
    m1.add_event(Note(pitch_name="C4", midi=60, start_time=0.0, duration=1.0, velocity=0.8))
    m1.add_event(Note(pitch_name="D4", midi=62, start_time=1.0, duration=1.0, velocity=0.8))
    m1.add_event(Note(pitch_name="E4", midi=64, start_time=2.0, duration=1.0, velocity=0.8))
    m1.add_event(Note(pitch_name="F4", midi=65, start_time=3.0, duration=1.0, velocity=0.8))
    score.add_measure(m1)

    xml_output = score_to_musicxml(score)
    print("Simple melody MusicXML:")
    print(xml_output)
    print()

def test_dotted_rhythms():
    """Test exporting dotted rhythms."""
    score = Score(title="Dotted Rhythms Test", composer="Test Composer", tempo_bpm=120.0)

    # Measure 1: Dotted half note C4 (3 beats), quarter note D4 (1 beat)
    m1 = Measure(number=1, time_signature_top=4, time_signature_bottom=4)
    m1.add_event(Note(pitch_name="C4", midi=60, start_time=0.0, duration=3.0, velocity=0.8))  # dotted half
    m1.add_event(Note(pitch_name="D4", midi=62, start_time=3.0, duration=1.0, velocity=0.8))  # quarter
    score.add_measure(m1)

    # Measure 2: Half note E4 (2 beats), dotted quarter F#4 (1.5 beats)
    m2 = Measure(number=2, time_signature_top=4, time_signature_bottom=4)
    m2.add_event(Note(pitch_name="E4", midi=64, start_time=0.0, duration=2.0, velocity=0.8))  # half
    m2.add_event(Note(pitch_name="F#4", midi=66, start_time=2.0, duration=1.5, velocity=0.8))  # dotted quarter
    score.add_measure(m2)

    xml_output = score_to_musicxml(score)
    print("Dotted rhythms MusicXML:")
    print(xml_output)
    print()

def test_sixteenth_notes():
    """Test exporting sixteenth notes."""
    score = Score(title="Sixteenth Notes Test", composer="Test Composer", tempo_bpm=120.0)

    # Measure 1: Four sixteenth notes
    m1 = Measure(number=1, time_signature_top=4, time_signature_bottom=4)
    m1.add_event(Note(pitch_name="C4", midi=60, start_time=0.0, duration=0.25, velocity=0.8))
    m1.add_event(Note(pitch_name="D4", midi=62, start_time=0.25, duration=0.25, velocity=0.8))
    m1.add_event(Note(pitch_name="E4", midi=64, start_time=0.5, duration=0.25, velocity=0.8))
    m1.add_event(Note(pitch_name="F4", midi=65, start_time=0.75, duration=0.25, velocity=0.8))
    score.add_measure(m1)

    xml_output = score_to_musicxml(score)
    print("Sixteenth notes MusicXML:")
    print(xml_output)
    print()

def test_rests():
    """Test exporting rests."""
    score = Score(title="Rests Test", composer="Test Composer", tempo_bpm=120.0)

    # Measure 1: Quarter rest, quarter note, quarter rest, quarter note
    m1 = Measure(number=1, time_signature_top=4, time_signature_bottom=4)
    m1.add_event(Rest(start_time=0.0, duration=1.0))
    m1.add_event(Note(pitch_name="C4", midi=60, start_time=1.0, duration=1.0, velocity=0.8))
    m1.add_event(Rest(start_time=2.0, duration=1.0))
    m1.add_event(Note(pitch_name="D4", midi=62, start_time=3.0, duration=1.0, velocity=0.8))
    score.add_measure(m1)

    xml_output = score_to_musicxml(score)
    print("Rests MusicXML:")
    print(xml_output)
    print()

if __name__ == "__main__":
    test_simple_melody()
    test_dotted_rhythms()
    test_sixteenth_notes()
    test_rests()