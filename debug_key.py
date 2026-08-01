#!/usr/bin/env python3

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from music.key_detection import detect_key
from score.score import Note

# Test the exact case from our failing test
notes = [
    Note("A4", 69, 0.0, 1.0),
    Note("B4", 71, 1.0, 1.0),
    Note("C4", 60, 2.0, 1.0),  # Note: C4 is midi 60
    Note("D4", 62, 3.0, 1.0),
    Note("E4", 64, 4.0, 1.0),
    Note("F4", 65, 5.0, 1.0),
    Note("G4", 67, 6.0, 1.0),
]

print("Notes and their pitch classes:")
for i, n in enumerate(notes):
    pc = n.midi % 12
    print(f"  {n.name} (MIDI {n.midi}) -> PC {pc}")

key_name, mode, confidence = detect_key(notes)

print(f"\nResult: {key_name} {mode} (confidence: {confidence})")

# Let's also manually compute what we expect
print("\nManual computation:")
pc_count = [0] * 12
for n in notes:
    pc = n.midi % 12
    pc_count[pc] += 1
    print(f"  {n.name} (MIDI {n.midi}) -> PC {pc}")

print(f"PC counts: {pc_count}")

# Compute scores for each tonic
MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

def scale_mask(tonic, intervals):
    mask = [False] * 12
    for i in intervals:
        pc = (tonic + i) % 12
        if 0 <= pc < 12:
            mask[pc] = True
    return mask

print("\nScores for each tonic:")
best_score = -1
second_best = -1
best_tonic = 0
best_mode = 'major'

for tonic in range(12):
    major_mask = scale_mask(tonic, MAJOR_INTERVALS)
    major_score = sum(pc_count[i] for i in range(12) if major_mask[i])

    minor_mask = scale_mask(tonic, MINOR_INTERVALS)
    minor_score = sum(pc_count[i] for i in range(12) if minor_mask[i])

    print(f"  Tonic {tonic} ({'C' if tonic==0 else 'C#' if tonic==1 else 'D' if tonic==2 else 'D#' if tonic==3 else 'E' if tonic==4 else 'F' if tonic==5 else 'F#' if tonic==6 else 'G' if tonic==7 else 'G#' if tonic==8 else 'A' if tonic==9 else 'A#' if tonic==10 else 'B'}):")
    print(f"    Major: {major_score} (notes: {[i for i in range(12) if major_mask[i]]})")
    print(f"    Minor: {minor_score} (notes: {[i for i in range(12) if minor_mask[i]]})")

    # Update best and second best
    if major_score > best_score:
        second_best = best_score
        best_score = major_score
        best_tonic = tonic
        best_mode = 'major'
    elif major_score == best_score:
        second_best = best_score
    elif major_score > second_best:
        second_best = major_score

    if minor_score > best_score:
        second_best = best_score
        best_score = minor_score
        best_tonic = tonic
        best_mode = 'minor'
    elif minor_score == best_score:
        pass  # Don't update second_best on tie for best
    elif minor_score > second_best:
        second_best = minor_score

print(f"\nBest: {best_score} (tonic {best_tonic}, mode {best_mode})")
print(f"Second best: {second_best}")
print(f"Tie? {best_score == second_best}")