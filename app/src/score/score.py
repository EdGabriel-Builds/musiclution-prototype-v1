"""
Score representation for music notation.

This module provides data structures for representing musical scores
built from quantized note and rest data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Union


@dataclass
class Note:
    """
    Represents a single musical note with quantized timing information.

    Attributes:
        pitch_name: Scientific pitch notation (e.g., "C4", "D#5")
        midi: MIDI note number (0-127)
        start_time: Start time in beats (quarter note beats)
        duration: Duration in beats (quarter note beats)
        velocity: Note velocity/amplitude (0.0-1.0)
    """
    pitch_name: str
    midi: int
    start_time: float
    duration: float
    velocity: float = 1.0

    def __post_init__(self):
        """Validate note properties after initialization."""
        if not 0 <= self.midi <= 127:
            raise ValueError(f"MIDI note must be between 0 and 127, got {self.midi}")
        if self.start_time < 0:
            raise ValueError(f"Start time must be non-negative, got {self.start_time}")
        if self.duration <= 0:
            raise ValueError(f"Duration must be positive, got {self.duration}")
        if not 0.0 <= self.velocity <= 1.0:
            raise ValueError(f"Velocity must be between 0.0 and 1.0, got {self.velocity}")


@dataclass
class Rest:
    """
    Represents a musical rest (silence) with quantized timing.

    Attributes:
        start_time: Start time in beats (quarter note beats)
        duration: Duration in beats (quarter note beats)
    """
    start_time: float
    duration: float

    def __post_init__(self):
        """Validate rest properties after initialization."""
        if self.start_time < 0:
            raise ValueError(f"Start time must be non-negative, got {self.start_time}")
        if self.duration <= 0:
            raise ValueError(f"Duration must be positive, got {self.duration}")


@dataclass
class Measure:
    """
    Represents a single measure in a musical score.

    Attributes:
        number: Measure number (1-indexed)
        events: List of musical events (Note or Rest) in chronological order.
        time_signature_top: Numerator of time signature (beats per measure)
        time_signature_bottom: Denominator of time signature (note value that gets the beat)
    """
    number: int
    events: List[Union[Note, Rest]] = field(default_factory=list)
    time_signature_top: int = 4
    time_signature_bottom: int = 4

    def __post_init__(self):
        """Validate measure properties after initialization."""
        if self.number < 1:
            raise ValueError(f"Measure number must be >= 1, got {self.number}")
        if self.time_signature_top <= 0:
            raise ValueError(f"Time signature top must be positive, got {self.time_signature_top}")
        if self.time_signature_bottom <= 0:
            raise ValueError(f"Time signature bottom must be positive, got {self.time_signature_bottom}")
        # Validate each event is either Note or Rest
        for i, event in enumerate(self.events):
            if not isinstance(event, (Note, Rest)):
                raise ValueError(
                    f"Event at index {i} must be Note or Rest, got {type(event).__name__}"
                )
        # Sort events by start_time to ensure chronological order
        self.events.sort(key=lambda e: e.start_time)

    @property
    def notes(self) -> List[Note]:
        """List of notes in this measure, preserving order."""
        return [event for event in self.events if isinstance(event, Note)]

    @property
    def rests(self) -> List[Rest]:
        """List of rests in this measure, preserving order."""
        return [event for event in self.events if isinstance(event, Rest)]

    def add_event(self, event: Union[Note, Rest]) -> None:
        """
        Add an event (Note or Rest) to the measure, maintaining sorted order by start_time.

        Args:
            event: A Note or Rest instance to add
        """
        if not isinstance(event, (Note, Rest)):
            raise TypeError("Event must be a Note or Rest instance")
        self.events.append(event)
        self.events.sort(key=lambda e: e.start_time)


@dataclass
class Score:
    """
    Represents a complete musical score.

    Attributes:
        title: Title of the piece
        composer: Composer name
        measures: List of measures in the score
        tempo_bpm: Beats per quarter note (defaults to 120)
    """
    title: str = ""
    composer: str = ""
    measures: List[Measure] = field(default_factory=list)
    tempo_bpm: float = 120.0

    def __post_init__(self):
        """Validate score properties after initialization."""
        if self.tempo_bpm <= 0:
            raise ValueError(f"Tempo must be positive, got {self.tempo_bpm}")

    def add_measure(self, measure: Measure) -> None:
        """
        Add a measure to the score.

        Args:
            measure: The measure to add
        """
        # Renumber measures to be sequential
        measure.number = len(self.measures) + 1
        self.measures.append(measure)

    def get_total_duration(self) -> float:
        """
        Calculate the total duration of the score in beats.

        Returns:
            Total duration in quarter note beats
        """
        if not self.measures:
            return 0.0

        total = 0.0
        for measure in self.measures:
            # Each measure's duration is based on its time signature
            measure_duration = measure.time_signature_top * (4.0 / measure.time_signature_bottom)
            total += measure_duration
        return total

    def get_all_notes(self) -> List[Note]:
        """
        Get all notes from all measures in the score.

        Returns:
            Flat list of all notes in the score
        """
        all_notes = []
        for measure in self.measures:
            all_notes.extend(measure.notes)
        return all_notes

    def get_all_events(self) -> List[List[Union[Note, Rest]]]:
        """
        Get all events (notes and rests) from all measures in the score.

        Returns:
            List of lists, each inner list contains events for a measure in chronological order.
        """
        return [measure.events for measure in self.measures]