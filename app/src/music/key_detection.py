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

# Pitch class names using sharps (standard music theory)
NOTE_NAMES_SHARPS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
# Pitch class names using flats (for display preference in flat keys)
NOTE_NAMES_FLATS = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Intervals (in semitones) for major and natural minor scales
MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

# Key signature fifths mapping for preferred spelling (positive = sharps, negative = flats)
# Maps tonic (0=C, 1=C#/Db, etc.) to fifths value using preferred enharmonic spelling
TONIC_TO_FIFTHS_PREFERRED = {
    0: 0,   # C
    1: -5,  # Db (prefer 5 flats over 7 sharps)
    2: 2,   # D
    3: -3,  # Eb (prefer 3 flats over 4 sharps)
    4: 4,   # E
    5: -1,  # F
    6: -6,  # Gb (prefer 6 flats over 6 sharps when equal)
    7: 1,   # G
    8: -4,  # Ab
    9: 3,   # A
    10: -2, # Bb
    11: 5   # B
}


def _scale_mask(tonic: int, intervals: List[int]) -> List[bool]:
    """Return a boolean list of length 12 indicating which pitch classes are in the scale."""
    mask = [False] * 12
    for i in intervals:
        pc = (tonic + i) % 12
        if 0 <= pc < 12:  # Safety check
            mask[pc] = True
    return mask


def detect_key(notes: Iterable[Note]) -> Tuple[str, str, float, int]:
    """
    Estimate the key of a collection of notes.

    Parameters
    ----------
    notes : iterable of Note
        The notes to analyze. Rests are ignored (should not be passed).

    Returns
    -------
    tuple (key_name, mode, confidence, fifths)
        key_name: e.g., 'C', 'C#', 'Db', etc. (prefers flats for flat keys)
        mode: either 'major' or 'minor'
        confidence: a float between 0.0 and 1.0 indicating how confident we are
                    in the detection. This is the proportion of notes explained by
                    the winning scale (best_score / total), but 0.0 if there is a
                    tie for the highest score *before* tie-breaking (indicating
                    ambiguity between multiple keys).
        fifths: number of sharps (+) or flats (-) in the key signature
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

    # Calculate the correct fifths value based on tonic and mode
    # For major keys, fifths is based directly on the tonic
    # For minor keys, fifths is based on the relative major (up 3 semitones)
    if best_mode == "major":
        fifths = TONIC_TO_FIFTHS_PREFERRED[best_tonic]
    else:  # minor
        # Relative major is up 3 semitones (minor third) from minor tonic
        relative_major_tonic = (best_tonic + 3) % 12
        fifths = TONIC_TO_FIFTHS_PREFERRED[relative_major_tonic]

    # Convert tonic to appropriate key name spelling
    # Prefer flats for flat keys (negative fifths), sharps for sharp keys (positive fifths)
    # C (0 fifths) can go either way, we'll use sharp scripting by convention (C major)
    key_name_sharps = NOTE_NAMES_SHARPS[best_tonic]
    key_name_flats = NOTE_NAMES_FLATS[best_tonic]

    if fifths < 0:
        # Flat key: prefer flat spelling
        key_name = key_name_flats
    elif fifths > 0:
        # Sharp key: prefer sharp spelling
        key_name = key_name_sharps
    else:
        # C major/A minor: use sharp scripting by convention (C major)
        key_name = key_name_sharps

    return (key_name, best_mode, confidence, fifths)


def detect_key_from_score(score) -> Tuple[str, str, float, int]:
    """
    Convenience function to detect key from a Score object.

    Parameters
    ----------
    score : Score
        A musiclution Score object.

    Returns
    -------
    tuple (key_name, mode, confidence, fifths)
    """
    # Extract all notes from the score (ignoring rests)
    notes = []
    for measure in score.measures:
        for event in measure.events:
            if isinstance(event, Note):
                notes.append(event)
    return detect_key(notes)


def get_fifths_from_key_name_mode(key_name: str, mode: str) -> int:
    """
    Convert a key name and mode to fifths value using the same logic as detect_key.

    Parameters
    ----------
    key_name : str
        Key name (e.g., 'C', 'C#', 'Db', etc.)
    mode : str
        Either 'major' or 'minor'

    Returns
    -------
    int
        Number of sharps (+) or flats (-) in the key signature
    """
    # Find tonic index from key name
    try:
        tonic = NOTE_NAMES_SHARPS.index(key_name)
    except ValueError:
        try:
            tonic = NOTE_NAMES_FLATS.index(key_name)
        except ValueError:
            raise ValueError(f"Invalid key name: {key_name}")

    # Calculate fifths based on mode
    if mode == "major":
        return TONIC_TO_FIFTHS_PREFERRED[tonic]
    else:  # minor
        # Relative major is up 3 semitones (minor third) from minor tonic
        relative_major_tonic = (tonic + 3) % 12
        return TONIC_TO_FIFTHS_PREFERRED[relative_major_tonic]


def apply_key_aware_spelling(quantized_notes: List[Dict], fifths: int) -> List[Dict]:
    """
    Apply key-aware enharmonic spelling to quantized notes.

    Preserves all fields except pitch_name, which is respelled according to
    the key signature's preferred enharmonic spelling.

    Parameters
    ----------
    quantized_notes : List[Dict]
        List of note dictionaries as returned by quantize_notes.
        Each dict must contain at least the keys:
        "pitch_name", "midi", "beat_start", "beat_duration", "quantized_duration", "amplitude".
    fifths : int
        Key signature fifths (positive=sharps, negative=flats).

    Returns
    -------
    List[Dict]
        New list of note dictionaries with respelled pitch_name.
        All other fields are preserved exactly.
        Input dictionaries are not mutated.
    """
    # Choose spelling preference based on key signature
    if fifths < 0:
        note_names = NOTE_NAMES_FLATS   # Flat keys: prefer flats
    elif fifths > 0:
        note_names = NOTE_NAMES_SHARPS  # Sharp keys: prefer sharps
    else:
        note_names = NOTE_NAMES_SHARPS  # C major: sharp spelling by convention

    result = []
    for note_dict in quantized_notes:
        # Create shallow copy to avoid mutating input
        new_note = note_dict.copy()

        # Respell the pitch name using key-appropriate table
        midi_number = new_note["midi"]
        note_index = midi_number % 12
        octave = (midi_number // 12) - 1
        new_note["pitch_name"] = f"{note_names[note_index]}{octave}"

        result.append(new_note)

    return result