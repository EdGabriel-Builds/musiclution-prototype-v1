"""
Milestone 0 smoke test.

Purpose: prove the detection pipeline RUNS and returns well-formed data on a
known WAV. This is NOT an accuracy metric (those live in evaluation/metrics.py
later). It guarantees shape + basic sanity so later milestones build on solid
ground.

There is ALSO one light-touch objective check: the ordered predicted pitch
sequence must match the ground-truth MIDI for at least 90% of the truth notes.
This catches gross regressions (wrong octave, silence, total garbage) without
pretending to be a full evaluation.

Run:
    pytest tests/test_detect_notes_smoke.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make src/transcription importable without installing the package.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src" / "transcription"))

from detect_notes import detect_notes, load_ground_truth  # noqa: E402

MELODIES = [
    "melody_001/D_major",
    "melody_002/Eb_major",
    "melody_003/E_major",
]

REQUIRED_KEYS = {"pitch_name", "midi", "start", "end", "duration", "amplitude"}


@pytest.fixture(scope="module", params=MELODIES)
def melody_dir(request):
    d = REPO_ROOT / "tests" / "melodies" / request.param
    if not (d / "audio.wav").exists():
        pytest.skip(f"missing audio for {request.param}")
    return d


def test_pipeline_runs_and_returns_notes(melody_dir):
    notes = detect_notes(melody_dir / "audio.wav")
    assert isinstance(notes, list)
    assert len(notes) > 0, "no notes detected at all"


def test_note_shape_is_wellformed(melody_dir):
    notes = detect_notes(melody_dir / "audio.wav")
    for n in notes:
        assert REQUIRED_KEYS.issubset(n.keys()), f"missing keys in {n}"
        assert 0 <= n["midi"] <= 127
        assert n["start"] >= 0
        assert n["end"] > n["start"], "note must have positive duration"
        assert 0.0 <= n["amplitude"] <= 1.0


def test_notes_sorted_by_start(melody_dir):
    notes = detect_notes(melody_dir / "audio.wav")
    starts = [n["start"] for n in notes]
    assert starts == sorted(starts), "notes not sorted by start time"


def test_pitch_sequence_matches_ground_truth(melody_dir):
    """Light objective check: >=90% positional pitch match against source.mid."""
    gt_path = melody_dir / "source.mid"
    if not gt_path.exists():
        pytest.skip("no ground-truth MIDI available")

    pred = [n["pitch_name"] for n in detect_notes(melody_dir / "audio.wav")]
    truth = [n["pitch_name"] for n in load_ground_truth(gt_path)]

    matches = sum(1 for a, b in zip(pred, truth) if a == b)
    ratio = matches / len(truth)
    assert ratio >= 0.90, (
        f"pitch match {matches}/{len(truth)} = {ratio:.0%} < 90%\n"
        f"  truth: {' '.join(truth)}\n"
        f"  pred : {' '.join(pred)}"
    )
