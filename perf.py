import pygame
import time
import mido

# Constants
GRID_WIDTH = 800
GRID_HEIGHT = 400
PADDING = 100
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLINK_COLOR = (240, 240, 255)  # Subtle blink effect
NOTE_COLOR = (144, 238, 144)
CURRENT_NOTE_COLOR = (255, 100, 100)

# Initialize pygame
pygame.init()
pygame.mixer.init()
pygame.font.init()

# Screen setup
window_width = GRID_WIDTH + 2 * PADDING
window_height = GRID_HEIGHT + 2 * PADDING
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Piano Roll Grid")
font = pygame.font.SysFont("Arial", 16)
clock = pygame.time.Clock()

# Initialize MIDI output
midi_output_name = "IAC Driver Bus 1"
try:
    midi_out = mido.open_output(midi_output_name)
    print(f"MIDI output connected to {midi_output_name}")
except Exception as e:
    print(f"Error connecting to MIDI output: {e}")
    midi_out = None

def play_pattern_with_visuals(patterns, bpm=120, loop_beats=8):
    """Play patterns and visualize them with smooth timing."""
    beat_duration = 60 / bpm
    eighth_beat_duration = beat_duration / 8
    total_beats = loop_beats * 8

    start_time = time.perf_counter()
    last_blink_time = 0
    is_blinking = False

    while True:
        # Timing calculation
        elapsed_time = time.perf_counter() - start_time
        current_beat = (elapsed_time / beat_duration) % loop_beats
        eighth_beat = int((elapsed_time / eighth_beat_duration) % total_beats)

        # Blink effect on each beat
        if int(current_beat) != last_blink_time:
            last_blink_time = int(current_beat)
            is_blinking = True
        else:
            is_blinking = False

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # Playback and visualization
        played_notes = []
        for pattern in patterns:
            midi_note = pattern.get("midi_note")
            beats = pattern.get("beats", [])
            duration = pattern.get("duration", eighth_beat_duration)

            # Schedule notes for playback
            for beat in beats:
                if abs(current_beat - beat) < 0.05:  # Within tolerance
                    if midi_note not in played_notes:
                        played_notes.append(midi_note)
                        play_midi(midi_note, velocity=pattern.get("velocity", 100), duration=duration)

        # Draw visuals
        draw_grid_from_patterns(patterns, current_beat, played_notes, is_blinking)

        # Update display and enforce frame rate
        pygame.display.flip()
        clock.tick(FPS)

def draw_grid_from_patterns(patterns, current_beat, played_notes, is_blinking):
    """Draw the piano roll grid with current notes and blink effect."""
    # Blink background on each beat
    screen.fill(BLINK_COLOR if is_blinking else WHITE)

    # Draw rows and columns
    for row in range(12):
        for col in range(32):
            rect = pygame.Rect(
                col * (GRID_WIDTH // 32) + PADDING,
                row * (GRID_HEIGHT // 12) + PADDING,
                GRID_WIDTH // 32,
                GRID_HEIGHT // 12
            )
            pygame.draw.rect(screen, WHITE, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

    # Highlight played notes
    for pattern in patterns:
        midi_note = pattern.get("midi_note")
        if midi_note in played_notes:
            color = CURRENT_NOTE_COLOR
        else:
            color = NOTE_COLOR

        for beat in pattern.get("beats", []):
            col = int(beat * (32 / 8))  # Map beats to grid columns
            row = 12 - (midi_note % 12 + 1)  # Reverse rows for notes
            rect = pygame.Rect(
                col * (GRID_WIDTH // 32) + PADDING,
                row * (GRID_HEIGHT // 12) + PADDING,
                GRID_WIDTH // 32,
                GRID_HEIGHT // 12
            )
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

def play_midi(note: int, velocity: int = 100, duration: float = 0.5, delay: float = 0.025):
    if midi_out:
        time.sleep(delay)
        midi_out.send(mido.Message('note_on', note=note, velocity=velocity))
        time.sleep(duration)
        midi_out.send(mido.Message('note_off', note=note, velocity=0))


# Example MIDI patterns
patterns = [
    {"midi_note": 60, "beats": [0, 2, 4, 6], "velocity": 100, "duration": 0.25},
    {"midi_note": 62, "beats": [1, 3, 5, 7], "velocity": 100, "duration": 0.25},
]

# Run the playback
play_pattern_with_visuals(patterns, bpm=120, loop_beats=8)
