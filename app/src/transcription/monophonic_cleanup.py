"""
Monophonic cleanup stage for Basic Pitch output.

This module provides functions to clean up overlapping note events from
monophonic audio recordings, addressing Basic Pitch's tendency to produce
overlong offsets and spurious detections due to reverb/artifacts.
"""

from __future__ import annotations

from typing import List, Dict, Tuple


def cleanup_monophonic(notes: List[Dict], max_voices: int = 1) -> List[Dict]:
    """
    Clean up overlapping note events for monophonic audio.

    For v0.1, enforces a single active melodic voice by truncating previous
    notes when a new note begins before the previous note ends, when the
    overlap is likely an artifact/overlong offset.

    Parameters
    ----------
    notes : list[dict]
        List of note dictionaries as returned by detect_notes.
        Each dict must contain at least the keys:
        "pitch_name", "midi", "start", "end", "duration", "amplitude".
    max_voices : int, optional
        Maximum number of simultaneous voices allowed. Defaults to 1 for
        monophonic cleanup. Kept for future polyphonic expansion.

    Returns
    -------
    list[dict]
        Cleaned list of note dictionaries with overlaps resolved.
        Original input list is not modified.

    Notes
    -----
    - The function does not modify the input ``notes`` list.
    - Preserves pitch, onset, amplitude/velocity information.
    - Only truncates note ends, never shifts onsets or creates new notes.
    - Does not modify note durations to be exactly equal to next onset.
    - Preserves legitimate silence between notes.
    - Handles short embedded artifacts and legitimate short notes.
    """
    if max_voices <= 0:
        raise ValueError("max_voices must be positive")

    # For v0.1, we enforce strict monophonic (max_voices = 1)
    if not notes:
        return []

    # Work on a shallow copy to avoid modifying input
    cleaned = [note.copy() for note in notes]
    cleaned.sort(key=lambda n: n["start"])

    i = 0
    just_removed_embedded = False  # Track if we just removed an embedded artifact

    while i < len(cleaned) - 1:
        current = cleaned[i]
        next_note = cleaned[i + 1]

        # Calculate actual overlap
        overlap_start = max(current["start"], next_note["start"])
        overlap_end = min(current["end"], next_note["end"])
        overlap_duration = max(0.0, overlap_end - overlap_start)

        # Check for adjacent same-pitch notes that should be merged (no overlap or tiny gap)
        # This addresses cases where basic-pitch incorrectly splits a single note into two
        # adjacent same-pitch notes due to signal fluctuations
        # Check this FIRST so it handles both overlapping and adjacent cases
        if current["pitch_name"] == next_note["pitch_name"]:
            # Calculate gap or overlap
            gap = next_note["start"] - current["end"]  # positive = gap, negative = overlap
            # Check if they should be merged: either tiny overlap or tiny gap
            if abs(gap) <= 0.01:  # 10ms maximum gap/overlap for merging
                # Merge the two notes into one
                merged_note = current.copy()
                merged_note["end"] = next_note["end"]
                merged_note["duration"] = merged_note["end"] - merged_note["start"]
                # Use the maximum amplitude of the two notes
                merged_note["amplitude"] = max(current["amplitude"], next_note["amplitude"])

                # Replace current note with merged note and remove next note
                cleaned[i] = merged_note
                cleaned.pop(i + 1)
                just_removed_embedded = False
                # Don't increment i, check merged note against new next
                continue

        if overlap_duration > 0:
            # Overlap detected - need to resolve

            # Calculate overlap duration
            current_duration = current["duration"]
            next_duration = next_note["duration"]
            current_amplitude = current["amplitude"]
            next_amplitude = next_note["amplitude"]

            # Skip cleanup for tiny overlaps (likely timing jitter)
            if overlap_duration < 0.05:  # 50ms threshold
                just_removed_embedded = False
                i += 1
                continue

            # Check if this looks like an embedded artifact (very short note inside longer one)
            # If next note is very short (< 0.15s) and low amplitude (< 0.4) and overlap is most of its duration,
            # it's likely an artifact inside the current note
            if next_duration <= 0.15 and next_amplitude < 0.4 and overlap_duration > next_duration * 0.8:
                # Remove the embedded artifact (next_note)
                cleaned.pop(i + 1)
                just_removed_embedded = True
                # Don't increment i, check current against new next
                continue

            # If we just removed an embedded artifact, we fall through to standard overlap resolution
            # This ensures we handle any resulting overlap appropriately
            if just_removed_embedded:
                just_removed_embedded = False
                # Fall through to overlap resolution logic below

            # Check if current note looks like an overlong offset
            # If overlap is significant portion of current note AND
            # next note has reasonable amplitude, truncate current
            overlap_ratio_current = overlap_duration / current_duration if current_duration > 0 else 0

            # But don't truncate current if it's much shorter than next note (unlikely to be overlong)
            if overlap_ratio_current > 0.3 and next_amplitude > 0.1 and current_duration >= next_duration * 0.5:
                # Truncate current note at next_note's onset
                current["end"] = next_note["start"]
                current["duration"] = current["end"] - current["start"]
                just_removed_embedded = False
                i += 1
                continue

            # Default case: truncate the earlier note (current) to respect the onset of the later note (next)
            # This handles the case where we have a clear note onset followed by overlong offset
            current["end"] = next_note["start"]
            current["duration"] = current["end"] - current["start"]
            just_removed_embedded = False
            i += 1
        else:
            # No overlap, move to next pair
            just_removed_embedded = False
            i += 1

    # Remove any zero-length notes that might have been created
    cleaned = [note for note in cleaned if note["duration"] > 0.001]  # 1ms minimum

    # For v0.1, check if the final note looks like an overlong offset
    # If there are at least 2 notes, compare the final note to the previous one
    # This addresses cases where basic-pitch produces overlong final notes due to reverb/decay artifacts
    if len(cleaned) >= 2:
        final_note = cleaned[-1]
        prev_note = cleaned[-2]

        # Only apply if notes have the same pitch (common case for final repeated tone)
        if final_note["pitch_name"] == prev_note["pitch_name"]:
            # Calculate how much longer the final note is compared to previous
            duration_ratio = final_note["duration"] / prev_note["duration"] if prev_note["duration"] > 0 else 0

            # If final note is significantly longer (>50% longer) and has comparable amplitude,
            # it may be an overlong offset due to reverb/artifact
            # Use amplitude threshold to avoid truncating legitimate long final notes
            if duration_ratio > 1.5 and final_note["amplitude"] > 0.3:
                # Truncate final note to match previous note's duration
                # This preserves the onset and shortens the offset to match typical note length
                final_note["end"] = final_note["start"] + prev_note["duration"]
                final_note["duration"] = prev_note["duration"]
                # Preserve the maximum amplitude of the two notes
                final_note["amplitude"] = max(final_note["amplitude"], prev_note["amplitude"])

    return cleaned


