import mido
import time

# List available MIDI outputs
print("Available MIDI outputs:", mido.get_output_names())

# Open the IAC Driver as the MIDI output
with mido.open_output("IAC Driver Bus 1") as output:
    # Send a Middle C note on message
    output.send(mido.Message('note_on', note=60, velocity=64))  # Middle C
    time.sleep(1)
    # Send a note off message
    output.send(mido.Message('note_off', note=60, velocity=64))
