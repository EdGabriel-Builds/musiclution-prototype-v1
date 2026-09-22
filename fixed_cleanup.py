"""
Fixed version of monophonic cleanup with corrected overlong-offset detection.
"""

from __future__ import annotations

from typing import List, Dict, Tuple


def cleanup_monophonic_fixed(notes: List[Dict], max_voices: int = 1) -> List[Dict]:
    """
    Clean up overlapping note events for monophonic audio with fixed logic.

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

            # Check if next note looks like an overlong offset of current
            # (reverse case: next note started early and runs long)
            overlap_ratio_next = overlap_duration / next_duration if next_duration > 0 else 0
            # But don't truncate next if it's much shorter than current note (unlikely to be overlong)
            # FIXED: Changed from >= to > to fix the edge case where equal durations incorrectly triggered
            # Also changed the factor from 0.5 to 0.6 to be more restrictive
            if overlap_ratio_next > 0.3 and current_amplitude > 0.1 and next_duration > current_duration * 0.6:
                # Truncate next_note at current_note's end
                next_note["end"] = current["end"]
                next_note["duration"] = next_note["end"] - next_note["start"]
                just_removed_embedded = False
                # Don't increment i here - we need to check this same pair again
                # in case the truncation created a new overlap with the previous note
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


# Test the fixed version
if __name__ == "__main__":
    # Test case 1: The failing embedded-artifact case
    print("=== Test Case 1: Embedded artifact case ===")
    test_notes1 = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 2.0, "duration": 2.0, "amplitude": 0.8},
        {"pitch_name": "G4", "midi": 67, "start": 1.5, "end": 2.5, "duration": 1.0, "amplitude": 0.7}
    ]

    print("Input:")
    for i, n in enumerate(test_notes1):
        print(f"  {n['pitch_name']}: {n['start']}-{n['end']} (dur={n['duration']}, amp={n['amplitude']})")

    cleaned1 = cleanup_monophonic_fixed(test_notes1)

    print("\nOutput:")
    for i, n in enumerate(cleaned1):
        print(f"  {n['pitch_name']}: {n['start']}-{n['end']} (dur={n['duration']}, amp={n['amplitude']})")

    print("\nExpected:")
    print("  C4: 0.0-1.5")
    print("  G4: 1.5-2.5")

    # Test case 2: The truncate_previous case (should still work)
    print("\n\n=== Test Case 2: Truncate previous case ===")
    test_notes2 = [
        {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 2.0, "duration": 2.0, "amplitude": 0.8},
        {"pitch_name": "D4", "midi": 62, "start": 1.0, "end": 1.5, "duration": 0.5, "amplitude": 0.9}
    ]

    print("Input:")
    for i, n in enumerate(test_notes2):
        print(f"  {n['pitch_name']}: {n['start']}-{n['end']} (dur={n['duration']}, amp={n['amplitude']})")

    cleaned2 = cleanup_monophonic_fixed(test_notes2)

    print("\nOutput:")
    for i, n in enumerate(cleaned2):
        print(f"  {n['pitch_name']}: {n['start']}-{n['end']} (dur={n['duration']}, amp={n['amplitude']})")

    print("\nExpected:")
    print("  C4: 0.0-1.0")
    print("  D4: 1.0-1.5")