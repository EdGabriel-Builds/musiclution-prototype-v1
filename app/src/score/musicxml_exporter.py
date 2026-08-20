"""
MusicXML exporter for Score model.
Exports to MusicXML Partwise format using only supported features:
notes, rests, measures, time signatures, key signature (default C major).
Ignores dynamics, articulations, ties, slurs, lyrics, multiple voices.
Assumes events are sequential and fill the measure (no backup/forward).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List, Union

from .score import Score, Measure, Note, Rest


# Mapping of base beat durations to (duration_xml_per_beat, type_string) for divisions=4
# This maps the base duration (without dots) to (duration_xml_per_beat, type_string)
_BASE_DURATION_LOOKUP = {
    0.25: (1, "16th"),   # sixteenth
    0.5: (2, "eighth"),   # eighth
    1.0: (4, "quarter"),  # quarter
    2.0: (8, "half"),     # half
    4.0: (16, "whole"),   # whole
}

# Supported durations including dotted ones (in beats)
_SUPPORTED_DURATIONS = set(_BASE_DURATION_LOOKUP.keys()) | {0.75, 1.5, 3.0}  # dotted eighth, quarter, half

# Default divisions (ticks per quarter note)
_DIVISIONS = 4


def _pitch_name_to_musicxml(pitch_name: str):
    """
    Convert scientific pitch name (e.g., "C4", "D#5", "Bb3") to
    (step, alter, octave) where alter is +1 for sharp, -1 for flat, 0 for natural.
    """
    if not pitch_name:
        raise ValueError("Empty pitch name")
    # First character is step letter
    step = pitch_name[0].upper()
    if step not in "ABCDEFG":
        raise ValueError(f"Invalid step in pitch name: {pitch_name}")
    # Check for accidental
    alter = 0
    idx = 1
    if len(pitch_name) > 1 and pitch_name[1] in "#b":
        if pitch_name[1] == "#":
            alter = 1
        else:  # 'b'
            alter = -1
        idx += 1
    # The rest should be octave digits
    octave_str = pitch_name[idx:]
    if not octave_str.isdigit():
        raise ValueError(f"Invalid octave in pitch name: {pitch_name}")
    octave = int(octave_str)
    return step, alter, octave


def _duration_to_xml(beats: float):
    """
    Convert beat duration to (duration_xml, type_string, dots_count).
    Handles dotted durations by calculating the appropriate number of dots.

    Args:
        beats: Duration in beats

    Returns:
        Tuple of (duration_xml, type_string, dots_count) where:
        - duration_xml: Integer duration units for MusicXML <duration> element
        - type_string: String for MusicXML <type> element (e.g., "quarter")
        - dots_count: Number of dots to add (0, 1, or 2)

    Raises:
        ValueError: If duration not supported
    """
    # Check if it's a base duration (no dots)
    if beats in _BASE_DURATION_LOOKUP:
        duration_xml, type_str = _BASE_DURATION_LOOKUP[beats]
        return duration_xml, type_str, 0

    # Check for dotted durations (base duration * 1.5)
    # We consider a limited set of dotted durations as specified in the milestone
    # Map from total beats to the base type string (the undotted duration)
    dotted_candidates = {
        0.75: "eighth",   # dotted eighth
        1.5: "quarter",   # dotted quarter
        3.0: "half",      # dotted half
    }

    if beats in dotted_candidates:
        type_str = dotted_candidates[beats]
        # Get the base duration for this type (e.g., for "eighth", base duration is 0.5)
        base_beats = None
        for duration_val, (duration_xml_base, type_name) in _BASE_DURATION_LOOKUP.items():
            if type_name == type_str:
                base_beats = duration_val
                break
        if base_beats is None:
            raise ValueError(f"Internal error: could not find base duration for type {type_str}")

        # For dotted notes, duration_xml = base_duration_xml * 1.5
        duration_xml_base, _ = _BASE_DURATION_LOOKUP[base_beats]
        duration_xml = int(duration_xml_base * 1.5)
        return duration_xml, type_str, 1

    # If we get here, the duration is not supported
    supported = list(_BASE_DURATION_LOOKUP.keys()) + list(dotted_candidates.keys())
    raise ValueError(f"Unsupported duration: {beats}. Supported: {supported}")


def score_to_musicxml(score: Score) -> str:
    """
    Convert a Score object to a MusicXML string.
    """
    # Create root element
    score_partwise = ET.Element("score-partwise", version="4.0")

    # Work title
    work = ET.SubElement(score_partwise, "work")
    work_title = ET.SubElement(work, "work-title")
    work_title.text = score.title

    # Identification (composer)
    identification = ET.SubElement(score_partwise, "identification")
    creator = ET.SubElement(identification, "creator", type="composer")
    creator.text = score.composer

    # Part list
    part_list = ET.SubElement(score_partwise, "part-list")
    score_part = ET.SubElement(part_list, "score-part", id="P1")
    part_name = ET.SubElement(score_part, "part-name")
    part_name.text = "Instrument"

    # Part
    part = ET.SubElement(score_partwise, "part", id="P1")

    # Keep track of previous time signature to decide when to repeat attributes
    prev_ts_top = None
    prev_ts_bottom = None

    for measure in score.measures:
        # Measure element
        measure_elem = ET.SubElement(part, "measure", number=str(measure.number))

        # Attributes (include if first measure or time signature changed)
        need_attributes = (measure.number == 1) or (
            measure.time_signature_top != prev_ts_top
            or measure.time_signature_bottom != prev_ts_bottom
        )
        if need_attributes:
            attributes = ET.SubElement(measure_elem, "attributes")
            # Divisions
            divisions = ET.SubElement(attributes, "divisions")
            divisions.text = str(_DIVISIONS)
            # Key signature
            key = ET.SubElement(attributes, "key")
            fifths = ET.SubElement(key, "fifths")
            mode = ET.SubElement(key, "mode")
            # Try to get detected key from score, default to C major
            detected_fifths = 0
            detected_mode = "major"
            try:
                # Import here to avoid circular imports
                from music.key_detection import detect_key_from_score
                key_name, mode_str, confidence, detected_fifths = detect_key_from_score(score)
                detected_mode = mode_str
            except Exception:
                # If key detection fails, default to C major
                pass
            fifths.text = str(detected_fifths)
            mode.text = detected_mode
            # Time signature
            time = ET.SubElement(attributes, "time")
            beats = ET.SubElement(time, "beats")
            beats.text = str(measure.time_signature_top)
            beat_type = ET.SubElement(time, "beat-type")
            beat_type.text = str(measure.time_signature_bottom)
            # Clef (treble)
            clef = ET.SubElement(attributes, "clef")
            sign = ET.SubElement(clef, "sign")
            sign.text = "G"
            clef_line = ET.SubElement(clef, "line")
            clef_line.text = "2"

            # Update previous time signature
            prev_ts_top = measure.time_signature_top
            prev_ts_bottom = measure.time_signature_bottom

        # Events (notes/rests) in order
        for event in measure.events:
            if isinstance(event, Note):
                note_elem = ET.SubElement(measure_elem, "note")
                # Pitch
                pitch_elem = ET.SubElement(note_elem, "pitch")
                step, alter, octave = _pitch_name_to_musicxml(event.pitch_name)
                step_elem = ET.SubElement(pitch_elem, "step")
                step_elem.text = step
                if alter != 0:
                    alter_elem = ET.SubElement(pitch_elem, "alter")
                    alter_elem.text = str(alter)
                octave_elem = ET.SubElement(pitch_elem, "octave")
                octave_elem.text = str(octave)
                # Duration
                duration_xml, type_str, dots_count = _duration_to_xml(event.duration)
                duration_elem = ET.SubElement(note_elem, "duration")
                duration_elem.text = str(duration_xml)
                type_elem = ET.SubElement(note_elem, "type")
                type_elem.text = type_str
                # Add dots if needed
                for _ in range(dots_count):
                    dot_elem = ET.SubElement(note_elem, "dot")
                # Voice and staff (default 1)
                voice_elem = ET.SubElement(note_elem, "voice")
                voice_elem.text = "1"
                staff_elem = ET.SubElement(note_elem, "staff")
                staff_elem.text = "1"
            elif isinstance(event, Rest):
                rest_elem = ET.SubElement(measure_elem, "rest")
                # Duration
                duration_xml, type_str, dots_count = _duration_to_xml(event.duration)
                duration_elem = ET.SubElement(rest_elem, "duration")
                duration_elem.text = str(duration_xml)
                type_elem = ET.SubElement(rest_elem, "type")
                type_elem.text = type_str
                # Add dots if needed
                for _ in range(dots_count):
                    dot_elem = ET.SubElement(rest_elem, "dot")
                # Voice and staff (default 1)
                voice_elem = ET.SubElement(rest_elem, "voice")
                voice_elem.text = "1"
                staff_elem = ET.SubElement(rest_elem, "staff")
                staff_elem.text = "1"
            else:
                # Should not happen due to validation in Measure.__post_init__
                raise TypeError(f"Unexpected event type: {type(event)}")

    # Convert to string
    xml_str = ET.tostring(score_partwise, encoding="unicode")
    # Optionally pretty-print (indent)
    # Using ET.indent if available (Python 3.9+)
    try:
        ET.indent(score_partwise, space="    ")
        xml_str = ET.tostring(score_partwise, encoding="unicode")
    except AttributeError:
        # fallback: no pretty print
        pass
    return xml_str


# Simple test when run directly
if __name__ == "__main__":
    # Create a simple score for testing
    score = Score(title="Test Score", composer="Test Composer", tempo_bpm=120.0)

    # Measure 1: 4/4, quarter note C4, quarter rest, half note D4
    m1 = Measure(number=1, time_signature_top=4, time_signature_bottom=4)
    m1.add_event(Note(pitch_name="C4", midi=60, start_time=0.0, duration=1.0, velocity=0.8))
    m1.add_event(Rest(start_time=1.0, duration=1.0))
    m1.add_event(Note(pitch_name="D4", midi=62, start_time=2.0, duration=2.0, velocity=0.6))
    score.add_measure(m1)

    # Measure 2: 3/4, whole note? Actually whole note is 4 beats, can't fit in 3/4. We'll use half + quarter.
    m2 = Measure(number=2, time_signature_top=3, time_signature_bottom=4)
    m2.add_event(Note(pitch_name="E4", midi=64, start_time=0.0, duration=2.0, velocity=0.7))
    m2.add_event(Note(pitch_name="G4", midi=67, start_time=2.0, duration=1.0, velocity=0.7))
    score.add_measure(m2)

    xml_output = score_to_musicxml(score)
    print("Generated MusicXML:")
    print(xml_output)
    # Optionally write to file
    with open("/tmp/test_output.musicxml", "w", encoding="utf-8") as f:
        f.write(xml_output)
    print("\nWritten to /tmp/test_output.musicxml")