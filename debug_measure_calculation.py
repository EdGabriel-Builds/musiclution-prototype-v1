#!/usr/bin/env python3
"""
Debug script to understand what's happening in measure building.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'src'))

from transcription.detect_notes import detect_notes
from transcription.quantize import quantize_notes
from typing import Dict

# Mapping from quantized duration string to beats (quarter note beats)
_DURATION_TO_BEATS = {
    "whole": 4.0,
    "dotted half": 3.0,
    "half": 2.0,
    "dotted quarter": 1.5,
    "quarter": 1.0,
    "dotted eighth": 0.75,
    "eighth": 0.5,
    "sixteenth": 0.25,
}

def _duration_from_quantized(note_dict: Dict) -> float:
    """
    Return duration in beats for a note, preferring the quantized duration if available.
    """
    if "quantized_duration" in note_dict:
        qd = note_dict["quantized_duration"]
        if qd in _DURATION_TO_BEATS:
            return float(_DURATION_TO_BEATS[qd])
    # Fallback to raw beat_duration (should already be quantized-ish, but we keep for safety)
    return float(note_dict.get("beat_duration", 0.0))

def debug_measure_calculation(wav_path, melody_name):
    print(f"\nDebugging measure calculation for: {melody_name}")
    print("=" * 60)

    # Detect notes
    detected = detect_notes(wav_path)
    print(f"Detected {len(detected)} raw notes")

    # Quantize with CONTROLLED BPM=120.0
    print(f"Quantizing with CONTROLLED BPM=120.0...")
    quantized = quantize_notes(detected, bpm=120.0)

    print(f"\nAnalyzing {len(quantized)} quantized notes:")

    # Calculate what each note contributes in terms of start, end, duration
    total_duration_all_notes = 0.0

    for i, note in enumerate(quantized):
        start = float(note["beat_start"])
        duration = float(_duration_from_quantized(note))
        end = start + duration
        total_duration_all_notes += duration

        if i < 10:  # Show first 10 notes
            print(f"  Note {i+1:2d}: {note['pitch_name']:4s} "
                  f"start={start:5.2f} "
                  f"duration={duration:5.2f} "
                  f"end={end:5.2f} "
                  f"[{note['quantized_duration']}]")

    print(f"\nTotal duration of all notes: {total_duration_all_notes:.3f} beats")
    print(f"This should fill {total_duration_all_notes / 4.0:.2f} measures of 4/4 time")

    # Now let's see what measure each note belongs to
    print(f"\nNote measure assignments:")
    measure_totals = {}  # measure_number -> total duration of notes in that measure

    for i, note in enumerate(quantized):
        start = float(note["beat_start"])
        duration = float(_duration_from_quantized(note))
        end = start + duration

        # Determine which measures this note spans
        start_measure = int(start // 4.0) + 1
        end_measure = int((end - 1e-9) // 4.0) + 1  # Subtract small epsilon to handle boundary case

        if i < 10:  # Show first 10 notes
            marker = " *" if start_measure != end_measure else ""
            print(f"  Note {i+1:2d}: {note['pitch_name']:4s} "
                  f"[{start:5.2f}, {end:5.2f}) "
                  f"measures {start_measure} to {end_measure}{marker}")

        # If note is within one measure
        if start_measure == end_measure:
            if start_measure not in measure_totals:
                measure_totals[start_measure] = 0.0
            measure_totals[start_measure] += duration
        else:
            # Note spans multiple measures
            # First partial: from start to end of start_measure
            first_measure_end = start_measure * 4.0
            first_duration = first_measure_end - start
            if start_measure not in measure_totals:
                measure_totals[start_measure] = 0.0
            measure_totals[start_measure] += first_duration

            # Middle full measures (if any)
            for m in range(start_measure + 1, end_measure):
                if m not in measure_totals:
                    measure_totals[m] = 0.0
                measure_totals[m] += 4.0

            # Last partial: from start of end_measure to end
            last_measure_start = (end_measure - 1) * 4.0
            last_duration = end - last_measure_start
            if end_measure not in measure_totals:
                measure_totals[end_measure] = 0.0
            measure_totals[end_measure] += last_duration

    print(f"\nCalculated measure totals (before adding rests):")
    for measure_num in sorted(measure_totals.keys()):
        total = measure_totals[measure_num]
        marker = " *" if abs(total - 4.0) > 0.001 else ""
        print(f"  Measure {measure_num}: {total:.3f} beats{marker}")

    # Show what rests would be needed
    print(f"\nRests needed to make each measure exactly 4.0 beats:")
    for measure_num in sorted(measure_totals.keys()):
        total = measure_totals[measure_num]
        rest_needed = 4.0 - total
        if abs(rest_needed) > 0.001:
            print(f"  Measure {measure_num}: need {rest_needed:+.3f} beats rest")
        else:
            print(f"  Measure {measure_num}: already 4.0 beats")

if __name__ == "__main__":
    base_path = "/Users/user/Desktop/musiclutionv0.1/app/tests/melodies"

    for melody_info in [
        ("melody_001", f"{base_path}/melody_001/D_major/audio.wav"),
        ("melody_002", f"{base_path}/melody_002/Eb_major/audio.wav"),
        ("melody_003", f"{base_path}/melody_003/E_major/audio.wav"),
    ]:
        melody_name, wav_path = melody_info
        if os.path.exists(wav_path):
            debug_measure_calculation(wav_path, melody_name)
        else:
            print(f"File not found: {wav_path}")