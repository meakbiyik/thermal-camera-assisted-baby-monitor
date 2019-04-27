import pyaudio
import wave
import os
import numpy as np
import audioop
import sys
import math
from collections import deque
import time

def audio_routine(audio_queue, baby_is_crying):
    
    '''
    Routine that:
        + Acquires the audio feed
        + Determines if the baby is crying
    
    Some more features may be added to this routine, so do not overpopulate it 
    just because it looks empty.
    '''
    
    form_1 = pyaudio.paInt16
    chans = 2
    samp_rate = 48000
    chunk = 1500
    dev_index = 2
    audio = pyaudio.PyAudio()
    
    rms_deque = deque([0]*8, 8)
    print_counter = 0
    
    cry_timer = time.perf_counter()
    CRYING_LIMIT = 5
    baby_is_crying.value = False
    
    try:
        
        audio = pyaudio.PyAudio()
        stream = audio.open(format = form_1, rate = samp_rate, channels = chans,
                            input_device_index = dev_index, input=True, frames_per_buffer=chunk)
    
        while True:
            
            data = stream.read(chunk ,exception_on_overflow = False)
            
            # Send the frame to queue
            audio_queue.put(data)
            
            rms = 20 * math.log10(audioop.rms(data, 2))
            rms_deque.append(rms)
            
            mean_rms = np.mean(np.array(rms_deque))
            
            print_counter += 1
            if( print_counter == 5):
                print('Averaged RMS: {}'.format(mean_rms))
                sys.stdout.flush()
                print_counter = 0
            
            peak_count = np.count_nonzero( np.array(rms_deque) > 50)
            
            if( peak_count > 4):
                baby_is_crying.value = True
                cry_timer = time.perf_counter()
            elif (time.perf_counter() - cry_timer > CRYING_LIMIT):
                baby_is_crying.value = False

    
    finally:
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
