"""
Musiclution v0.1 — Milestone 0: "Audio in, notes out."

Scope (intentionally minimal):
  WAV file -> basic-pitch -> list of detected notes -> printed table.

NOT in scope for this milestone:
  - No quantization
  - No key signature handling
  - No MusicXML export
  - No notation / rendering
  - No app structure

The single public function `detect_notes(wav_path)` returns a clean list of
note dicts. This is the seam the later quantization stage will plug into, but
it does nothing beyond note detection today.

Usage:
    python src/transcription/detect_notes.py path/to/audio.wav
    python src/transcription/detect_notes.py path/to/audio.wav --gt path/to/source.mid
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import pretty_midi
from basic_pitch import ICASSP_2022_MODEL_PATH
from basic_pitch.inference import predict


def midi_to_name(midi_number: int) -> str:
    """Convert a MIDI note number to scientific pitch name, e.g. 62 -> 'D4'."""
    return pretty_midi.note_number_to_name(int(midi_number))


def detect_notes(wav_path: str | Path) -> list[dict]:
    """
    Run basic-pitch on a mono/stereo WAV and return detected notes.

    Returns a list of dicts sorted by start time, each:
        {
          "pitch_name": str,   # e.g. "D4"
          "midi": int,         # e.g. 62
          "start": float,      # seconds
          "end": float,        # seconds
          "duration": float,   # seconds
          "amplitude": float,  # 0..1, basic-pitch's velocity proxy (NOT a confidence score)
        }

    Note: basic-pitch does not emit a separate confidence value. `amplitude`
    is the note-event salience/velocity proxy and is labeled honestly as such.
    """
    wav_path = Path(wav_path)
    if not wav_path.exists():
        raise FileNotFoundError(f"Audio file not found: {wav_path}")

    # predict() returns (model_output, midi_data, note_events).
    # note_events is a list of tuples:
    #   (start_time, end_time, pitch_midi, amplitude, pitch_bend)
    _model_output, _midi_data, note_events = predict(
        str(wav_path),
        ICASSP_2022_MODEL_PATH,
    )

    notes: list[dict] = []
    for ev in note_events:
        start, end, pitch_midi, amplitude = ev[0], ev[1], ev[2], ev[3]
        notes.append(
            {
                "pitch_name": midi_to_name(pitch_midi),
                "midi": int(pitch_midi),
                "start": float(start),
                "end": float(end),
                "duration": float(end) - float(start),
                "amplitude": float(amplitude),
            }
        )

    notes.sort(key=lambda n: (n["start"], n["midi"]))
    return notes


def load_ground_truth(mid_path: str | Path) -> list[dict]:
    """Parse a ground-truth MIDI file into the same note-dict shape (no amplitude focus)."""
    mid_path = Path(mid_path)
    pm = pretty_midi.PrettyMIDI(str(mid_path))
    notes: list[dict] = []
    for inst in pm.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            notes.append(
                {
                    "pitch_name": midi_to_name(n.pitch),
                    "midi": int(n.pitch),
                    "start": float(n.start),
                    "end": float(n.end),
                    "duration": float(n.end - n.start),
                    "amplitude": float(n.velocity) / 127.0,
                }
            )
    notes.sort(key=lambda n: (n["start"], n["midi"]))
    return notes


def print_notes(notes: list[dict], title: str = "DETECTED NOTES") -> None:
    print(f"\n{title}  ({len(notes)} notes)")
    print(f"{'#':>3}  {'Pitch':<6} {'MIDI':>4}  {'Start(s)':>8}  {'End(s)':>7}  {'Dur(s)':>7}  {'Amp':>5}")
    print("-" * 52)
    for i, n in enumerate(notes, 1):
        print(
            f"{i:>3}  {n['pitch_name']:<6} {n['midi']:>4}  "
            f"{n['start']:>8.3f}  {n['end']:>7.3f}  {n['duration']:>7.3f}  {n['amplitude']:>5.2f}"
        )


def compare_pitch_sequences(pred: list[dict], truth: list[dict]) -> None:
    """
    Rough Milestone-0 objective check: compare the ORDERED pitch sequences.
    This is a sanity signal, not a real metric (that lives in evaluation/metrics.py later).
    """
    pred_seq = [n["pitch_name"] for n in pred]
    truth_seq = [n["pitch_name"] for n in truth]
    matches = sum(1 for a, b in zip(pred_seq, truth_seq) if a == b)
    n = max(len(pred_seq), len(truth_seq))
    print("\nPITCH SEQUENCE COMPARISON (ordered, positional)")
    print(f"  ground truth : {' '.join(truth_seq)}")
    print(f"  predicted    : {' '.join(pred_seq)}")
    print(f"  positional match: {matches}/{n}"
          f"   (count truth={len(truth_seq)}, pred={len(pred_seq)})")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Milestone 0: audio in, notes out.")
    parser.add_argument("wav", help="Path to the input WAV file")
    parser.add_argument("--gt", help="Optional ground-truth .mid for a side-by-side pitch check")
    args = parser.parse_args(argv)

    notes = detect_notes(args.wav)
    print_notes(notes, title=f"PREDICTED (basic-pitch)  <- {Path(args.wav).name}")

    if args.gt:
        truth = load_ground_truth(args.gt)
        print_notes(truth, title=f"GROUND TRUTH (source.mid)  <- {Path(args.gt).name}")
        compare_pitch_sequences(notes, truth)

    return 0


if __name__ == "__main__":
    sys.exit(main())
