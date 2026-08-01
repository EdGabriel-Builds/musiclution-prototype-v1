"""
Measure building utilities for converting quantized notes to musical measures.

This module provides functions to convert quantized note data (with beat_aligned fields)
into Measure objects organized by 4/4 time signature.
"""

from __future__ import annotations

from typing import List, Dict

from score.score import Note, Measure


def build_measures(quantized_notes: List[Dict]) -> List:
    """
    Convert quantized notes into Measure objects with 4/4 time signature.

    Args:
        quantized_notes: List of note dictionaries with the following keys:
            - pitch_name: Scientific pitch notation (e.g., "C4")
            - midi: MIDI note number (0-127)
            - beat_start: Start time in beats (quarter note beats)
            - beat_duration: Duration in beats (quarter note beats)
            - amplitude: Velocity/amplitude (0.0-1.0)

    Returns:
        List of Measure objects with notes properly assigned to measures.
        Each measure represents 4 beats in 4/4 time signature.
    """
    if not quantized_notes:
        return []

    measures: List = []
    current_measure_number = 1
    current_measure_start = 0.0
    current_measure_end = 4.0  # 4/4 time = 4 beats per measure

    # Sort notes by their start time to ensure proper ordering
    sorted_notes = sorted(quantized_notes, key=lambda x: x["beat_start"])

    for note_dict in sorted_notes:
        # Extract note properties
        pitch_name = note_dict["pitch_name"]
        midi = note_dict["midi"]
        note_start = float(note_dict["beat_start"])
        note_duration = float(note_dict["beat_duration"])
        amplitude = note_dict["amplitude"]

        # Clamp amplitude to valid range [0.0, 1.0]
        amplitude = max(0.0, min(1.0, amplitude))

        # Calculate note end time
        note_end = note_start + note_duration

        # Process the note, potentially splitting it across multiple measures
        remaining_duration = note_duration
        current_position = note_start

        while remaining_duration > 0:
            # Check if we need to move to the next measure
            if current_position >= current_measure_end:
                # Move to next measure
                current_measure_number += 1
                current_measure_start = current_measure_end
                current_measure_end += 4.0

            # Calculate how much of the note fits in the current measure
            time_in_measure = min(remaining_duration, current_measure_end - current_position)

            # Create the note segment for this measure
            note_segment = Note(
                pitch_name=pitch_name,
                midi=midi,
                start_time=current_position,
                duration=time_in_measure,
                velocity=amplitude
            )

            # Add the note to the current measure (creating it if needed)
            while len(measures) < current_measure_number:
                measures.append(Measure(number=len(measures) + 1))

            measures[current_measure_number - 1].add_event(note_segment)

            # Move to the next position
            current_position += time_in_measure
            remaining_duration -= time_in_measure

    return measures