def detect_overlaps(notes: List[Dict]) -> List[Tuple[int, int, float]]:
    """
    Detect overlapping note events in a list of notes.

    Parameters
    ----------
    notes : list[dict]
        List of note dictionaries sorted by start time.

    Returns
    -------
    list[tuple]
        List of tuples (index1, index2, overlap_duration) for each overlapping pair.
        index1 < index2 and notes[index1] starts before notes[index2].
    """
    overlaps = []
    sorted_notes = sorted(notes, key=lambda n: n["start"])

    for i in range(len(sorted_notes) - 1):
        current = sorted_notes[i]
        for j in range(i + 1, len(sorted_notes)):
            next_note = sorted_notes[j]
            if next_note["start"] >= current["end"]:
                # Since sorted by start time, no further notes will overlap with current
                break
            overlap_start = max(current["start"], next_note["start"])
            overlap_end = min(current["end"], next_note["end"])
            overlap = max(0.0, overlap_end - overlap_start)
            if overlap > 0:
                overlaps.append((i, j, overlap))

    return overlaps


if __name__ == "__main__":
    # Simple test
    test_notes = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 1.0, "duration": 1.0, "amplitude": 0.8},
        {"pitch_name": "D4", "midi": 62, "start": 0.5, "end": 1.5, "duration": 1.0, "amplitude": 0.9},
        {"pitch_name": "E4", "midi": 64, "start": 2.0, "end": 2.5, "duration": 0.5, "amplitude": 0.7},
    ]

    print("Original notes:")
    for i, n in enumerate(test_notes):
        print(f"  {i}: {n['pitch_name']} {n['start']:.3f}-{n['end']:.3f}")

    overlaps = detect_overlaps(test_notes)
    print(f"\nDetected overlaps: {overlaps}")

    cleaned = cleanup_monophonic(test_notes)
    print("\nAfter cleanup:")
    for i, n in enumerate(cleaned):
        print(f"  {i}: {n['pitch_name']} {n['start']:.3f}-{n['end']:.3f}")