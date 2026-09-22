#!/usr/bin/env python3
"""
Debug script to see exactly what's happening in the measure building process.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'src'))

from transcription.detect_notes import detect_notes
from transcription.quantize import quantize_notes
from score.measure_builder import build_measures
from score.score import Note

def debug_full_pipeline(wav_path, melody_name):
    print(f"\n{'='*60}")
    print(f"FULL PIPELINE DEBUG: {melody_name}")
    print(f"{'='*60}")

    # Step 1: Detect notes
    print("[1] Detecting notes from audio...")
    detected = detect_notes(wav_path)
    print(f"   Detected {len(detected)} raw notes")

    # Show first few raw notes
    print("   First 3 raw notes:")
    for i, note in enumerate(detected[:3]):
        print(f"     {note['pitch_name']} (MIDI {note['midi']}) "
              f"start={note['start']:.3f}s, duration={note['duration']:.3f}s")

    # Step 2: Quantize with CONTROLLED BPM=120.0
    print(f"\n[2] Quantizing with CONTROLLED BPM=120.0...")
    quantized = quantize_notes(detected, bpm=120.0)

    print(f"   ✓ Quantized {len(quantized)} notes")

    # Show quantization details
    print("   Quantization details:")
    for i, note in enumerate(quantized[:5]):
        start = float(note["beat_start"])
        duration = float(note["beat_duration"])
        qd = note["quantized_duration"]
        print(f"     {i+1}. {note['pitch_name']:4s} "
              f"start={start:5.2f} beat, "
              f"duration={duration:5.2f} beat → "
              f"[{qd}]")

    # Step 3: Build measures
    print(f"\n[3] Building measures...")
    measures = build_measures(quantized)
    print(f"   Built {len(measures)} measures")

    # Detailed measure analysis
    print(f"\n   Measure details:")
    all_valid = True
    for i, measure in enumerate(measures):
        measure_number = measure.number
        total_duration = sum(event.duration for event in measure.events)
        note_count = len([e for e in measure.events if isinstance(e, Note)])
        rest_count = len([e for e in measure.events if not isinstance(e, Note)])

        # Check if measure is exactly 4.0 beats
        is_exactly_4 = abs(total_duration - 4.0) < 0.001
        if not is_exactly_4:
            all_valid = False

        status = "✓" if is_exactly_4 else "✗"
        print(f"     {status} Measure {measure_number}: "
              f"{total_duration:5.3f} beats "
              f"({note_count} notes, {rest_count} rests)"
              f"{' *' if not is_exactly_4 else ''}")

        # Show what's in the measure
        if note_count > 0 and i < 2:  # Show details for first 2 measures
            print(f"       Events:")
            for j, event in enumerate(measure.events):
                if isinstance(event, Note):
                    print(f"         {j+1}. Note {event.pitch_name} "
                          f"start={event.start_time:5.2f} "
                          f"dur={event.duration:5.2f} "
                          f"vel={event.velocity:.2f}")
                else:
                    print(f"         {j+1}. Rest "
                          f"start={event.start_time:5.2f} "
                          f"dur={event.duration:5.2f}")

    print(f"\n   Summary: {'All measures exactly 4.0 beats' if all_valid else 'Some measures NOT exactly 4.0 beats'}")

    return all_valid

def main():
    base_path = "/Users/user/Desktop/musiclutionv0.1/app/tests/melodies"

    melodies = [
        ("melody_001", f"{base_path}/melody_001/D_major/audio.wav"),
        ("melody_002", f"{base_path}/melody_002/Eb_major/audio.wav"),
        ("melody_003", f"{base_path}/melody_003/E_major/audio.wav"),
    ]

    all_passed = True
    for melody_name, wav_path in melodies:
        if os.path.exists(wav_path):
            passed = debug_full_pipeline(wav_path, melody_name)
            if not passed:
                all_passed = False
        else:
            print(f"File not found: {wav_path}")
            all_passed = False

    print(f"\n{'='*60}")
    print(f"FINAL RESULT: {'ALL MEASURES VALID' if all_passed else 'SOME MEASURES INVALID'}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()