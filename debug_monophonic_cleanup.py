#!/usr/bin/env python3
"""
Observation-only debug harness for monophonic cleanup.
Strictly imports and observes the production implementation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'src'))

from transcription.monophonic_cleanup import cleanup_monophonic, detect_overlaps
from transcription.detect_notes import detect_notes
from transcription.quantize import quantize_notes
from score.measure_builder import build_measures
from score.score import Score, Note


def format_note(note):
    """Format a note dictionary for display."""
    return (f"{note['pitch_name']} ({note['midi']}): "
            f"{note['start']:.3f}-{note['end']:.3f} "
            f"(dur={note['duration']:.3f}, amp={note['amplitude']:.3f})")


def notes_to_dict_key(notes):
    """Create a set of (pitch, start) tuples for note identification."""
    return {(note['pitch_name'], note['start']) for note in notes}


def debug_monophonic_cleanup(input_notes, max_voices=1):
    """
    Observation-only debug harness for cleanup_monophonic.
    Shows exactly what the production function does without reimplementing logic.
    """
    print("=" * 60)
    print("MONOPHONIC CLEANUP DEBUG HARNESS (OBSERVATION ONLY)")
    print("=" * 60)

    # Show input
    print("\n1. INPUT NOTES:")
    print("-" * 30)
    if not input_notes:
        print("  (empty)")
    else:
        for i, note in enumerate(input_notes):
            print(f"  [{i}] {format_note(note)}")

    # Detect overlaps before cleanup
    input_overlaps = detect_overlaps(input_notes)
    print(f"\n2. PRE-CLEANUP OVERLAPS: {len(input_overlaps)}")
    print("-" * 30)
    if input_overlaps:
        for idx1, idx2, overlap in input_overlaps:
            note1 = input_notes[idx1]
            note2 = input_notes[idx2]
            note1_str = f"{note1['pitch_name']}[{idx1}]"
            note2_str = f"{note2['pitch_name']}[{idx2}]"
            print(f"  {note1_str} <-> {note2_str}: {overlap:.3f}s")
    else:
        print("  (none)")

    # Call the actual production function (OBSERVE ONLY)
    print("\n3. CALLING PRODUCTION cleanup_monophonic()...")
    print("-" * 30)
    output_notes = cleanup_monophonic(input_notes, max_voices=max_voices)

    # Show output
    print("\n4. OUTPUT NOTES:")
    print("-" * 30)
    if not output_notes:
        print("  (empty)")
    else:
        for i, note in enumerate(output_notes):
            print(f"  [{i}] {format_note(note)}")

    # Detect overlaps after cleanup
    output_overlaps = detect_overlaps(output_notes)
    print(f"\n5. POST-CLEANUP OVERLAPS: {len(output_overlaps)}")
    print("-" * 30)
    if output_overlaps:
        for idx1, idx2, overlap in output_overlaps:
            note1 = output_notes[idx1]
            note2 = output_notes[idx2]
            note1_str = f"{note1['pitch_name']}[{idx1}]"
            note2_str = f"{note2['pitch_name']}[{idx2}]"
            print(f"  {note1_str} <-> {note2_str}: {overlap:.3f}s")
    else:
        print("  (none)")

    # Change analysis (approximate - based on pitch/start only)
    print("\n6. CHANGE ANALYSIS (APPROXIMATE - based on pitch/start only):")
    print("-" * 50)

    input_keys = notes_to_dict_key(input_notes)
    output_keys = notes_to_dict_key(output_notes)

    # Notes removed (in input but not in output)
    removed_keys = input_keys - output_keys
    # Notes added (in output but not in input) - should not happen with current algorithm
    added_keys = output_keys - input_keys
    # Notes preserved (in both)
    preserved_keys = input_keys & output_keys

    if removed_keys:
        print(f"  REMOVED NOTES ({len(removed_keys)}):")
        for note in input_notes:
            key = (note['pitch_name'], note['start'])
            if key in removed_keys:
                print(f"    - {format_note(note)}")
    else:
        print("  REMOVED NOTES: (none)")

    if added_keys:
        print(f"  ADDED NOTES ({len(added_keys)}):")
        for note in output_notes:
            key = (note['pitch_name'], note['start'])
            if key in added_keys:
                print(f"    + {format_note(note)}")
    else:
        print("  ADDED NOTES: (none)")

    if preserved_keys:
        print(f"  PRESERVED NOTES ({len(preserved_keys)}):")
        for note in input_notes:
            key = (note['pitch_name'], note['start'])
            if key in preserved_keys:
                # Check if note was modified
                matching_output = [n for n in output_notes
                                 if n['pitch_name'] == note['pitch_name'] and n['start'] == note['start']]
                if matching_output:
                    output_note = matching_output[0]
                    # Check for modifications
                    if (abs(note['end'] - output_note['end']) > 0.001 or
                        abs(note['duration'] - output_note['duration']) > 0.001):
                        print(f"    ~ MODIFIED: {format_note(note)}")
                        print(f"        → {format_note(output_note)}")
                    else:
                        print(f"    = {format_note(note)}")
                else:
                    print(f"    = {format_note(note)}")  # Should not happen
    else:
        print("  PRESERVED NOTES: (none)")

    # Summary
    print("\n7. SUMMARY:")
    print("-" * 30)
    print(f"  Input notes:  {len(input_notes)}")
    print(f"  Output notes: {len(output_notes)}")
    print(f"  Removed:      {len(removed_keys)}")
    print(f"  Added:        {len(added_keys)}")
    print(f"  Preserved:    {len(preserved_keys)}")
    print(f"  Pre-overlaps: {len(input_overlaps)}")
    print(f"  Post-overlaps:{len(output_overlaps)}")

    print("\n" + "=" * 60)
    print("END OF OBSERVATION (zero reimplementation of cleanup logic)")
    print("=" * 60)

    return output_notes


def debug_full_pipeline(wav_path: str, melody_name: str):
    """
    Observation-only debug harness for the full v0.1 pipeline.
    Shows exactly what each production function does without reimplementing logic.
    """
    print("=" * 70)
    print(f"FULL PIPELINE DEBUG HARNESS (OBSERVATION ONLY): {melody_name}")
    print("=" * 70)

    # Stage 1: Audio -> detected notes
    print(f"\n[1] DETECT NOTES: {wav_path}")
    print("-" * 50)
    try:
        detected_notes = detect_notes(wav_path)
        print(f"   Detected {len(detected_notes)} raw notes")

        if detected_notes:
            print("   Raw detected notes:")
            for i, note in enumerate(detected_notes):
                print(f"     [{i}] {note['pitch_name']} (MIDI {note['midi']}): "
                      f"{note['start']:.3f}-{note['end']:.3f}s "
                      f"(dur={note['duration']:.3f}s, amp={note['amplitude']:.3f})")
        else:
            print("   (no notes detected)")

    except Exception as e:
        print(f"   ❌ Error in detect_notes: {e}")
        return None

    # Detect overlaps before cleanup
    input_overlaps = detect_overlaps(detected_notes)
    print(f"\n   Pre-cleanup overlaps: {len(input_overlaps)}")
    if input_overlaps:
        for idx1, idx2, overlap in input_overlaps:
            note1 = detected_notes[idx1]
            note2 = detected_notes[idx2]
            print(f"     {note1['pitch_name']}[{idx1}] <-> {note2['pitch_name']}[{idx2}]: {overlap:.3f}s")

    # Stage 2: Detected notes -> cleaned notes
    print(f"\n[2] MONOPHONIC CLEANUP")
    print("-" * 50)
    cleaned_notes = cleanup_monophonic(detected_notes, max_voices=1)
    print(f"   After cleanup: {len(cleaned_notes)} notes")

    if cleaned_notes:
        print("   Cleaned notes:")
        for i, note in enumerate(cleaned_notes):
            print(f"     [{i}] {note['pitch_name']} (MIDI {note['midi']}): "
                  f"{note['start']:.3f}-{note['end']:.3f}s "
                  f"(dur={note['duration']:.3f}s, amp={note['amplitude']:.3f})")
    else:
        print("   (no notes after cleanup)")

    # Detect overlaps after cleanup
    output_overlaps = detect_overlaps(cleaned_notes)
    print(f"\n   Post-cleanup overlaps: {len(output_overlaps)}")
    if output_overlaps:
        for idx1, idx2, overlap in output_overlaps:
            note1 = cleaned_notes[idx1]
            note2 = cleaned_notes[idx2]
            print(f"     {note1['pitch_name']}[{idx1}] <-> {note2['pitch_name']}[{idx2}]: {overlap:.3f}s")

    # Change analysis for cleanup (approximate)
    print(f"\n   Cleanup change analysis (approximate - based on pitch/start only):")
    input_keys = {(n['pitch_name'], n['start']) for n in detected_notes}
    output_keys = {(n['pitch_name'], n['start']) for n in cleaned_notes}

    removed_keys = input_keys - output_keys
    added_keys = output_keys - input_keys
    preserved_keys = input_keys & output_keys

    if removed_keys:
        print(f"     Removed: {len(removed_keys)} notes")
    if added_keys:
        print(f"     Added: {len(added_keys)} notes (should not happen with current algorithm)")
    if preserved_keys:
        print(f"     Preserved: {len(preserved_keys)} notes")

    # Stage 3: Cleaned notes -> quantized notes
    print(f"\n[3] QUANTIZE NOTES (BPM=120.0)")
    print("-" * 50)
    try:
        quantized_notes = quantize_notes(cleaned_notes, bpm=120.0)
        print(f"   Quantized {len(quantized_notes)} notes")

        if quantized_notes:
            print("   Quantized notes (with beat-aligned fields):")
            for i, note in enumerate(quantized_notes):
                print(f"     [{i}] {note['pitch_name']}: "
                      f"beat_start={note['beat_start']:.2f}, "
                      f"beat_duration={note['beat_duration']:.2f} → "
                      f"quantized={note['quantized_duration']}")
        else:
            print("   (no notes after quantization)")

    except Exception as e:
        print(f"   ❌ Error in quantize_notes: {e}")
        return None

    # Stage 4: Quantized notes -> measures
    print(f"\n[4] BUILD MEASURES (4/4 time signature)")
    print("-" * 50)
    try:
        measures = build_measures(quantized_notes)
        print(f"   Built {len(measures)} measures")

        # Validate measure durations
        expected_beats = 4.0
        measure_valid = True

        print("   Measure details:")
        for i, measure in enumerate(measures):
            total_duration = sum(event.duration for event in measure.events)
            is_valid = abs(total_duration - expected_beats) < 0.001
            if not is_valid:
                measure_valid = False

            note_count = len([e for e in measure.events if isinstance(e, Note)])
            rest_count = len([e for e in measure.events if not isinstance(e, Note)])

            validity_mark = "✓" if is_valid else "❌"
            print(f"     {validity_mark} Measure {measure.number}: {total_duration:.3f} beats "
                  f"({note_count} notes, {rest_count} rests)")

            if hasattr(measure, 'events'):
                for j, event in enumerate(measure.events):
                    if isinstance(event, Note):
                        print(f"       Note {j}: {event.pitch_name} (MIDI {event.midi}) "
                              f"start={event.start_time:.3f}, duration={event.duration:.3f}")
                    else:
                        print(f"       Rest {j}: start={event.start_time:.3f}, duration={event.duration:.3f}")

        if measure_valid:
            print(f"   ✓ All measures have exactly {expected_beats:.3f} beats")
        else:
            print(f"   ❌ Some measures have incorrect duration")

    except Exception as e:
        print(f"   ❌ Error in build_measures: {e}")
        return None

    # Summary
    print(f"\n{'='*70}")
    print(f"PIPELINE SUMMARY FOR {melody_name}")
    print(f"{'='*70}")
    print(f"  Raw detected notes:    {len(detected_notes) if detected_notes else 0}")
    print(f"  After cleanup:         {len(cleaned_notes) if cleaned_notes else 0}")
    print(f"  After quantization:    {len(quantized_notes) if quantized_notes else 0}")
    print(f"  Measures built:        {len(measures) if measures else 0}")
    if measures:
        print(f"  All measures 4.0 beats: {'YES' if measure_valid else 'NO'}")
        if measures:
            total_beats = sum(sum(event.duration for event in m.events) for m in measures)
            print(f"  Total beats across all measures: {total_beats:.3f}")

    print("\n" + "=" * 70)
    print("END OF FULL PIPELINE OBSERVATION (zero reimplementation)")
    print("=" * 70)

    return {
        'detected': detected_notes,
        'cleaned': cleaned_notes,
        'quantized': quantized_notes,
        'measures': measures,
        'measure_valid': measure_valid if measures else False
    }


if __name__ == "__main__":
    # Run full pipeline observation on the first failing melody
    base_path = "/Users/user/Desktop/musiclutionv0.1/app/tests/melodies"
    wav_path = f"{base_path}/melody_001/D_major/audio.wav"
    melody_name = "melody_001"

    if os.path.exists(wav_path):
        debug_full_pipeline(wav_path, melody_name)
    else:
        print(f"Audio file not found: {wav_path}")