# Debug Log: MusicXML Exporter Development

## Overview
This log documents the development and debugging of the MusicXML exporter for the musiclutionv0.1 project. The goal is to convert audio files -> note detection -> quantization -> measure building -> MusicXML export.

## Current State (as of 2026-08-07)

### Working Components
1. **Note Detection**: Uses `basic_pitch` to detect notes from WAV files.
   - Function: `transcription.detect_notes.detect_notes(wav_path)`
   - Output: List of dicts with keys: pitch_name, midi, start (sec), end (sec), duration (sec), amplitude.

2. **Quantization**: Converts detected notes to beat-aligned timing and quantizes duration.
   - Function: `transcription.quantize.quantize_notes(notes, bpm=None)`
   - Adds fields: beat_start (beats), beat_duration (beats), quantized_duration (string: sixteenth, eighth, quarter, half, whole).

3. **Measure Building**: Groups quantized notes into measures (assuming 4/4 time signature).
   - Function: `score.measure_builder.build_measures(quantized_notes)`
   - Output: List of `score.score.Measure` objects.

4. **MusicXML Export**: Converts a `Score` object to MusicXML string.
   - Function: `score.musicxml_exporter.score_to_musicxml(score)`
   - Output: Valid MusicXML Partwise format (supports notes, rests, measures, time signatures, key signature).

5. **Export Script**: Command-line tool to run the pipeline and optionally convert to PDF via MuseScore CLI.
   - Script: `app/src/score/audio_to_musicxml.py`

### Issues Encountered

