#!/usr/bin/env python3

# Test the scoring logic directly
def test_scoring_logic():
    # Simulate what happens with our A minor test case
    # We expect: C major = 7, A minor = 7, everything else < 7

    best_score = -1
    second_best = -1
    best_tonic = 0
    best_mode = 'major'

    # Process C major (tonic=0, mode=major, score=7)
    score = 7
    if score > best_score:
        second_best = best_score
        best_score = score
        best_tonic = 0
        best_mode = 'major'
        print(f"After C major: best={best_score}, second={second_best}")
    elif score == best_score:
        second_best = best_score  # This is what SHOULD happen for ties
        print(f"After C major (tie): best={best_score}, second={second_best}")
    elif score > second_best:
        second_best = score
        print(f"After C major (new second): best={best_score}, second={second_best}")

    # Process A minor (tonic=9, mode=minor, score=7)
    score = 7
    if score > best_score:
        second_best = best_score
        best_score = score
        best_tonic = 9
        best_mode = 'minor'
        print(f"After A minor: best={best_score}, second={second_best}")
    elif score == best_score:
        second_best = best_score  # This is what SHOULD happen for ties
        print(f"After A minor (tie): best={best_score}, second={second_best}")
    elif score > second_best:
        second_best = score
        print(f"After A minor (new second): best={best_score}, second={second_best}")

if __name__ == "__main__":
    test_scoring_logic()