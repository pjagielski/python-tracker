from mido import MidiFile
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_html_grid(notes, ticks_per_beat, title="Piano Roll"):
    # HTML structure for visualization
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            .piano-roll {{
                position: relative;
                width: 100%;
                height: 800px;
                border: 1px solid black;
                background-color: #f9f9f9;
            }}
            .note {{
                position: absolute;
                background-color: blue;
                opacity: 0.7;
                height: 20px;
                border-radius: 5px;
            }}
            .grid-line {{
                position: absolute;
                width: 100%;
                height: 1px;
                background-color: #ddd;
            }}
            .note-label {{
                position: absolute;
                left: -50px;
                top: -10px;
                font-size: 12px;
                color: black;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="piano-roll">
            <!-- Piano roll grid -->
            {generate_grid_lines()}
            {generate_notes_html(notes)}
        </div>
    </body>
    </html>
    """
    return html

def generate_grid_lines():
    # Create horizontal grid lines for the piano roll (at every 10th beat)
    grid_lines_html = ""
    for i in range(0, 500, 10):  # Adjust the range to cover enough time
        grid_lines_html += f'<div class="grid-line" style="top: {i * 20}px;"></div>'
    return grid_lines_html

def generate_notes_html(notes):
    # Create a div for each note in the piano roll
    notes_html = ""
    for note in notes:
        start_time = note['start_time'] * 10  # Adjust to fit the grid scale
        duration = note['duration'] * 10  # Adjust to fit the grid scale
        top_position = (128 - note['note']) * 10  # Adjust to fit the Y axis
        notes_html += f"""
            <div class="note" style="left: {start_time}px; width: {duration}px; top: {top_position}px;">
                <div class="note-label">{note['note']}</div>
            </div>
        """
    return notes_html

def extract_notes(file_path, track_name="Synth Bass"):
    """
    Extract note-on and note-off events from a specific track in a MIDI file.

    :param file_path: Path to the MIDI file
    :param track_name: Name of the track to extract events from (default is "Synth Bass")
    :return: List of dictionaries with note, start_time, duration
    """
    midi_file = MidiFile(file_path)
    notes = []
    active_notes = {}  # Track active notes with start times
    current_time = 0  # Cumulative time in ticks
    track_found = False  # Flag to indicate if we have found the desired track

    for track in midi_file.tracks:
        # Look for the track name in the meta messages
        track_name_found = False
        for msg in track:
            if msg.type == 'track_name' and msg.name == track_name:
                track_name_found = True
                track_found = True
                print(f"Processing track: {msg.name}")  # Debug: Show track name
                break

        if track_found and track_name_found:
            for msg in track:
                current_time += msg.time  # Increment cumulative time
                if msg.type == "note_on" and msg.velocity > 0:
                    print(f"Note ON: {msg.note}, Time: {current_time}")  # Debug
                    active_notes[msg.note] = current_time
                elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                    if msg.note in active_notes:
                        start_time = active_notes.pop(msg.note)
                        duration = current_time - start_time
                        print(f"Note OFF: {msg.note}, Start: {start_time}, Duration: {duration}")  # Debug
                        notes.append({
                            "note": msg.note,
                            "start_time": start_time,
                            "duration": duration,
                        })
    # Normalize the start times to start from 0
    if notes:
        first_start_time = notes[0]['start_time']
        for note in notes:
            note['start_time'] -= first_start_time  # Normalize

    return notes, midi_file.ticks_per_beat

if __name__ == "__main__":
    midi_file_path = "melody.mid"  # Path to your MIDI file
    notes, ticks_per_beat = extract_notes(midi_file_path, track_name="Synth Bass")
    html_output = generate_html_grid(notes, ticks_per_beat=480)  # Pass the appropriate ticks_per_beat
    with open("piano_roll.html", "w") as file:
        file.write(html_output)
    print("Piano roll saved as 'piano_roll.html'. Open it in a browser.")
