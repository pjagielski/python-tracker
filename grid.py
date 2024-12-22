from random import random

import pygame
import pygame.midi
import time
import random
from typing import List, Dict, Union
from concurrent.futures import ThreadPoolExecutor
import mido

# Define a Pattern as a dictionary
Pattern = Dict[str, Union[str, List[float], int]]

# Initialize pygame mixer and MIDI
pygame.mixer.init()
pygame.midi.init()

# Screen dimensions
GRID_WIDTH = 800   # Width of the grid (in pixels)
GRID_HEIGHT = 400  # Height of the grid (in pixels)
PADDING = 100      # Equal padding for all sides


# Grid settings
GRID_ROWS = 12  # Number of piano keys per octave
GRID_COLS = 32  # Number of beats to display
CELL_WIDTH = GRID_WIDTH // GRID_COLS
CELL_HEIGHT = GRID_HEIGHT // GRID_ROWS
NOTE_LABEL_WIDTH = 50

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
NOTE_COLOR = (144, 238, 144)  # Light green
CURRENT_NOTE_COLOR = (255, 100, 100)  # Light red for the currently played note

# Setup display
pygame.init()
window_width = GRID_WIDTH + 2 * PADDING  # Add padding to both sides
window_height = GRID_HEIGHT + 2 * PADDING  # Add padding to both top and bottom

screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Piano Roll Grid")
# Initialize pygame font
pygame.font.init()
font = pygame.font.SysFont("Arial", 16)  # Use Arial, size 16
screen.fill(WHITE)


# MIDI Note Range (C0 = 24, B8 = 107)
MIDI_MIN_NOTE = 24
MIDI_MAX_NOTE = MIDI_MIN_NOTE + GRID_ROWS - 1  # Adjust range to grid rows

# Initialize pygame mixer and MIDI
pygame.mixer.init()
pygame.midi.init()

# Load the audio files
sounds = {
    "bd": pygame.mixer.Sound("samples/bd.wav"),
    "sd": pygame.mixer.Sound("samples/sd.wav"),
    "hh": pygame.mixer.Sound("samples/hh.wav"),
    "hho": pygame.mixer.Sound("samples/hho.wav"),
}

# Initialize MIDI output
midi_output_name = "IAC Driver Bus 1"
try:
    midi_out = mido.open_output(midi_output_name)
    print(f"MIDI output connected to {midi_output_name}")
except Exception as e:
    print(f"Error connecting to MIDI output: {e}")
    midi_out = None


def play_pattern(patterns: List[Pattern], bpm: int = 120, loop_beats: int = 32):
    """Play patterns with visualization."""
    beat_duration = 60 / bpm
    total_eighth_beats = loop_beats * 8
    eighth_beat_duration = beat_duration / 8

    start_time = time.time()
    with ThreadPoolExecutor() as executor:
        for i in range(total_eighth_beats):
            current_time_in_beats = i / 8
            played_notes = []

            for pattern in patterns:
                midi_note = pattern.get("midi_note")
                beat_schedule = pattern["beats"]
                velocity = pattern.get("velocity", 100)
                duration = pattern.get("duration", eighth_beat_duration)
                sound = pattern.get("sound")

                if current_time_in_beats in beat_schedule:
                    if midi_note is not None:
                        played_notes.append((midi_note, beat_schedule))  # Track note and beat
                        executor.submit(play_midi, midi_note, velocity, duration)
                    elif sound is not None:
                        executor.submit(play_sound, sound, velocity)

            # Determine if the screen should blink
            blink = (i % 8 == 0)  # Blink at the start of each beat

            # Draw the grid with the current beat and played notes
            draw_grid_from_patterns(patterns, current_time_in_beats % loop_beats, played_notes, blink)

            # Update the display
            pygame.display.flip()

            # Wait for the next eighth-beat
            elapsed_time = time.time() - start_time
            wait_time = (i + 1) * eighth_beat_duration - elapsed_time
            if wait_time > 0:
                time.sleep(wait_time)

            # Handle pygame events to keep the window interactive
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return


