import pygame
import pygame.midi
import time
from typing import List, Dict, Union
from concurrent.futures import ThreadPoolExecutor
import mido

# Define a Pattern as a dictionary
Pattern = Dict[str, Union[str, List[float], int]]

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

# Parse a MIDI file and extract patterns from a specific track
def midi_to_patterns(midi_file: str, track_name: str, bpm: int = 120) -> List[Pattern]:
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
                patterns.append({
                    "midi_note": msg.note,
                    "beats": [start_time / (60 / bpm)],  # Convert start_time to beats
                    "velocity": velocity,
                    "duration": duration,
                })

    print(f"Extracted {len(patterns)} patterns from track '{track_name}'")
    return patterns

# Play a pattern
def play_pattern(patterns: List[Pattern], bpm: int = 120, loop_beats: int = 32):
    beat_duration = 60 / bpm  # Duration of a single beat in seconds
    total_eighth_beats = loop_beats * 8  # Total eighth beats for the loop
    eighth_beat_duration = beat_duration / 8  # Duration of an eighth beat

    start_time = time.time()
    with ThreadPoolExecutor() as executor:
        for i in range(total_eighth_beats):
            current_time_in_beats = i / 8  # Current time in full beats (eighths divided by 8)

            for pattern in patterns:
                midi_note = pattern.get("midi_note")
                beat_schedule = pattern["beats"]
                velocity = pattern.get("velocity", 100)
                duration = pattern.get("duration", eighth_beat_duration)
                sound = pattern.get("sound")

                if current_time_in_beats in beat_schedule:
                    if midi_note is not None:
                        executor.submit(play_midi, midi_note, velocity, duration)
                    elif sound is not None:
                        executor.submit(play_sound, sound, velocity)

            # Wait for the next eighth-beat
            elapsed_time = time.time() - start_time
            wait_time = (i + 1) * eighth_beat_duration - elapsed_time
            if wait_time > 0:
                time.sleep(wait_time)

def repeat(beats, size=4, times=2):
    repeated_beats = []
    repeated_beats.extend(beats)
    for beat in beats:
        for i in range(1, times):
            repeated_beats.append(beat + size * i)  # Add the beat with the interval
    return repeated_beats

# Define patterns with audio and MIDI notes
beat_patterns = [
    {"sound": "bd", "beats":  list(range(4)) + [4, 5, 7.25], "velocity": 0.75}, # Bass drum
    {"sound": "sd", "beats":  repeat([1,3]), "velocity": 0.5},       # Snare, medium volume
    {"sound": "hh", "beats":  repeat([x / 4 for x in range(0, 8)] + [x / 8 for x in range(24, 32)]), "velocity": 0.5},  # Additional hits in the 4th bar
    # {"sound": "hho", "beats": [x + 0.5 for x in range(16)], "velocity": 0.5},  # Open hi-hat
]

if __name__ == '__main__':
    try:
        bpm = 80  # Set your desired BPM here
        loop_beats = 8  # Set your desired loop duration in beats here
        midi_file = "melody.mid"  # Path to your MIDI file
        track_name = "Synth Bass"  # Name of the track to extract patterns from

        print(f"Extracting patterns from {midi_file}, track: '{track_name}'")
        patterns = midi_to_patterns(midi_file, track_name, bpm=bpm)

        min_beat = min(pattern["beats"][0] for pattern in patterns)

        # Subtract the smallest beat value from all beat times
        for pattern in patterns:
            pattern["beats"] = [beat - min_beat for beat in pattern["beats"]]

        print(f"Playing at {bpm} BPM for {loop_beats} beats. Press Ctrl+C to stop playback.")
        while True:
            play_pattern(patterns + beat_patterns, bpm=bpm, loop_beats=loop_beats)
    except KeyboardInterrupt:
        print("\nStopping playback.")
        if midi_out:
            midi_out.close()
        pygame.midi.quit()
        pygame.quit()
