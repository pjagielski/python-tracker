import simpleaudio as sa

# Play a sound file
wave_obj = sa.WaveObject.from_wave_file("samples/bd.wav")
play_obj = wave_obj.play()
play_obj.wait_done()