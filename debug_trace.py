#!/usr/bin/env python3

def cleanup_monophonic_trace(notes):
    """
    Trace version of cleanup_monophonic with detailed logging
    """
    if not notes:
        return []

    # Work on a shallow copy to avoid modifying input
    cleaned = [note.copy() for note in notes]
    cleaned.sort(key=lambda n: n["start"])

    print("Initial cleaned notes:")
    for i, note in enumerate(cleaned):
        print(f"  {i}: {note['pitch_name']} start={note['start']:.3f}, end={note['end']:.3f}, duration={note['duration']:.3f}, amplitude={note['amplitude']:.3f}")
    print()

    i = 0
    just_removed_embedded = False  # Track if we just removed an embedded artifact
    iteration = 0

    while i < len(cleaned) - 1:
        iteration += 1
        print(f"\n=== Iteration {iteration}, i={i} ===")
        current = cleaned[i]
        next_note = cleaned[i + 1]

        print(f"Current note ({i}): {current['pitch_name']} start={current['start']:.3f}, end={current['end']:.3f}, duration={current['duration']:.3f}, amplitude={current['amplitude']:.3f}")
        print(f"Next note ({i+1}): {next_note['pitch_name']} start={next_note['start']:.3f}, end={next_note['end']:.3f}, duration={next_note['duration']:.3f}, amplitude={next_note['amplitude']:.3f}")

        # Calculate actual overlap
        overlap_start = max(current["start"], next_note["start"])
        overlap_end = min(current["end"], next_note["end"])
        overlap_duration = max(0.0, overlap_end - overlap_start)

        print(f"Overlap: start={overlap_start:.3f}, end={overlap_end:.3f}, duration={overlap_duration:.3f}")

        if overlap_duration > 0:
            print("Overlap detected - need to resolve")

            # Calculate overlap duration
            current_duration = current["duration"]
            next_duration = next_note["duration"]
            current_amplitude = current["amplitude"]
            next_amplitude = next_note["amplitude"]

            print(f"Current duration: {current_duration:.3f}")
            print(f"Next duration: {next_duration:.3f}")
            print(f"Current amplitude: {current_amplitude:.3f}")
            print(f"Next amplitude: {next_amplitude:.3f}")

            # Skip cleanup for tiny overlaps (likely timing jitter)
            if overlap_duration < 0.05:  # 50ms threshold
                print("Overlap < 0.05s, skipping (timing jitter)")
                just_removed_embedded = False
                i += 1
                continue

            # Check if this looks like an embedded artifact (very short note inside longer one)
            # If next note is very short (< 0.15s) and low amplitude (< 0.4) and overlap is most of its duration,
            # it's likely an artifact inside the current note
            print(f"Checking embedded artifact condition:")
            print(f"  next_duration <= 0.15: {next_duration <= 0.15} ({next_duration:.3f} <= 0.15)")
            print(f"  next_amplitude < 0.4: {next_amplitude < 0.4} ({next_amplitude:.3f} < 0.4)")
            print(f"  overlap_duration > next_duration * 0.8: {overlap_duration > next_duration * 0.8} ({overlap_duration:.3f} > {next_duration * 0.8:.3f})")

            if next_duration <= 0.15 and next_amplitude < 0.4 and overlap_duration > next_duration * 0.8:
                print("EMBEDDED ARTIFACT DETECTED - removing next note")
                # Remove the embedded artifact (next_note)
                cleaned.pop(i + 1)
                just_removed_embedded = True
                print(f"After removal, just_removed_embedded = {just_removed_embedded}")
                # Don't increment i, check current against new next
                continue

            # If we just removed an embedded artifact, we fall through to standard overlap resolution
            # This ensures we handle any resulting overlap appropriately
            if just_removed_embedded:
                print("Just removed embedded artifact, falling through to standard overlap resolution")
                just_removed_embedded = False
                # Fall through to overlap resolution logic below

            # Check if current note looks like an overlong offset
            # If overlap is significant portion of current note AND
            # next note has reasonable amplitude, truncate current
            overlap_ratio_current = overlap_duration / current_duration if current_duration > 0 else 0
            print(f"Overlong offset check (current):")
            print(f"  overlap_ratio_current = {overlap_duration:.3f} / {current_duration:.3f} = {overlap_ratio_current:.3f}")
            print(f"  overlap_ratio_current > 0.3: {overlap_ratio_current > 0.3}")
            print(f"  next_amplitude > 0.1: {next_amplitude > 0.1} ({next_amplitude:.3f} > 0.1)")
            print(f"  current_duration >= next_duration * 0.5: {current_duration >= next_duration * 0.5} ({current_duration:.3f} >= {next_duration * 0.5:.3f})")

            # But don't truncate current if it's much shorter than next note (unlikely to be overlong)
            if overlap_ratio_current > 0.3 and next_amplitude > 0.1 and current_duration >= next_duration * 0.5:
                print("CURRENT NOTE LOOKS LIKE OVERLONG OFFSET - truncating current")
                # Truncate current note at next_note's onset
                old_end = current["end"]
                current["end"] = next_note["start"]
                current["duration"] = current["end"] - current["start"]
                print(f"  Truncated current from end={old_end:.3f} to {current['end']:.3f}")
                print(f"  New duration: {current['duration']:.3f}")
                just_removed_embedded = False
                i += 1
                continue

            # Check if next note looks like an overlong offset of current
            # (reverse case: next note started early and runs long)
            overlap_ratio_next = overlap_duration / next_duration if next_duration > 0 else 0
            print(f"Overlong offset check (next):")
            print(f"  overlap_ratio_next = {overlap_duration:.3f} / {next_duration:.3f} = {overlap_ratio_next:.3f}")
            print(f"  overlap_ratio_next > 0.3: {overlap_ratio_next > 0.3}")
            print(f"  current_amplitude > 0.1: {current_amplitude > 0.1} ({current_amplitude:.3f} > 0.1)")
            print(f"  next_duration >= current_duration * 0.5: {next_duration >= current_duration * 0.5} ({next_duration:.3f} >= {current_duration * 0.5:.3f})")

            # But don't truncate next if it's much shorter than current note (unlikely to be overlong)
            if overlap_ratio_next > 0.3 and current_amplitude > 0.1 and next_duration >= current_duration * 0.5:
                print("NEXT NOTE LOOKS LIKE OVERLONG OFFSET - truncating next")
                # Truncate next_note at current_note's end
                old_end = next_note["end"]
                next_note["end"] = current["end"]
                next_note["duration"] = next_note["end"] - next_note["start"]
                print(f"  Truncated next from end={old_end:.3f} to {next_note['end']:.3f}")
                print(f"  New duration: {next_note['duration']:.3f}")
                just_removed_embedded = False
                # Don't increment i here - we need to check this same pair again
                # in case the truncation created a new overlap with the previous note
                continue

            # Default case: truncate the earlier note (current) to respect the onset of the later note (next)
            # This handles the case where we have a clear note onset followed by overlong offset
            print("DEFAULT CASE - truncating current note to respect next note's onset")
            old_end = current["end"]
            current["end"] = next_note["start"]
            current["duration"] = current["end"] - current["start"]
            print(f"  Truncated current from end={old_end:.3f} to {current['end']:.3f}")
            print(f"  New duration: {current['duration']:.3f}")
            just_removed_embedded = False
            i += 1
        else:
            print("No overlap, moving to next pair")
            just_removed_embedded = False
            i += 1

        # Safety break to prevent infinite loops
        if iteration > 20:
            print("Breaking after 20 iterations to prevent infinite loop")
            break

    # Remove any zero-length notes that might have been created
    initial_count = len(cleaned)
    cleaned = [note for note in cleaned if note["duration"] > 0.001]  # 1ms minimum
    if len(cleaned) < initial_count:
        print(f"Removed {initial_count - len(cleaned)} zero-length notes")

    print("\nFinal cleaned notes:")
    for i, note in enumerate(cleaned):
        print(f"  {i}: {note['pitch_name']} start={note['start']:.3f}, end={note['end']:.3f}, duration={note['duration']:.3f}, amplitude={note['amplitude']:.3f}")

    return cleaned

# Test the embedded-artifact case
test_notes = [
    {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 2.0, "duration": 2.0, "amplitude": 0.8},
    {"pitch_name": "G4", "midi": 67, "start": 1.5, "end": 2.5, "duration": 1.0, "amplitude": 0.7}
]

print("=== Testing Embedded-Artifact Case ===")
print("Input notes:")
for i, note in enumerate(test_notes):
    print(f"  {i}: {note['pitch_name']} start={note['start']:.3f}, end={note['end']:.3f}, duration={note['duration']:.3f}, amplitude={note['amplitude']:.3f}")
print()

result = cleanup_monophonic_trace(test_notes)

print("\n=== Expected Result ===")
print("C4 → 0.0-1.5")
print("G4 → 1.5-2.5 unchanged")
print()
print("=== Actual Result ===")
for i, note in enumerate(result):
    print(f"{note['pitch_name']} → {note['start']:.1f}-{note['end']:.1f}")