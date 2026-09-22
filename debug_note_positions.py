#!/usr/bin/env python3
"""
Debug script to see exactly what note positions are after quantization and grid quantization.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'src'))

from transcription.detect_notes import detect_notes
from transcription.quantize import quantize_notes
from score.measure_builder import _quantize_position_to_grid, _duration_from_quantized

def debug_note_positions(wav_path, melody_name):
    print(f"\n{'='*60}")
    print(f"NOTE POSITIONS DEBUG: {melody_name}")
    print(f"{'='*60}")

    # Detect notes
    detected = detect_notes(wav_path)
    print(f"Detected {len(detected)} raw notes")

    # Quantize with CONTROLLED BPM=120.0
    print(f"Quantizing with CONTROLLED BPM=120.0...")
    quantized = quantize_notes(detected, bpm=120.0)

    print(f"\nAfter quantization and grid positioning:")
    print(f"{'Note':<4} {'Pitch':<6} {'Raw Start':<10} {'Quant Start':<12} {'Duration':<10} {'End Pos':<10} {'Measure Start'}")
    print(f"{'-'*70}")

    total_duration_all_notes = 0.0
    measure_assignments = []  # list of (note_idx, measure_number, start_in_measure, duration_in_measure)

    for i, note in enumerate(quantized):
        # Extract values
        pitch_name = note["pitch_name"]
        raw_start_sec = note["start"]  # in seconds
        raw_duration_sec = note["duration"]  # in seconds

        # Convert to beats using BPM=120.0
        beats_per_second = 120.0 / 60.0  # 2.0
        beat_start = raw_start_sec * beats_per_second
        beat_duration = raw_duration_sec * beats_per_second

        # Get quantized duration from quantization step
        if "quantized_duration" in note and note["quantized_duration"] in _duration_from_quantized.__globals__['_DURATION_TO_BEATS']:
            qd_duration = float(_duration_from_quantized.__globals__['_DURATION_TO_BEATS'][note["quantized_duration"]])
        else:
            # Fallback
            qd_duration = _duration_from_quantized(note)

        # Quantize start position to grid
        grid_start = _quantize_position_to_grid(beat_start, 0.25)

        # Calculate end position
        grid_end = grid_start + qd_duration

        total_duration_all_notes += qd_duration

        # Determine measure assignment
        measure_number = int(grid_start // 4.0) + 1
        measure_start_pos = 4.0 * (measure_number - 1)
        start_in_measure = grid_start - measure_start_pos

        measure_assignments.append((i, measure_number, start_in_measure, qd_duration, grid_start, grid_end))

        if i < 15:  # Show first 15 notes
            print(f"{i+1:<4} {pitch_name:<6} {beat_start:<10.2f} {grid_start:<12.2f} {qd_duration:<10.2f} {grid_end:<10.2f} {measure_number}")

    print(f"\nTotal duration of all notes: {total_duration_all_notes:.3f} beats")
    print(f"This should fill {total_duration_all_notes / 4.0:.2f} measures of 4/4 time")

    # Now simulate measure building
    print(f"\nSimulating measure assignment:")
    measure_totals = {}  # measure_number -> total duration

    for i, measure_num, start_in_meas, duration, grid_start, grid_end in measure_assignments:
        # How much of this note fits in the current measure?
        measure_start_pos = 4.0 * (measure_num - 1)
        measure_end_pos = 4.0 * measure_num

        # Note spans from grid_start to grid_end
        # Calculate overlap with this measure
        overlap_start = max(grid_start, measure_start_pos)
        overlap_end = min(grid_end, measure_end_pos)
        overlap_duration = max(0.0, overlap_end - overlap_start)

        if measure_num not in measure_totals:
            measure_totals[measure_num] = 0.0
        measure_totals[measure_num] += overlap_duration

        # Also check if it spans to next measure
        if grid_end > measure_end_pos:
            next_measure_num = measure_num + 1
            next_measure_start = 4.0 * (next_measure_num - 1)
            next_measure_end = 4.0 * next_measure_num

            overlap_start_next = max(grid_start, next_measure_start)
            overlap_end_next = min(grid_end, next_measure_end)
            overlap_duration_next = max(0.0, overlap_end_next - overlap_start_next)

            if next_measure_num not in measure_totals:
                measure_totals[next_measure_num] = 0.0
            measure_totals[next_measure_num] += overlap_duration_next

    print(f"\nSimulated measure totals:")
    for measure_num in sorted(measure_totals.keys()):
        total = measure_totals[measure_num]
        marker = " *" if abs(total - 4.0) > 0.001 else ""
        print(f"  Measure {measure_num}: {total:.3f} beats{marker}")

if __name__ == "__main__":
    base_path = "/Users/user/Desktop/musiclutionv0.1/app/tests/melodies"

    for melody_info in [
        ("melody_001", f"{base_path}/melody_001/D_major/audio.wav"),
        ("melody_002", f"{base_path}/melody_002/Eb_major/audio.wav"),
        ("melody_003", f"{base_path}/melody_003/E_major/audio.wav"),
    ]:
        melody_name, wav_path = melody_info
        if os.path.exists(wav_path):
            debug_note_positions(wav_path, melody_name)
        else:
            print(f"File not found: {wav_path}")