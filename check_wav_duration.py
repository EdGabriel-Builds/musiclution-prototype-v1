#!/usr/bin/env python3
"""
Check WAV file duration and detect_notes output.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'src'))

from transcription.detect_notes import detect_notes
from pathlib import Path

def check_wav_and_detection(wav_path):
    print(f"Checking WAV file: {wav_path}")

    # Check if file exists
    if not Path(wav_path).exists():
        print(f"❌ File not found: {wav_path}")
        return

    # Get file size and basic info
    file_size = Path(wav_path).stat().st_size
    print(f"File size: {file_size} bytes")

    # Try to get duration using soundfile or similar
    duration = None
    try:
        import soundfile as sf
        with sf.SoundFile(wav_path) as f:
            duration = len(f) / f.samplerate
            print(f"Duration (soundfile): {duration:.3f} seconds")
            print(f"Sample rate: {f.samplerate} Hz")
            print(f"Channels: {f.channels}")
    except ImportError:
        print("soundfile not available, trying another method")
        try:
            import wave
            with wave.open(wav_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
                print(f"Duration (wave): {duration:.3f} seconds")
                print(f"Sample rate: {rate} Hz")
                print(f"Channels: {wf.getnchannels()}")
        except Exception as e:
            print(f"Could not determine duration: {e}")

    # Run detect_notes
    print(f"\nRunning detect_notes...")
    try:
        notes = detect_notes(wav_path)
        print(f"Detected {len(notes)} notes")

        if notes:
            print("\nAll detected notes:")
            for i, note in enumerate(notes):
                print(f"  [{i}] {note['pitch_name']} (MIDI {note['midi']}): "
                      f"{note['start']:.3f}-{note['end']:.3f}s "
                      f"(dur={note['duration']:.3f}s, amp={note['amplitude']:.3f})")

            # Find the last note
            last_note = notes[-1]
            print(f"\nLast note: {last_note['pitch_name']} (MIDI {last_note['midi']}): "
                  f"{last_note['start']:.3f}-{last_note['end']:.3f}s "
                  f"(dur={last_note['duration']:.3f}s, amp={last_note['amplitude']:.3f})")

            # Compare with audio duration if we have it
            if duration is not None:
                extension = last_note['end'] - duration
                print(f"\nAudio duration: {duration:.3f}s")
                print(f"Last note ends: {last_note['end']:.3f}s")
                print(f"Extension beyond audio: {extension:.3f}s")
                if extension > 0:
                    print(f"❌ Last note extends {extension:.3f}s beyond audio file!")
                else:
                    print(f"✅ Last note ends within audio file bounds.")

    except Exception as e:
        print(f"Error in detect_notes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    wav_path = "/Users/user/Desktop/musiclutionv0.1/app/tests/melodies/melody_001/D_major/audio.wav"
    check_wav_and_detection(wav_path)