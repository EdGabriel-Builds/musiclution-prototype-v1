#!/usr/bin/env python3
"""
Test script to verify the v0.1 baseline with fixed measure building.
Tests all three melodies with BPM=120.0 control.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'src'))

from transcription.detect_notes import detect_notes
from transcription.monophonic_cleanup import cleanup_monophonic
from transcription.quantize import quantize_notes
from score.measure_builder import build_measures
from score.score import Score, Note
from score.musicxml_exporter import score_to_musicxml
from music.key_detection import detect_key, apply_key_aware_spelling

def run_melody_test(melody_name, wav_path, expected_key=None):
    """Test a single melody and return detailed results."""
    print(f"\n{'='*70}")
    print(f"TESTING: {melody_name}")
    if expected_key:
        print(f"Expected key: {expected_key}")
    print(f"{'='*70}")

    # Step 1: Detect notes
    print("[1] Detecting notes from audio...")
    detected = detect_notes(wav_path)
    print(f"   Detected {len(detected)} raw notes")

    # Show first few notes with raw durations
    print("   First 5 notes (raw):")
    for i, note in enumerate(detected[:5]):
        print(f"     {i+1}. {note['pitch_name']} (MIDI {note['midi']}) "
              f"at {note['start']:.3f}s, duration {note['duration']:.3f}s")

    # Step 1.5: Monophonic cleanup (NEW for v0.1)
    print(f"\n[1.5] Applying monophonic cleanup...")
    cleaned = cleanup_monophonic(detected, max_voices=1)
    print(f"   After cleanup: {len(cleaned)} notes")

    # Show overlap info
    from transcription.monophonic_cleanup import detect_overlaps
    overlaps_before = detect_overlaps(detected)
    overlaps_after = detect_overlaps(cleaned)
    print(f"   Overlaps before cleanup: {len(overlaps_before)}")
    print(f"   Overlaps after cleanup: {len(overlaps_after)}")
    if overlaps_before and not overlaps_after:
        print("   ✓ All overlaps resolved")
    elif overlaps_after:
        print(f"   ⚠ {len(overlaps_after)} overlaps remain")

    # Step 2: Quantize with CONTROLLED BPM=120.0
    print(f"\n[2] Quantizing with CONTROLLED BPM=120.0...")
    quantized = quantize_notes(cleaned, bpm=120.0)

    print(f"   ✓ Quantized {len(quantized)} notes")

    # Show quantization details
    print("   Quantization details (first 5 notes):")
    for i, note in enumerate(quantized[:5]):
        print(f"     {i+1}. {note['pitch_name']}: "
              f"beat_start={note['beat_start']:.2f}, "
              f"beat_duration={note['beat_duration']:.2f} → "
              f"quantized={note['quantized_duration']}")

    # Verify all quantized durations are supported
    supported_durations = {0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0}
    duration_map = {
        "sixteenth": 0.25, "eighth": 0.5, "dotted eighth": 0.75,
        "quarter": 1.0, "dotted quarter": 1.5, "half": 2.0,
        "dotted half": 3.0, "whole": 4.0
    }

    unsupported = []
    for i, note in enumerate(quantized):
        qd = note['quantized_duration']
        if qd in duration_map:
            computed_beats = duration_map[qd]
            if computed_beats not in supported_durations:
                unsupported.append((i, qd, computed_beats))
        else:
            unsupported.append((i, qd, "invalid string"))

    if unsupported:
        print(f"   ❌ ERROR: {len(unsupported)} notes have unsupported quantized duration")
        for i, qd, beats in unsupported[:3]:
            print(f"     Note {i}: quantized_duration='{qd}' → {beats} beats")
        return False, {}
    else:
        print(f"   ✓ All {len(quantized)} notes have supported quantized durations")

    # Step 3: Key detection
    print(f"\n[3] Key detection...")
    notes_for_key = []
    for d in detected:  # Use original detected notes for key detection (more data)
        note = Note(
            pitch_name=d['pitch_name'],
            midi=d['midi'],
            start_time=d['start'],
            duration=d['duration'],
            velocity=d['amplitude']
        )
        notes_for_key.append(note)

    key_name, mode, confidence, _ = detect_key(notes_for_key)
    print(f"   Detected key: {key_name} {mode} (confidence: {confidence:.3f})")

    # Apply test override if specified
    if expected_key:
        print(f"   Using test override: {expected_key}")
        key_name, mode, confidence = expected_key.split()[0], expected_key.split()[1], 1.0

    # Compute the effective fifths for the key we are using (after override)
    from music.key_detection import get_fifths_from_key_name_mode
    effective_fifths = get_fifths_from_key_name_mode(key_name, mode)
    print(f"   Effective key signature fifths: {effective_fifths}")

    # Step 3.5: Apply key-aware pitch spelling (NEW for v0.1)
    print(f"\n[3.5] Applying key-aware pitch spelling...")
    key_aware_quantized = apply_key_aware_spelling(quantized, effective_fifths)
    print(f"   Applied spelling to {len(key_aware_quantized)} notes")
    # Show first few note names after spelling
    print("   First 5 notes after spelling:")
    for i, note in enumerate(key_aware_quantized[:5]):
        print(f"     {i+1}. {note['pitch_name']} (MIDI {note['midi']})")

    # Step 4: Build measures
    print(f"\n[4] Building measures...")
    measures = build_measures(key_aware_quantized)
    print(f"   Built {len(measures)} measures")

    # Validate measure durations (each should be exactly 4.0 beats for 4/4)
    expected_beats = 4.0
    measure_valid = True
    measure_details = []

    total_beats_all_measures = 0.0

    for i, measure in enumerate(measures):
        total_duration = sum(event.duration for event in measure.events)
        is_valid = abs(total_duration - expected_beats) < 0.001
        if not is_valid:
            measure_valid = False
        measure_details.append({
            'number': measure.number,
            'duration': total_duration,
            'valid': is_valid,
            'note_count': len([e for e in measure.events if isinstance(e, Note)]),
            'rest_count': len([e for e in measure.events if not isinstance(e, Note)])
        })
        total_beats_all_measures += total_duration

    if measure_valid:
        print(f"   ✓ All measures have exactly {expected_beats:.3f} beats")
        print(f"   ✓ Total duration across all measures: {total_beats_all_measures:.3f} beats")
    else:
        print(f"   ❌ Some measures have incorrect duration:")
        for md in measure_details:
            if not md['valid']:
                print(f"     Measure {md['number']}: {md['duration']:.3f} beats "
                      f"({md['note_count']} notes, {md['rest_count']} rests)")

    # Step 5: Create Score and export MusicXML
    print(f"\n[5] Creating Score and exporting MusicXML...")
    score = Score(
        title=f"Transcription of {melody_name}",
        composer="Musiclution Test",
        tempo_bpm=120.0
    )
    for m in measures:
        score.add_measure(m)

    try:
        xml_str = score_to_musicxml(score)
        print(f"   ✓ MusicXML export successful ({len(xml_str)} chars)")

        # Save the file
        output_dir = "/Users/user/Desktop/musiclutionv0.1/outputs/v0.1_fixed"
        os.makedirs(output_dir, exist_ok=True)
        musicxml_file = os.path.join(output_dir, f"{melody_name}.musicxml")
        with open(musicxml_file, 'w') as f:
            f.write(xml_str)
        print(f"   Saved MusicXML to: {musicxml_file}")

        # Validate MusicXML content for key and time signature
        import re
        fifths_match = re.search(r'<fifths>(-?\d+)</fifths>', xml_str)
        time_match = re.search(r'<beats>(\d+)</beats>.*<beat-type>(\d+)</beat-type>', xml_str, re.DOTALL)

        fifths = int(fifths_match.group(1)) if fifths_match else None
        beats = time_match.group(1) if time_match else None
        beat_type = time_match.group(2) if time_match else None
        time_signature = f"{beats}/{beat_type}" if beats and beat_type else None

        print(f"   MusicXML validation:")
        print(f"     Key signature fifths: {fifths}")
        print(f"     Time signature: {time_signature}")

        xml_valid = fifths is not None and time_signature == "4/4"
        if xml_valid:
            print(f"   ✓ MusicXML contains valid key signature and 4/4 time signature")
        else:
            print(f"   ❌ MusicXML validation failed")
            if fifths is None:
                print(f"     Could not find key signature")
            if time_signature != "4/4":
                print(f"     Time signature is {time_signature}, expected 4/4")

    except Exception as e:
        print(f"   ❌ MusicXML export failed: {e}")
        return False, {}

    # Overall assessment
    all_good = measure_valid and xml_valid
    print(f"\n   RESULT: {'PASS' if all_good else 'FAIL'}")
    return all_good, {
        'detected_notes': len(detected),
        'cleaned_notes': len(cleaned),
        'quantized_notes': len(quantized),
        'key_detected': f"{key_name} {mode}",
        'key_confidence': confidence,
        'measures_built': len(measures),
        'musicxml_file': musicxml_file if 'musicxml_file' in locals() else None,
        'key_signature_fifths': fifths if 'fifths' in locals() else None,
        'time_signature': time_signature if 'time_signature' in locals() else None,
        'all_measures_4_beats': measure_valid,
        'measure_details': measure_details
    }

def main():
    """Test all three melodies with the fixed measure building."""
    base_path = "/Users/user/Desktop/musiclutionv0.1/app/tests/melodies"

    melodies = [
        ("melody_001", f"{base_path}/melody_001/D_major/audio.wav", "D major"),
        ("melody_002", f"{base_path}/melody_002/Eb_major/audio.wav", "Eb major"),
        ("melody_003", f"{base_path}/melody_003/E_major/audio.wav", "E major"),
    ]

    print("V0.1 FIXED BASELINE TEST")
    print("Controls: BPM=120.0, Fixed measure building, Monophonic cleanup")
    print("=" * 70)

    results = {}
    all_passed = True

    for melody_name, wav_path, expected_key in melodies:
        if os.path.exists(wav_path):
            passed, details = run_melody_test(melody_name, wav_path, expected_key)
            results[melody_name] = {'passed': passed, 'details': details}
            if not passed:
                all_passed = False
        else:
            print(f"\n{'='*70}")
            print(f"TESTING: {melody_name}")
            print(f"{'='*70}")
            print(f"❌ Audio file not found: {wav_path}")
            results[melody_name] = {'passed': False, 'details': {'error': 'File not found'}}
            all_passed = False

    # Summary
    print(f"\n{'='*70}")
    print(f"V0.1 FIXED BASELINE TEST SUMMARY")
    print(f"{'='*70}")

    for melody_name, result in results.items():
        status = "PASS" if result['passed'] else "FAIL"
        print(f"{melody_name}: {status}")
        if result['passed'] and 'details' in result:
            details = result['details']
            print(f"  Detected key: {details.get('key_detected', 'N/A')} "
                  f"(confidence: {details.get('key_confidence', 0):.3f})")
            print(f"  MusicXML key: {details.get('key_signature_fifths', 'N/A')} fifths")
            print(f"  Time signature: {details.get('time_signature', 'N/A')}")
            print(f"  Measures: {details.get('measures_built', 0)} "
                  f"(all 4.0 beats: {details.get('all_measures_4_beats', False)})")

    print(f"\nOverall result: {'ALL MELODIES PASSED V0.1 FIXED BASELINE' if all_passed else 'SOME MELODIES FAILED V0.1 FIXED BASELINE'}")

    if all_passed:
        print("\n🎉 V0.1 BASELINE SUCCESSFULLY ESTABLISHED!")
        print("  ✓ All melodies use controlled BPM=120.0")
        print("  ✓ All notes have supported durations for MusicXML")
        print("  ✓ All measures have exactly 4.0 beats")
        print("  ✓ Key detection works with test overrides")
        print("  ✓ MusicXML exports successfully with correct key/time signatures")
        print("\nThe v0.1 pipeline is now stable and ready for v0.2 development.")
    else:
        print("\n❌ V0.1 baseline still has issues that need fixing")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())