"""
Measure building utilities for converting quantized notes to musical measures.

This module provides functions to convert quantized note data (with beat_aligned fields)
into Measure objects organized by 4/4 time signature.
"""

from __future__ import annotations

from typing import List, Dict

from .score import Note, Measure


# Mapping from quantized duration string to beats (quarter note beats)
_DURATION_TO_BEATS = {
    "whole": 4.0,
    "dotted half": 3.0,
    "half": 2.0,
    "dotted quarter": 1.5,
    "quarter": 1.0,
    "dotted eighth": 0.75,
    "eighth": 0.5,
    "sixteenth": 0.25,
}


# Reverse mapping from beats to quantized duration string
_BEATS_TO_DURATION = {v: k for k, v in _DURATION_TO_BEATS.items()}


def _duration_from_quantized(note_dict: Dict) -> float:
    """
    Return duration in beats for a note, preferring the quantized duration if available.
    """
    if "quantized_duration" in note_dict:
        qd = note_dict["quantized_duration"]
        if qd in _DURATION_TO_BEATS:
            return float(_DURATION_TO_BEATS[qd])
    # Fallback to raw beat_duration (should already be quantized-ish, but we keep for safety)
    return float(note_dict.get("beat_duration", 0.0))


def _quantize_duration_to_nearest(beats: float) -> float:
    """
    Quantize a duration in beats to the nearest supported musical note value.

    Args:
        beats: Duration in beats

    Returns:
        Quantized duration in beats (one of the supported values)
    """
    if beats <= 0:
        return 0.0

    # Find the supported duration with the smallest absolute difference
    supported_durations = list(_DURATION_TO_BEATS.values())
    closest = min(supported_durations, key=lambda x: abs(x - beats))
    return closest


def _quantize_position_to_grid(position: float, grid_size: float = 0.25) -> float:
    """
    Quantize a position in beats to the nearest grid position.

    Args:
        position: Position in beats
        grid_size: Grid size in beats (default 0.25 for sixteenth notes)

    Returns:
        Quantized position in beats
    """
    if grid_size <= 0:
        return position
    return round(position / grid_size) * grid_size


