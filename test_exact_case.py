#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app/src'))

from transcription.monophonic_cleanup import cleanup_monophonic

def test_exact_embedded_artifact_case():
    """Test the exact failing case from the problem description."""
    notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 2.0, "duration": 2.0, "amplitude": 0.8},
        {"pitch_name": "G4", "midi": 67, "start": 1.5, "end": 2.5, "duration": 1.0, "amplitude": 0.7}
    ]

    print("Input:")
    for i, n in enumerate(notes):
        print(f"  {n['pitch_name']}: {n['start']}-{n['end']} (dur={n['duration']}, amp={n['amplitude']})")

    cleaned = cleanup_monophonic(notes)

    print("\nOutput:")
    for i, n in enumerate(cleaned):
        print(f"  {n['pitch_name']}: {n['start']}-{n['end']} (dur={n['duration']}, amp={n['amplitude']})")

    print("\nExpected:")
    print("  C4: 0.0-1.5")
    print("  G4: 1.5-2.5 (unchanged)")

    # Check if we got the expected result
    if len(cleaned) >= 2:
        c4_result = cleaned[0]
        g4_result = cleaned[1]

        c4_correct = (abs(c4_result["start"] - 0.0) < 0.001 and
                     abs(c4_result["end"] - 1.5) < 0.001)
        g4_correct = (abs(g4_result["start"] - 1.5) < 0.001 and
                     abs(g4_result["end"] - 2.5) < 0.001)

        print(f"\nC4 correct: {c4_correct} (got {c4_result['start']}-{c4_result['end']})")
        print(f"G4 correct: {g4_correct} (got {g4_result['start']}-{g4_result['end']})")

        if c4_correct and g4_correct:
            print("✓ PASS")
            return True
        else:
            print("✗ FAIL")
            return False
    else:
        print("✗ FAIL - wrong number of notes")
        return False

if __name__ == "__main__":
    test_exact_embedded_artifact_case()