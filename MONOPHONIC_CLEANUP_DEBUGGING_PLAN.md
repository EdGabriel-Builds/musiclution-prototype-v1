# Monophonic Cleanup Debugging Plan

**Purpose**: Establish a single, authoritative debugging approach for `cleanup_monophonic()` that observes rather than duplicates the production implementation, preventing the kind of divergence that caused misleading debug traces.

## Authoritative Implementation

The **single source of truth** for the cleanup algorithm is:
```
/Users/user/Desktop/musiclutionv0.1/app/src/transcription/monophonic_cleanup.py
```

Specifically the function:
```python
def cleanup_monophonic(notes: List[Dict], max_voices: int = 1) -> List[Dict]
```

**Critical Note**: Files `debug_trace.py`, `debug_trace2.py`, and `debug_trace3.py` **previously contained duplicated/divergent cleanup logic** and **must not be treated as authoritative** for the production algorithm. They showed different behavior (including incorrect G4 truncation) because they reimplemented rather than observed the production code.

File `fixed_cleanup.py` is **stale experimental code** and should be archived/deleted.

---

## Consolidated Debug Harness: `debug_monophonic_cleanup.py`

Will replace `debug_trace.py`, `debug_trace2.py`, and `debug_trace3.py` with a single observation-only debugging tool.

### Strict Import-Only Approach
- Imports: `from transcription.monophonic_cleanup import cleanup_monophonic, detect_overlaps`
- **Zero** reimplementation of cleanup logic anywhere in the file
- **Zero** duplicated condition checks (no overlap ratio calculations, no embedded artifact detection, no branch condition evaluation)

### Observation-Only Diagnostics
All insights derived solely from comparing inputs to outputs of the **actual** production function.

1. **Input/Output Summary**
   - Tabular display: pitch, start, end, duration, amplitude (before/after)

2. **Change Analysis**
   - Removed notes: Identified by comparing input vs output pitch/start time sets
   - Modified notes: Show old→new end/duration for notes with changed boundaries
   - Preserved notes: List of notes identical in input and output

3. **Overlap Verification**
   - Pre-call: `detect_overlaps(input_notes)` count and details
   - Post-call: `detect_overlaps(output_notes)` count and details (must be 0 for valid cases)

4. **Regression Test Runner**
   - Executes known cases from the test suite (embedded artifact, truncate previous, etc.)
   - For each: shows PASS/FAIL by comparing actual output to expected test assertions

### No Branch-Level Tracing Through Duplication
- The debug harness **will not** attempt to show which internal branch (embedded artifact, current overlong, next overlong, default) was taken
- If such detail is genuinely needed for debugging:
  - *Recommended approach*: Temporarily add conditional logging to the **production** implementation (guarded by a debug flag)
  - *Alternative*: Use a debugger/IDE to set breakpoints in the actual `cleanup_monophonic()`
- **Per constraint**: No instrumentation of production code will be implemented now

---

## Fate of Existing Files

| File | Action | Reason |
|------|--------|--------|
| `debug_trace.py` | **REPLACE** (part of consolidation) | Reimplemented algorithm; contained divergent next-note check |
| `debug_trace2.py` | **REPLACE** (part of consolidation) | Reimplemented algorithm; duplicated production logic |
| `debug_trace3.py` | **REPLACE** (part of consolidation) | Reimplemented algorithm; same issues as above |
| `fixed_cleanup.py` | **ARCHIVE/DELETE** | Stale experimental version with incorrect logic (next-note check) |
| `debug_note_positions.py` | **KEEP AS-IS** | Correctly imports production functions; debugs quantization/measure building (different pipeline stage) |
| `debug_measure_calculation.py` | **KEEP AS-IS** | Correctly uses production detection/quantization; debugs measure assignment (downstream stage) |
| `debug_final_measure.py` | **KEEP AS-IS** | Correctly imports production pipeline stages; end-to-end validation without logic duplication |

---

## Verification Properties

✅ **No second implementation**: Main execution path exclusively calls imported `cleanup_monophonic()`  
✅ **Regression validation**: Confirms production function passes known test cases  
✅ **Change transparency**: Shows exactly what the production function did to inputs  
✅ **Future-proof**: Cannot diverge from production because it contains zero algorithm logic  
✅ **Safe to run**: No risk of executing outdated/incorrect logic (eliminates the `debug_trace.py` problem)  

---

**This plan eliminates the root cause of our earlier contradiction: debug tools showing different behavior than production because they were running different code. All debugging fidelity now comes from observing the single, true implementation.**

## Current State

- v0.1 production code is authoritative.
- `app/src/transcription/monophonic_cleanup.py` currently contains the actual cleanup implementation.
- The earlier G4 truncation came from duplicated debug logic, not the production implementation.
- No production-code change is currently justified.
- `debug_trace.py`, `debug_trace2.py`, and `debug_trace3.py` contain duplicated/divergent implementations and should not be used as authoritative behavior.
- `fixed_cleanup.py` is stale experimental code.

## Next Action

Create the consolidated `debug_monophonic_cleanup.py` harness using an import-only approach:
- import `cleanup_monophonic`
- import `detect_overlaps`
- do not reimplement cleanup logic
- do not duplicate internal conditions
- compare input/output behavior
- run regression cases only after the harness is created and reviewed

Do not modify production cleanup logic unless a concrete failing test demonstrates an actual production bug.