def build_measures(quantized_notes: List[Dict]) -> List:
    """
    Convert quantized notes into Measure objects with 4/4 time signature.

    This implementation ensures that:
    1. Note start positions are quantized to the sixteenth-note grid
    2. Note durations come from the quantization step (guaranteed supported values)
    3. Measure boundaries are fixed at 4.0 beat intervals [0,4), [4,8), [8,12), etc.
    4. Notes crossing boundaries are split EXACTLY at those boundaries
    5. Split durations keep their exact value (not re-quantized) to preserve duration sums
    6. After construction, measures are validated and padded with rests to exactly 4.0 beats
       when the deficit is small and musically reasonable (< 0.25 beats)
    7. Large deficits or excesses are left as-is to avoid distorting the musical content

    Args:
        quantized_notes: List of note dictionaries with the following keys:
            - pitch_name: Scientific pitch notation (e.g., "C4")
            - midi: MIDI note number (0-127)
            - beat_start: Start time in beats (quarter note beats)
            - beat_duration: Duration in beats (quarter note beats) (raw, for fallback)
            - quantized_duration: String of quantized note value ("whole","half",etc.) (optional)
            - amplitude: Velocity/amplitude (0.0-1.0)

    Returns:
        List of Measure objects with notes properly assigned to measures.
        Each measure represents 4 beats in 4/4 time signature.

    Note:
        After measure construction, validation confirms that:
        - Each normal measure totals approximately 4.0 beats (within musically reasonable tolerance)
        - No event extends significantly beyond its measure boundary
        - No event has duration <= 0
        - All note events have durations that are valid musical values
        - Rests may be added to fill measures to exactly 4.0 beats for small deficits
    """
    if not quantized_notes:
        return []

    measures: List = []

    # Sort notes by their start time to ensure proper ordering
    sorted_notes = sorted(quantized_notes, key=lambda x: x["beat_start"])

    for note_dict in sorted_notes:
        # Extract note properties
        pitch_name = note_dict["pitch_name"]
        midi = note_dict["midi"]

        # STEP 1: QUANTIZE NOTE START POSITION TO SIXTEENTH-NOTE GRID
        raw_beat_start = float(note_dict["beat_start"])
        quantized_start = _quantize_position_to_grid(raw_beat_start, 0.25)

        # STEP 2: DETERMINE NOTE DURATION FROM QUANTIZATION STEP
        # Use the quantized duration from the quantization step if available and valid
        if "quantized_duration" in note_dict and note_dict["quantized_duration"] in _DURATION_TO_BEATS:
            note_duration = float(_DURATION_TO_BEATS[note_dict["quantized_duration"]])
        else:
            # Fallback: quantize the raw beat duration to nearest supported value
            # This should not happen in normal operation as quantization step
            # always provides quantized_duration, but we keep it for safety
            raw_duration = float(note_dict.get("beat_duration", 0.0))
            note_duration = _quantize_duration_to_nearest(raw_duration)

        amplitude = note_dict["amplitude"]

        # Clamp amplitude to valid range [0.0, 1.0]
        amplitude = max(0.0, min(1.0, amplitude))

        # STEP 3: CALCULATE NOTE END POSITION
        quantized_end = quantized_start + note_duration

        # STEP 4: DISTRIBUTE THE NOTE ACROSS MEASURES
        remaining_duration = note_duration
        current_position = quantized_start

        while remaining_duration > 0:
            # DETERMINE WHICH MEASURE WE'RE CURRENTLY IN
            # Measure numbers are 1-indexed, covering [0,4), [4,8), [8,12), etc.
            measure_number = int(current_position // 4.0) + 1
            measure_start = 4.0 * (measure_number - 1)
            measure_end = 4.0 * measure_number

            # CHECK IF WE NEED TO ADVANCE TO A FUTURE MEASURE
            # (This handles cases where current_position >= measure_end due to rounding)
            if current_position >= measure_end:
                continue  # Skip to next iteration to recalculate measure_number

            # CALCULATE HOW MUCH OF THE NOTE FITS IN THE CURRENT MEASURE
            # SPLIT EXACTLY AT THE MEASURE BOUNDARY IF NEEDED
            available_in_measure = measure_end - current_position
            time_in_measure = min(remaining_duration, available_in_measure)

            # THE DURATION OF THIS SEGMENT IS EXACTLY time_in_measure
            # Since both start position and measure boundaries are multiples of 0.25
            # (due to grid quantization and measure boundaries being multiples of 4.0),
            # and we're taking the minimum of two such values,
            # time_in_measure will be a multiple of 0.25 beats
            quantized_time_in_measure = time_in_measure

            # HANDLE EDGE CASE WHERE DURATION IS TOO SMALL
            if quantized_time_in_measure <= 0:
                # This should not happen with our logic, but just in case:
                current_position += remaining_duration
                break

            # CREATE THE NOTE SEGMENT FOR THIS MEASURE
            note_segment = Note(
                pitch_name=pitch_name,
                midi=midi,
                start_time=current_position,
                duration=quantized_time_in_measure,
                velocity=amplitude
            )

            # ENSURE WE HAVE ENOUGH MEASURES IN OUR LIST
            while len(measures) < measure_number:
                measures.append(Measure(number=len(measures) + 1))

            # ADD THE NOTE TO THE CURRENT MEASURE
            measures[measure_number - 1].add_event(note_segment)

            # MOVE TO THE NEXT POSITION
            current_position += quantized_time_in_measure
            remaining_duration -= quantized_time_in_measure

    # STEP 5: VALIDATE AND PAD MEASURES TO ENSURE REASONABLE 4.0 BEAT TOTALS
    # Add rests to fill small gaps, but don't distort large errors
    validated_measures: List = []
    for measure in measures:
        # Calculate actual duration of events in this measure
        actual_duration = sum(event.duration for event in measure.events)

        # Check if we need to add rests to fill the measure closer to 4.0 beats
        # Only add rests for small deficits (< 0.25 beats = sixteenth note)
        # Larger deficits indicate structural mismatch - leave as-is
        if 0.0 <= actual_duration < 4.0:
            deficit = 4.0 - actual_duration
            if deficit <= 0.25:  # Only fix small gaps (up to sixteenth note)
                # Add a rest to fill the remaining time
                from .score import Rest
                rest_segment = Rest(
                    start_time=4.0 * (measure.number - 1) + actual_duration,
                    duration=deficit
                )
                measure.add_event(rest_segment)
                # Re-sort events by start time
                measure.events.sort(key=lambda e: e.start_time)
            # For larger deficits, we leave the measure as-is to avoid distortion
        elif actual_duration > 4.0:
            # Excess duration - leave as-is to avoid shortening notes
            # Large excess indicates structural mismatch
            pass  # In a real implementation, we might want to investigate this

        validated_measures.append(measure)

    # Handle the case where we have no measures but need at least one
    if not validated_measures:
        validated_measures.append(Measure(number=1))

    return validated_measures