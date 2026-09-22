#!/usr/bin/env python3

def cleanup_monophonic_trace_detailed(notes):
    """
    Trace version with focus on the exact conditions
    """
    if not notes:
        return []

    cleaned = [note.copy() for note in notes]
    cleaned.sort(key=lambda n: n["start"])

    i = 0
    just_removed_embedded = False
    iteration = 0

    while i < len(cleaned) - 1:
        iteration += 1
        current = cleaned[i]
        next_note = cleaned[i + 1]

        # Calculate actual overlap
        overlap_start = max(current["start"], next_note["start"])
        overlap_end = min(current["end"], next_note["end"])
        overlap_duration = max(0.0, overlap_end - overlap_start)

        if overlap_duration > 0:
            current_duration = current["duration"]
            next_duration = next_note["duration"]
            current_amplitude = current["amplitude"]
            next_amplitude = next_note["amplitude"]

            print(f"\n=== Iteration {iteration} ===")
            print(f"Current: {current['pitch_name']} [{current['start']:.1f}-{current['end']:.1f}] dur={current_duration:.1f} amp={current_amplitude:.1f}")
            print(f"Next:    {next_note['pitch_name']} [{next_note['start']:.1f}-{next_note['end']:.1f}] dur={next_duration:.1f} amp={next_amplitude:.1f}")
            print(f"Overlap: {overlap_duration:.1f} ({overlap_start:.1f}-{overlap_end:.1f})")

            # Embedded artifact check
            cond1 = next_duration <= 0.15
            cond2 = next_amplitude < 0.4
            cond3 = overlap_duration > next_duration * 0.8
            print(f"Embedded artifact check:")
            print(f"  next_duration <= 0.15: {next_duration:.1f} <= 0.15 → {cond1}")
            print(f"  next_amplitude < 0.4: {next_amplitude:.1f} < 0.4 → {cond2}")
            print(f"  overlap_duration > next_duration * 0.8: {overlap_duration:.1f} > {next_duration * 0.8:.1f} → {cond3}")
            print(f"  ALL: {cond1 and cond2 and cond3}")

            if cond1 and cond2 and cond3:
                print("→ REMOVING EMBEDDED ARTIFACT (next note)")
                cleaned.pop(i + 1)
                just_removed_embedded = True
                continue

            # Current overlong offset check
            overlap_ratio_current = overlap_duration / current_duration if current_duration > 0 else 0
            cond_a = overlap_ratio_current > 0.3
            cond_b = next_amplitude > 0.1
            cond_c = current_duration >= next_duration * 0.5
            print(f"Current overlong offset check:")
            print(f"  overlap_ratio_current > 0.3: {overlap_ratio_current:.3f} > 0.3 → {cond_a}")
            print(f"  next_amplitude > 0.1: {next_amplitude:.1f} > 0.1 → {cond_b}")
            print(f"  current_duration >= next_duration * 0.5: {current_duration:.1f} >= {next_duration * 0.5:.1f} → {cond_c}")
            print(f"  ALL: {cond_a and cond_b and cond_c}")

            if cond_a and cond_b and cond_c:
                print("→ TRUNCATING CURRENT (overlong offset)")
                current["end"] = next_note["start"]
                current["duration"] = current["end"] - current["start"]
                just_removed_embedded = False
                i += 1
                continue

            # Next overlong offset check
            overlap_ratio_next = overlap_duration / next_duration if next_duration > 0 else 0
            cond_x = overlap_ratio_next > 0.3
            cond_y = current_amplitude > 0.1
            cond_z = next_duration >= current_duration * 0.5
            print(f"Next overlong offset check:")
            print(f"  overlap_ratio_next > 0.3: {overlap_ratio_next:.3f} > 0.3 → {cond_x}")
            print(f"  current_amplitude > 0.1: {current_amplitude:.1f} > 0.1 → {cond_y}")
            print(f"  next_duration >= current_duration * 0.5: {next_duration:.1f} >= {current_duration * 0.5:.1f} → {cond_z}")
            print(f"  ALL: {cond_x and cond_y and cond_z}")

            if cond_x and cond_y and cond_z:
                print("→ TRUNCATING NEXT (overlong offset)")
                next_note["end"] = current["end"]
                next_note["duration"] = next_note["end"] - next_note["start"]
                just_removed_embedded = False
                # Don't increment i
                continue

            # Default case
            print("→ DEFAULT: truncating current to respect next onset")
            current["end"] = next_note["start"]
            current["duration"] = current["end"] - current["start"]
            just_removed_embedded = False
            i += 1
        else:
            just_removed_embedded = False
            i += 1

        if iteration > 10:
            break

    cleaned = [note for note in cleaned if note["duration"] > 0.001]
    return cleaned

# Test case
test_notes = [
    {"pitch_name": "C4", "midi": 60, "start": 0.0, "end": 2.0, "duration": 2.0, "amplitude": 0.8},
    {"pitch_name": "G4", "midi": 67, "start": 1.5, "end": 2.5, "duration": 1.0, "amplitude": 0.7}
]

print("Input:")
for i, n in enumerate(test_notes):
    print(f"  {n['pitch_name']}: {n['start']}-{n['end']} (dur={n['duration']}, amp={n['amplitude']})")

result = cleanup_monophonic_trace_detailed(test_notes)

print("\nOutput:")
for i, n in enumerate(result):
    print(f"  {n['pitch_name']}: {n['start']}-{n['end']} (dur={n['duration']}, amp={n['amplitude']})")

print("\nExpected:")
print("  C4: 0.0-1.5")
print("  G4: 1.5-2.5")