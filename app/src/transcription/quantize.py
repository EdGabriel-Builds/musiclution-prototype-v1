"""
Milestone 1: Quantization stub.

Provides a placeholder function for note quantization that preserves all
existing note fields and adds placeholders for beat-aligned fields.
"""

from __future__ import annotations

from typing import List, Dict


def quantize_notes(
    notes: List[Dict],
    bpm: float | None = None,
) -> List[Dict]:
    """
    Quantize note onsets and durations to a musical grid (stub implementation).

    This function returns a new list of note dictionaries with the same fields
    as the input, plus three additional fields for beat-aligned timing:
        - beat_start: start time in beats (placeholder: copied from 'start')
        - beat_duration: duration in beats (placeholder: copied from 'duration')
        - quantized_duration: quantized duration in beats (placeholder: "unknown")

    The actual quantization logic will be implemented in a later milestone.
    For now, the function preserves the input and adds placeholder values.

    Parameters
    ----------
    notes : list[dict]
        List of note dictionaries as returned by :func:`detect_notes`.
        Each dict must contain at least the keys:
        "pitch_name", "midi", "start", "end", "duration", "amplitude".
    bpm : float | None, optional
        Beats per minute for quantization grid. Not used in this stub.

    Returns
    -------
    list[dict]
        New list of note dictionaries with added fields:
        "beat_start", "beat_duration", "quantized_duration".
        The original input list is not modified.

    Notes
    -----
    - The function does not modify the input ``notes`` list.
    - All original fields are preserved exactly as-is.
    - The three new fields are added to each note dictionary.
    """
    _ = bpm  # Mark as intentionally unused for now
    quantized: List[Dict] = []
    for note in notes:
        # Create a shallow copy of the note dictionary to avoid mutating input
        new_note = note.copy()
        # Add placeholder quantization fields
        new_note["beat_start"] = new_note["start"]
        new_note["beat_duration"] = new_note["duration"]
        new_note["quantized_duration"] = "unknown"
        quantized.append(new_note)
    return quantized