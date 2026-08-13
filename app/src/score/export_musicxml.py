"""
Command-line script to export a Score to MusicXML and PDF.
Exports to output.musicxml and attempts to convert to output.pdf using MuseScore CLI.
If MuseScore is not available, only exports MusicXML and prints a helpful message.
"""

import sys
import subprocess
import os
from pathlib import Path

# Add the src directory to the path so we can import the score module
# We do this only when the script is run directly (not when imported as a module)
if __name__ == "__main__" and __package__ is None:
    # We need to add the directory that contains the 'src' package to sys.path
    # From script location: .../app/src/score/export_musicxml.py
    # Go up two levels to get to .../app (which contains src)
    path_to_add = os.path.join(os.path.dirname(__file__), '..', '..')
    sys.path.insert(0, path_to_add)

# Now we can import from the score package
from src.score.musicxml_exporter import score_to_musicxml
from src.score.score import Score, Measure, Note, Rest


def create_sample_score() -> Score:
    """Create a sample score for demonstration."""
    score = Score(title="Sample Score", composer="Demo Composer", tempo_bpm=120.0)

    # Measure 1: 4/4, quarter note C4, quarter rest, half note D4
    m1 = Measure(number=1, time_signature_top=4, time_signature_bottom=4)
    m1.add_event(Note(pitch_name="C4", midi=60, start_time=0.0, duration=1.0, velocity=0.8))
    m1.add_event(Rest(start_time=1.0, duration=1.0))
    m1.add_event(Note(pitch_name="D4", midi=62, start_time=2.0, duration=2.0, velocity=0.6))
    score.add_measure(m1)

    # Measure 2: 3/4, half note E4, quarter note G4
    m2 = Measure(number=2, time_signature_top=3, time_signature_bottom=4)
    m2.add_event(Note(pitch_name="E4", midi=64, start_time=0.0, duration=2.0, velocity=0.7))
    m2.add_event(Note(pitch_name="G4", midi=67, start_time=2.0, duration=1.0, velocity=0.7))
    score.add_measure(m2)

    return score


def main():
    # Create or get a score (for now, we use a sample)
    score = create_sample_score()

    # Export to MusicXML
    musicxml_str = score_to_musicxml(score)

    # Write MusicXML file
    output_xml = Path("output.musicxml")
    output_xml.write_text(musicxml_str, encoding="utf-8")
    print(f"Exported MusicXML to {output_xml.absolute()}")

    # Try to convert to PDF using MuseScore CLI
    mscore_cmd = "mscore"  # common command name for MuseScore CLI
    # Check if mscore is available
    try:
        # Try to run mscore with --version to see if it's installed
        subprocess.run([mscore_cmd, "--version"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Try alternative command names
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
            print("MuseScore CLI not found. Install MuseScore to convert MusicXML to PDF.")
            print(f"Only MusicXML exported: {output_xml.absolute()}")
            return

    # If we get here, MuseScore CLI is available
    output_pdf = Path("output.pdf")
    try:
        # Run: mscore output.musicxml -o output.pdf
        result = subprocess.run(
            [mscore_cmd, str(output_xml), "-o", str(output_pdf)],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Exported PDF to {output_pdf.absolute()}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting to PDF: {e}")
        print(f"MuseScore stdout: {e.stdout}")
        print(f"MuseScore stderr: {e.stderr}")
        print(f"MusicXML file is available at: {output_xml.absolute()}")


if __name__ == "__main__":
    main()