import pyaudio
import wave
import os
import numpy as np

def audio_routine(audio_queue, baby_is_crying):
    
    '''
    Routine that:
        + Acquires the audio feed
        + Determines if the baby is crying
    
    Some more features may be added to this routine, so do not overpopulate it 
    just because it looks empty.
    '''
    
    form_1 = pyaudio.paInt16
    chans = 1
    samp_rate = 48000
    chunk = 750
    dev_index = 2
    audio = pyaudio.PyAudio()
    
    try:
        
        audio = pyaudio.PyAudio()
        stream = audio.open(format = form_1, rate=samp_rate, channels=chans,
                            input_device_index = dev_index, input=True, frames_per_buffer=chunk)
    
        while True:
            
            data = stream.read(chunk,exception_on_overflow = False)
    
            # Send the frame to queue
            audio_queue.put(data)
    
    finally:
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
