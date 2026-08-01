"""

Estimates musical key using a scale membership scoring algorithm.

For each possible major/minor key, pitch classes are compared against
the scale pattern. The highest-scoring key is selected.


This implementation does not use machine learning and is intended to be
easily replaceable with a learned model in the future.
"""

from __future__ import annotations

from typing import Iterable, Tuple, List
from score.score import Note

# Pitch class names using sharps
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Intervals (in semitones) for major and natural minor scales
MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]


def _scale_mask(tonic: int, intervals: List[int]) -> List[bool]:
    """Return a boolean list of length 12 indicating which pitch classes are in the scale."""
    mask = [False] * 12
    for i in intervals:
        pc = (tonic + i) % 12
        if 0 <= pc < 12:  # Safety check
            mask[pc] = True
    return mask


def detect_key(notes: Iterable[Note]) -> Tuple[str, str, float]:
    """
    Estimate the key of a collection of notes.

    Parameters
    ----------
    notes : iterable of Note
        The notes to analyze. Rests are ignored (should not be passed).

    Returns
    -------
    tuple (key_name, mode, confidence)
        key_name: e.g., 'C', 'C#', etc.
        mode: either 'major' or 'minor'
        confidence: a float between 0.0 and 1.0 indicating how confident we are
                    in the detection. This is the proportion of notes explained by
                    the winning scale (best_score / total), but 0.0 if there is a
                    tie for the highest score *before* tie-breaking (indicating
                    ambiguity between multiple keys).
    """
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

    if total == 0:
        # No notes: default to C major with zero confidence
        return ('C', 'major', 0.0)

    best_score = -1          # highest score seen
    second_best = -1         # second highest score seen
    best_tonic = 0           # tonic of the best key
    best_mode = 'major'      # mode of the best key ('major' or 'minor')

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
        elif major_score == best_score:
            second_best = best_score
            pass
        elif major_score > second_best:
            second_best = major_score

        # Minor scale
        minor_mask = _scale_mask(tonic, MINOR_INTERVALS)
        minor_score = sum(pc_count[i] for i in range(12) if minor_mask[i])
        # Update best and second best
        if minor_score > best_score:
            second_best = best_score
            best_score = minor_score
            best_tonic = tonic
            best_mode = 'minor'
        elif minor_score == best_score:
            # Tie for best score - update second_best but don't change best_tonic/best_mode
            second_best = best_score
        elif minor_score > second_best:
            second_best = minor_score

    # If there's a tie for best score, resolve it using the first note's pitch class.
    # We need to check if there are multiple keys achieving the best score.
    if best_score == second_best:
        # There's a tie for first place. Find all keys with score == best_score.
        candidates = []
        for tonic in range(12):
            major_score = sum(pc_count[i] for i in range(12) if _scale_mask(tonic, MAJOR_INTERVALS)[i])
            minor_score = sum(pc_count[i] for i in range(12) if _scale_mask(tonic, MINOR_INTERVALS)[i])
            if major_score == best_score:
                candidates.append((tonic, 'major'))
            if minor_score == best_score:
                candidates.append((tonic, 'minor'))

        # If we have candidates, choose the one whose tonic matches first_pc
        if first_pc is not None:
            chosen = None
            for tonic, mode in candidates:
                if tonic == first_pc:
                    chosen = (tonic, mode)
                    break
            if chosen is not None:
                best_tonic, best_mode = chosen
            elif candidates:
                # Fallback to first candidate
                best_tonic, best_mode = candidates[0]
        elif candidates:
            # No first_pc (shouldn't happen if we have notes) but fallback anyway
            best_tonic, best_mode = candidates[0]

    # Determine if there was a tie for the highest score
    if best_score == second_best:
        # Ambiguous: multiple keys share the highest score
        confidence = 0.0
    else:
        confidence = best_score / total

    # Clamp for safety (should already be in [0,1]).
    if confidence < 0.0:
        confidence = 0.0
    if confidence > 1.0:
        confidence = 1.0

    return (NOTE_NAMES[best_tonic], best_mode, confidence)


def detect_key_from_score(score) -> Tuple[str, str, float]:
    """
    Convenience function to detect key from a Score object.

    Parameters
    ----------
    score : Score
        A musiclution Score object.

    Returns
    -------
    tuple (key_name, mode, confidence)
    """
    # Extract all notes from the score (ignoring rests)
    notes = []
    for measure in score.measures:
        for event in measure.events:
            if isinstance(event, Note):
                notes.append(event)
    return detect_key(notes)