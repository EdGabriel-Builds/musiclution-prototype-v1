"""
Milestone 2: Quantization with duration quantization.

Provides a function for note quantization that preserves all
existing note fields, adds beat-aligned fields, and quantizes
the duration to the nearest musical note value.
"""

from __future__ import annotations

from typing import List, Dict

import numpy as np


# Constants for BPM estimation
DEFAULT_BPM = 120.0
MIN_INTERVAL_THRESHOLD = 1e-3
BPM_CLAMP_MIN = 40.0
BPM_CLAMP_MAX = 200.0
SECONDS_TO_BEATS_FACTOR = 60.0  # Beats per minute constant


# Constants for duration quantization
DURATION_MAP = [
    (4.0, "whole"),
    (3.0, "dotted half"),
    (2.0, "half"),
    (1.5, "dotted quarter"),
    (1.0, "quarter"),
    (0.75, "dotted eighth"),
    (0.5, "eighth"),
    (0.25, "sixteenth"),
]


def estimate_bpm(notes: List[Dict]) -> float:
    """
    Estimate beats per minute (BPM) from a list of note events.

    This is a temporary, simple implementation:
    - Compute inter-onset intervals (IOIs) between sorted note start times.
    - Take the median IOI.
    - Assume each IOI corresponds to a quarter note.
    - BPM = 60 / median_ioi.
    - If insufficient notes to compute IOI, return a default of DEFAULT_BPM.

    Parameters
    ----------
    notes : list[dict]
        List of note dictionaries as returned by detect_notes.
        Each dict must contain a "start" key (float seconds).

    Returns
    -------
    float
        Estimated beats per minute.
    """
    if len(notes) < 2:
        # Not enough data to estimate tempo; return a moderate default.
        return DEFAULT_BPM

    # Extract start times and sort them.
    starts = sorted(note["start"] for note in notes)

    # Compute inter-onset intervals.
    ioi = np.diff(starts)

    # Filter out zero or near-zero intervals (e.g., simultaneous notes).
    ioi = ioi[ioi > MIN_INTERVAL_THRESHOLD]

    if len(ioi) == 0:
        return DEFAULT_BPM

    median_ioi = float(np.median(ioi))

    # Avoid division by zero or extremely small values.
    if median_ioi <= 0:
        return DEFAULT_BPM

    bpm = SECONDS_TO_BEATS_FACTOR / median_ioi

    # Clamp to a reasonable range to avoid absurd values.
    bpm = max(BPM_CLAMP_MIN, min(BPM_CLAMP_MAX, bpm))

    return bpm


def quantize_duration(beat_duration: float) -> str:
    """
    Quantize a duration in beats to the nearest musical note value.

    Supported note values (in beats):
        whole: 4.0
        dotted half: 3.0
        half: 2.0
        dotted quarter: 1.5
        quarter: 1.0
        dotted eighth: 0.75
        eighth: 0.5
        sixteenth: 0.25

    Parameters
    ----------
    beat_duration : float
        Duration in beats to be quantized.

    Returns
    -------
    str
        String representation of the quantized note value.
    """
    # Find the note value with the smallest absolute difference.
    closest = min(
        DURATION_MAP,
        key=lambda x: abs(x[0] - beat_duration),
    )

    return closest[1]


def quantize_notes(
    notes: List[Dict],
    bpm: float | None = None,
) -> List[Dict]:
    """
    Quantize note onsets and durations to a musical grid.

    This function returns a new list of note dictionaries with the same
    fields as the input, plus three additional fields for beat-aligned timing:

        - beat_start: start time in beats (computed using BPM)
        - beat_duration: duration in beats (computed using BPM)
        - quantized_duration: quantized duration as a string

    If ``bpm`` is provided, that value is used; otherwise, a BPM estimate
    is derived from the note onsets via estimate_bpm.

    The actual quantization logic is applied to the duration for now.
    The start time is converted to beats but not quantized.

    Parameters
    ----------
    notes : list[dict]
        List of note dictionaries as returned by detect_notes.

    bpm : float | None, optional
        Beats per minute. If None, a BPM estimate is computed.

    Returns
    -------
    list[dict]
        New list of note dictionaries with added:
        "beat_start", "beat_duration", and "quantized_duration".

    Notes
    -----
    - The input ``notes`` list is not modified.
    - All original fields are preserved.
    - ``quantized_duration`` represents the nearest supported note value.
    """
    # Use provided BPM or estimate one from the notes.
    if bpm is None:
        bpm = estimate_bpm(notes)

    # Convert seconds to beats: beats = seconds * (BPM / 60).
    beats_per_second = bpm / SECONDS_TO_BEATS_FACTOR
    quantized: List[Dict] = []

    for note in notes:
        # Create a shallow copy of the note dictionary to avoid mutating input.
        new_note = note.copy()

        # Convert start and duration to beats.
        raw_beat_start = float(note["start"]) * beats_per_second
        raw_beat_duration = float(note["duration"]) * beats_per_second

        new_note["beat_start"] = raw_beat_start
        new_note["beat_duration"] = raw_beat_duration

        # Quantize the duration to the nearest musical note value.
        new_note["quantized_duration"] = quantize_duration(raw_beat_duration)

        quantized.append(new_note)

    return quantized
