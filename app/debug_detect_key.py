#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from music.key_detection import _scale_mask
from score.score import Note

def debug_detect_key(notes):
    """Debug version of detect_key to see what's happening"""
    print("=== DEBUG DETECT_KEY ===")

    # Count pitch-class occurrences and capture the first note's pitch class.
    pc_count = [0] * 12
    total = 0
    first_pc = None
    for i, n in enumerate(notes):
        pc = n.midi % 12
        pc_count[pc] += 1
        total += 1
        if i == 0:
            first_pc = pc
        print(f"  Note {i}: {n.pitch_name} (MIDI {n.midi}) -> PC {pc}")

    print(f"\nPC counts: {pc_count}")
    print(f"Total notes: {total}")
    print(f"First PC: {first_pc}")

    if total == 0:
        # No notes: default to C major with zero confidence
        return ('C', 'major', 0.0)

    best_score = -1          # highest score seen
    second_best = -1         # second highest score seen
    best_tonic = 0           # tonic of the best key
    best_mode = 'major'      # mode of the best key ('major' or 'minor')

    MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
    MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

    print(f"\nProcessing each tonic:")
    for tonic in range(12):
        # Major scale
        major_mask = _scale_mask(tonic, MAJOR_INTERVALS)
        major_score = sum(pc_count[i] for i in range(12) if major_mask[i])
        # Update best and second best
        if major_score > best_score:
            second_best = best_score
            best_score = major_score
            best_tonic = tonic
            best_mode = 'major'
            print(f"  Tonic {tonic} (Major): score={major_score} -> NEW BEST")
        elif major_score == best_score:
            second_best = best_score
            print(f"  Tonic {tonic} (Major): score={major_score} -> EQUAL TO BEST")
        elif major_score > second_best:
            second_best = major_score
            print(f"  Tonic {tonic} (Major): score={major_score} -> NEW SECOND BEST")
        else:
            print(f"  Tonic {tonic} (Major): score={major_score}")

        # Minor scale
        minor_mask = _scale_mask(tonic, MINOR_INTERVALS)
        minor_score = sum(pc_count[i] for i in range(12) if minor_mask[i])
        # Update best and second best
        if minor_score > best_score:
            second_best = best_score
            best_score = minor_score
            best_tonic = tonic
            best_mode = 'minor'
            print(f"  Tonic {tonic} (Minor): score={minor_score} -> NEW BEST")
        elif minor_score == best_score:
            # Tie for best score - don't update second_best
            print(f"  Tonic {tonic} (Minor): score={minor_score} -> EQUAL TO BEST (no second_best update)")
        elif minor_score > second_best:
            second_best = minor_score
            print(f"  Tonic {tonic} (Minor): score={minor_score} -> NEW SECOND BEST")
        else:
            print(f"  Tonic {tonic} (Minor): score={minor_score}")

    print(f"\nAfter processing all tonics:")
    print(f"  best_score = {best_score} (tonic {best_tonic}, {best_mode})")
    print(f"  second_best = {second_best}")
    print(f"  Tie? {best_score == second_best}")

    # If there's a tie for best score, resolve it using the first note's pitch class.
    # We need to check if there are multiple keys achieving the best score.
    if best_score == second_best:
        print(f"\nTIE BREAKING:")
        # There's a tie for first place. Find all keys with score == best_score.
        candidates = []
        for tonic in range(12):
            major_score = sum(pc_count[i] for i in range(12) if _scale_mask(tonic, MAJOR_INTERVALS)[i])
            minor_score = sum(pc_count[i] for i in range(12) if _scale_mask(tonic, MINOR_INTERVALS)[i])
            if major_score == best_score:
                candidates.append((tonic, 'major'))
                print(f"  Found candidate: Tonic {tonic} (Major) with score {major_score}")
            if minor_score == best_score:
                candidates.append((tonic, 'minor'))
                print(f"  Found candidate: Tonic {tonic} (Minor) with score {minor_score}")

        print(f"Candidates: {candidates}")

        # If we have candidates, choose the one whose tonic matches first_pc
        if first_pc is not None:
            chosen = None
            for tonic, mode in candidates:
                if tonic == first_pc:
                    chosen = (tonic, mode)
                    print(f"  Found match: tonic {tonic} == first_pc {first_pc} -> SELECTING")
                    break
            if chosen is not None:
                best_tonic, best_mode = chosen
                print(f"  Selected: tonic {best_tonic}, mode '{best_mode}'")
            elif candidates:
                # Fallback to first candidate
                best_tonic, best_mode = candidates[0]
                print(f"  No match found, using first candidate: {candidates[0]}")
        elif candidates:
            # No first_pc (shouldn't happen if we have notes) but fallback anyway
            best_tonic, best_mode = candidates[0]
            print(f"  No first_pc, using first candidate: {candidates[0]}")

    # Confidence: if there is a clear winner (best > second), use best/total; else 0.
    if best_score > second_best:
        confidence = best_score / total
    else:
        confidence = 0.0

    # Clamp for safety (should already be in [0,1]).
    if confidence < 0.0:
        confidence = 0.0
    if confidence > 1.0:
        confidence = 1.0

    result = (['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][best_tonic], best_mode, confidence)
    print(f"\nFINAL RESULT: {result}")
    return result

# Test with the failing case
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

print("Testing with A minor scale notes:")
result = debug_detect_key(notes)
print(f"\nReturned: {result}")
print(f"Expected: ('A', 'minor', >0)")
print(f"Match: {result[0] == 'A' and result[1] == 'minor'}")