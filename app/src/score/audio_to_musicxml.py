"""
Pipeline: audio file -> note detection -> quantization -> measure building -> MusicXML export.
Usage:
    PYTHONPATH=./app/src python -m app.src.score.audio_to_musicxml path/to/input.wav [output_base]
If output_base is omitted, uses "output".
Exports to <output_base>.musicxml and attempts to create <output_base>.pdf via MuseScore CLI.
"""

import sys
import os
from pathlib import Path

# Ensure the src directory is on the path when run as a module
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Imports from the project
from transcription.detect_notes import detect_notes
from transcription.quantize import quantize_notes
from score.measure_builder import build_measures
from score.score import Score
from score.musicxml_exporter import score_to_musicxml
import subprocess


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: python -m app.src.score.audio_to_musicxml <input_wav> [output_base]")
        print("  <input_wav>: Path to a WAV file (e.g., app/tests/melodies/melody_001/D_major/audio.wav)")
        print("  [output_base]: Base name for output files (default: 'output')")
        return 1

    wav_path = argv[0]
    output_base = argv[1] if len(argv) > 1 else "output"

    # Step 1: Detect notes from audio
    print(f"[1/4] Detecting notes from {wav_path} ...")
    try:
        detected = detect_notes(wav_path)
    except Exception as e:
        print(f"Error during note detection: {e}")
        return 1
    print(f"   Detected {len(detected)} notes.")

    # Step 2: Quantize notes (estimates BPM, adds beat-aligned fields)
    print("[2/4] Quantizing notes ...")
    quantized = quantize_notes(detected)  # BPM estimated internally
    print(f"   Quantized {len(quantized)} notes.")

    # Step 3: Build measures (assumes 4/4 time signature)
    print("[3/4] Building measures (4/4) ...")
    measures = build_measures(quantized)
    print(f"   Built {len(measures)} measures.")

    # Step 4: Create Score and add measures
    print("[4/4] Assembling Score and exporting MusicXML ...")
    score = Score(title=f"Transcription of {Path(wav_path).name}", composer="Musiclution")
    for m in measures:
        score.add_measure(m)

    # Export to MusicXML string
    musicxml_str = score_to_musicxml(score)

    # Write MusicXML file
    xml_path = Path(f"{output_base}.musicxml")
    xml_path.write_text(musicxml_str, encoding="utf-8")
    print(f"   Exported MusicXML to {xml_path.absolute()}")

    # Attempt to convert to PDF using MuseScore CLI
    mscore_cmd = "mscore"
    try:
        subprocess.run([mscore_cmd, "--version"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        alternative_commands = ["MuseScore3", "MuseScore4", "mscore3", "mscore4"]
        found = False
        for cmd in alternative_commands:
            try:
                subprocess.run([cmd, "--version"],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               check=True)
                mscore_cmd = cmd
                found = True
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        if not found:
            print("   MuseScore CLI not found. Install MuseScore to convert MusicXML to PDF.")
            print(f"   Only MusicXML exported: {xml_path.absolute()}")
            return 0

    pdf_path = Path(f"{output_base}.pdf")
    try:
        subprocess.run(
            [mscore_cmd, str(xml_path), "-o", str(pdf_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"   Exported PDF to {pdf_path.absolute()}")
    except subprocess.CalledProcessError as e:
        print(f"   Error converting to PDF: {e}")
        print(f"   MuseScore stdout: {e.stdout}")
        print(f"   MuseScore stderr: {e.stderr}")
        print(f"   MusicXML file is available at: {xml_path.absolute()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())