def get_note_name(midi_note: int) -> str:
    """Convert a MIDI note number to a note name (e.g., C4, D#4)."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    note_names.reverse()
    octave = (midi_note // 12) - 1
    note = note_names[midi_note % 12]
    return f"{note}{octave}"


# Function to play a sound
def play_sound(sound_name, volume: float = 1.0):
    if sound_name in sounds:
        sound = sounds[sound_name]
        sound.set_volume(volume)
        sound.play()


# Function to send a MIDI note
def play_midi(note: int, velocity: int = 100, duration: float = 0.5, delay: float = 0.025):
    if midi_out:
        time.sleep(delay)
        midi_out.send(mido.Message('note_on', note=note, velocity=velocity))
        time.sleep(duration)
        midi_out.send(mido.Message('note_off', note=note, velocity=0))

def midi_to_patterns(midi_file: str, track_name: str, bpm: int = 120, limit_beats: int = 8) -> List[Pattern]:
    """Extracts patterns from a specific track in a MIDI file, limited to a set number of beats."""
    mid = mido.MidiFile(midi_file)
    patterns = []
    ticks_per_beat = mid.ticks_per_beat
    seconds_per_tick = 60 / bpm / ticks_per_beat  # Convert MIDI ticks to seconds

    for track in mid.tracks:
        if track.name != track_name:
            continue

        current_time = 0
        active_notes = {}

        for msg in track:
            current_time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                start_time = current_time * seconds_per_tick
                active_notes[msg.note] = (start_time, msg.velocity)
            elif msg.type in ('note_off', 'note_on') and msg.note in active_notes:
                start_time, velocity = active_notes.pop(msg.note)
                duration = (current_time * seconds_per_tick) - start_time
                beat_start = start_time / (60 / bpm)
                if beat_start < limit_beats:
                    patterns.append({
                        "midi_note": msg.note,
                        "beats": [beat_start],  # Convert start_time to beats
                        "velocity": velocity,
                        "duration": duration,
                    })

    print(f"Extracted {len(patterns)} patterns from track '{track_name}' (up to {limit_beats} beats)")
    return patterns


def draw_grid_from_patterns(patterns, current_time_in_beats, played_notes, blink=False):
    """Draw the piano roll grid and visualize notes based on patterns."""
    background_color = (random.choice([0, 200]), random.choice([0, 200]), random.choice([0, 200])) if blink else WHITE
    screen.fill(background_color)

    # Draw labels for notes
    for row in range(GRID_ROWS):
        midi_note = MIDI_MIN_NOTE + row
        note_name = get_note_name(midi_note)
        label = font.render(note_name, True, BLACK)
        label_rect = label.get_rect(
            center=(PADDING // 2, row * CELL_HEIGHT + CELL_HEIGHT // 2 + PADDING)
        )
        screen.blit(label, label_rect)

    # Draw the grid
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            rect = pygame.Rect(
                col * CELL_WIDTH + PADDING,
                row * CELL_HEIGHT + PADDING,
                CELL_WIDTH,
                CELL_HEIGHT,
            )
            pygame.draw.rect(screen, WHITE, rect)
            pygame.draw.rect(screen, GRAY, rect, 1)

        # Draw beat dividers
        for beat in range(1, GRID_COLS // 8):
            divider_x = beat * 8 * CELL_WIDTH + PADDING
            pygame.draw.line(screen, BLACK, (divider_x, PADDING), (divider_x, PADDING + CELL_HEIGHT * GRID_ROWS - 1), 1)

    # Draw notes
    for pattern in patterns:
        midi_note = pattern.get("midi_note")
        beats = pattern.get("beats", [])
        duration = pattern.get("duration", 0.25)

        if midi_note is not None and MIDI_MIN_NOTE <= midi_note <= MIDI_MAX_NOTE:
            row = GRID_ROWS - (midi_note - MIDI_MIN_NOTE + 1)
            for beat in beats:
                col = int(beat * GRID_COLS / 8)
                # width = int(duration * GRID_COLS / 8 * CELL_WIDTH)
                rect = pygame.Rect(
                    col * CELL_WIDTH + PADDING,
                    row * CELL_HEIGHT + PADDING,
                    CELL_WIDTH,
                    CELL_HEIGHT,
                )

                # Highlight played notes
                is_current_note = any(
                    midi_note == note and abs(beat - current_time_in_beats) < 0.05
                    for note, played_beat in played_notes
                )
                color = CURRENT_NOTE_COLOR if is_current_note else NOTE_COLOR
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)

    pygame.display.flip()

beat_patterns = [
    {"sound": "bd", "beats": range(8), "velocity": 0.25},
    {"sound": "sd", "beats": [1, 3, 5, 7], "velocity": 0.25},
    {"sound": "hh", "beats": [x + 1/2 for x in range(8)] + [3.25, 6.75, 7.75], "velocity": 0.5},
]

if __name__ == '__main__':
    try:
        bpm = 120
        loop_beats = 8  # Limit to 8 beats for visualization
        midi_file = "melody.mid"
        track_name = "Synth Bass"

        # Extract patterns
        print(f"Extracting patterns from {midi_file}, track: '{track_name}'")
        patterns = midi_to_patterns(midi_file, track_name, bpm=bpm, limit_beats=12)

        # Align patterns to start at beat 0
        min_beat = min(pattern["beats"][0] for pattern in patterns)
        for pattern in patterns:
            pattern["beats"] = [beat - min_beat for beat in pattern["beats"]]

        print(f"Playing at {bpm} BPM for {loop_beats} beats. Press Ctrl+C to stop playback.")
        while True:
            play_pattern(patterns + beat_patterns, bpm=bpm, loop_beats=loop_beats)
    except KeyboardInterrupt:
        print("\nStopping playback.")
        pygame.quit()