#### Issue 1: Unsupported Durations in MusicXML Export
- Error: `ValueError: Unsupported duration: 0.6215441894531324. Supported: [0.25, 0.5, 1.0, 2.0, 4.0]`
- Root Cause: The measure builder was splitting notes at measure boundaries, resulting in segment durations that were not in the supported set (even if the original note's duration was quantized to a supported value).
- Example: A note with quantized duration "quarter" (1.0 beats) starting at 3.250 beats and ending at 4.250 beats would be split into two segments: 0.750 beats (in measure 1) and 0.250 beats (in measure 2). While 0.250 is supported (sixteenth), 0.750 is not.

#### Issue 2: Quantization granularity
- Initial quantization only quantized duration to the nearest supported value, but did not quantize start times. This led to notes starting at arbitrary beat positions (e.g., 0.031 beats), causing splits that produced unsupported durations.

#### Issue 3: Measure boundary splits produce non-standard durations
- Even when both start time and duration are quantized to the sixteenth note grid (multiples of 0.25 beats), splitting a note at a measure boundary can yield segment durations that are not multiples of 0.25 if the note does not start at a measure boundary. However, if both start and duration are multiples of 0.25, the segment durations will also be multiples of 0.25. The problem was that we were using the quantized duration string (nearest supported duration) to determine the note's length, but the actual duration we used for splitting was the grid duration (which might be, e.g., 0.75 beats, three sixteenth notes). When split, we got 0.75 and 0.25 — 0.75 is not a supported duration because our supported set only includes 0.25, 0.5, 1.0, 2.0, 4.0 (i.e., 1, 2, 4, 8, 16 sixteenth notes). Three sixteenth notes is not a standard note value in modern notation without using ties or dots.

### Attempted Fixes

#### Fix 1: Quantize both start time and duration to sixteenth note grid
- Modified `transcription.quantize.quantize_notes` to:
  - Quantize start time to nearest sixteenth note (0.25 beats).
  - Quantize duration to nearest sixteenth note (in beats), then map to the nearest supported duration string (using `quantize_duration`).
  - Store `beat_duration` as the grid duration (multiple of 0.25) and `quantized_duration` as the corresponding string.
- Result: Start times and durations are multiples of 0.25, but when splitting notes at measure boundaries, the segment durations may still be multiples of 0.25 that are not in the supported set (e.g., 0.75 beats = three sixteenth notes).

#### Fix 2: Quantize duration to nearest supported duration (not just sixteenth grid)
- Modified `transcription.quantize.quantize_notes` to:
  - Quantize start time to nearest sixteenth note.
  - Quantize duration to nearest supported duration (using `quantize_duration`) and set `beat_duration` to the exact numeric value from the supported set (0.25, 0.5, 1.0, 2.0, 4.0).
- This ensures that each note's duration is exactly one of the supported values.
- However, when a note is split at a measure boundary, the resulting segments may not have durations that are in the supported set (e.g., a note of duration 1.0 beats starting at 3.5 beats would split into 0.5 and 0.5 — both supported; but if it starts at 3.25 and duration 1.0, it splits into 0.75 and 0.25 — 0.75 not supported).

#### Fix 3: Avoid splitting notes by adjusting note placement
- Alternative approach: In the measure builder, if a note does not fit entirely in the current measure, move the entire note to the next measure (preserving its duration). This prevents splitting but may cause notes to be delayed or measures to have gaps.
- This approach was not implemented because it alters timing significantly.

### Current Working Solution (as of latest attempt)
We are currently testing Fix 2 (quantize duration to nearest supported duration, start time to sixteenth grid) and have not yet resolved the splitting issue for all cases.

### Test Case: First Melody (D_major)
- Audio file: `app/tests/melodies/melody_001/D_major/audio.wav`
- Detected notes: ~19
- After quantization (Fix 2): Notes have start times at multiples of 0.25 beats and durations in {0.25, 0.5, 1.0, 2.0, 4.0}
- Measure building: We still observe splits that produce unsupported durations (e.g., 0.75) because of the interaction between start time and duration.

### Next Steps
1. **Accept that splitting may produce unsupported durations and further quantize the segment durations to the nearest supported value.** This would alter timing but ensure valid MusicXML.
2. **Change the measure building algorithm to use a different time signature or to allow notes to cross measure boundaries by using ties.** However, ties are currently out of scope.
3. **Restrict the quantization to only produce notes that start and end at measure boundaries** by quantizing the start time to the nearest measure start (multiple of 4 beats) and duration to a value that fits within the measure. This is too restrictive.

Given the goal is a "simplest valid MusicXML exporter", we may opt for option 1: after splitting, quantize each segment's duration to the nearest supported duration. This will keep the notes within measures and produce valid MusicXML, albeit with small timing offsets.

### Files Modified
- `app/src/score/measure_builder.py`: Updated to use quantized duration for note length.
- `app/src/score/musicxml_exporter.py`: Exporter unchanged (supports only standard durations).
- `app/src/transcription/quantize.py`: Updated to quantize both start time and duration.
- `app/src/score/audio_to_musicxml.py`: Pipeline script.
- `app/src/score/export_musicxml.py`: Simple export script (uses sample score).

### Commands to Run
```bash
# Set Python path to include src
PYTHONPATH=./app/src python -m app.src.score.audio_to_musicxml <path_to_wav> [output_base]
```
Example:
```bash
PYTHONPATH=./app/src python -m app.src.score.audio_to_musicxml app/tests/melodies/melody_001/D_major/audio.wav test
```
This will produce `test.musicxml` and attempt to produce `test.pdf` using MuseScore CLI.

### Current Blockers
- The measure builder still produces segments with durations not in the supported set for certain note placements.
- Need to implement post-split duration quantization or accept that some notes will be slightly misaligned.

### Future Improvements
- Support for key signature detection (already have key detection module).
- Support for time signature changes.
- Support for tuplets, multiple voices, lyrics, articulations (as per future milestones).
- Better integration with the existing score model (e.g., using the Score class directly in the pipeline).

## Conclusion
We have a working pipeline that detects notes, quantizes them, builds measures, and exports to MusicXML. The main remaining issue is ensuring that all note durations in the exported MusicXML are from the supported set (sixteenth, eighth, quarter, half, whole). We are close to a solution by quantizing both start time and duration appropriately, but need to handle measure boundary splits without producing unsupported durations.