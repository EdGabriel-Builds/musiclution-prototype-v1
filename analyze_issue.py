#!/usr/bin/env python3

def analyze_problem():
    """
    Analyze exactly why the overlong-offset heuristic is triggering incorrectly
    """
    print("=== PROBLEM ANALYSIS ===")
    print()

    # The failing case
    c4_start, c4_end = 0.0, 2.0
    g4_start, g4_end = 1.5, 2.5

    c4_duration = c4_end - c4_start  # 2.0
    g4_duration = g4_end - g4_start  # 1.0

    overlap_start = max(c4_start, g4_start)  # 1.5
    overlap_end = min(c4_end, g4_end)        # 2.0
    overlap_duration = overlap_end - overlap_start  # 0.5

    print("Notes:")
    print(f"  C4: {c4_start}-{c4_end} (duration={c4_duration})")
    print(f"  G4: {g4_start}-{g4_end} (duration={g4_duration})")
    print(f"  Overlap: {overlap_start}-{overlap_end} (duration={overlap_duration})")
    print()

    # What the algorithm thinks:
    print("Algorithm's reasoning for 'G4 looks like overlong offset of C4':")
    overlap_ratio_next = overlap_duration / g4_duration  # 0.5/1.0 = 0.5
    amp_check = 0.8 > 0.1  # C4 amplitude check
    duration_check = g4_duration >= c4_duration * 0.5  # 1.0 >= 2.0 * 0.5 = 1.0

    print(f"  overlap_ratio_next = {overlap_duration}/{g4_duration} = {overlap_ratio_next}")
    print(f"  overlap_ratio_next > 0.3: {overlap_ratio_next > 0.3}")
    print(f"  current_amplitude > 0.1: {amp_check}")
    print(f"  next_duration >= current_duration * 0.5: {g4_duration} >= {c4_duration} * 0.5 → {g4_duration} >= {c4_duration * 0.5} → {duration_check}")
    print(f"  ALL TRUE → TRUNCATE G4")
    print()

    # But is this interpretation correct?
    print("What does 'G4 looks like overlong offset of C4' actually mean?")
    print("It means: G4 started early (at 1.5) and is running too long (until 2.5)")
    print("But wait - G4's ACTUAL duration is 1.0 (from 1.5 to 2.5)")
    print("If G4 started at the CORRECT time (when C4 ends at 2.0), it should end at 3.0")
    print("But G4 actually ends at 2.5, which is EARLIER than 3.0")
    print()
    print("So G4 is NOT running long - it's actually SHORTER than expected!")
    print("If anything, C4 is the one running long (overlapping into G4's territory)")
    print()

    # Let's think about what the condition should check
    print("What SHOULD the overlong-offset check detect?")
    print("Case 1: Current note is overlong (should truncate current)")
    print("  - Current note overlaps significantly into next note's territory")
    print("  - Next note has reasonable amplitude (is a real note)")
    print("  - Current note is significantly longer than next note")
    print()
    print("Case 2: Next note is overlong (should truncate next)")
    print("  - Next note overlaps significantly into current note's territory")
    print("  - Current note has reasonable amplitude (is a real note)")
    print("  - Next note is significantly longer than current note")
    print()

    print("In our case:")
    print(f"  Overlap ratio of current: {overlap_duration}/{c4_duration} = {overlap_duration/c4_duration:.3f}")
    print(f"  Overlap ratio of next: {overlap_duration}/{g4_duration} = {overlap_duration/g4_duration:.3f}")
    print()
    print("Current note overlap ratio: 0.25 (25% of C4 overlaps with G4)")
    print("Next note overlap ratio: 0.5 (50% of G4 overlaps with C4)")
    print()
    print("Neither is > 0.3 for current, but next is 0.5 > 0.3")
    print("But the DURATION CHECK is wrong!")
    print()
    print("For 'next note is overlong', we should check if next note is LONGER than current")
    print("But we're checking: next_duration >= current_duration * 0.5")
    print("This is TRUE whenever next note is at least HALF the duration of current")
    print("Which is almost always true for overlapping notes!")
    print()
    print("The correct check should be: next_duration > current_duration * SOME_FACTOR")
    print("Where SOME_FACTOR > 1.0 to indicate next is significantly LONGER")
    print()
    print("Actually, let's re-read the comment:")
    print('"But don\\t truncate next if it\\t much shorter than current note (unlikely to be overlong)"')
    print()
    print("So the intention is: don't trigger if next is MUCH SHORTER than current")
    print("Which means: DO trigger if next is NOT much shorter than current")
    print("I.e., if next_duration >= current_duration * 0.5 (not much shorter)")
    print()
    print("But this is backwards! If next is not much shorter, it could be:")
    print("- About the same length (ratio ~1.0)")
    print("- Longer (ratio > 1.0)")
    print("- Or just a bit shorter (ratio 0.5-1.0)")
    print()
    print("What we ACTUALLY want to check for 'next is overlong':")
    print("- Is next SIGNIFICANTLY longer than current?")
    print("- I.e., next_duration > current_duration * 1.5 or 2.0?")
    print()
    print("Let's check what the existing tests expect...")

if __name__ == "__main__":
    analyze_problem()