import random
import sys
import numpy as np

AUDIO_LENGTH = 512

def audio_routine(audio_queue, baby_is_crying):
    
    '''
    Routine that:
        + Acquires the audio feed
        + Determines if the baby is crying
    
    Some more features may be added to this routine, so do not overpopulate it 
    just because it looks empty.
    '''
    
    while True:
        
        # Audio processing
        count = 0
        for i in range(random.randint(1,10) * 10**7):
            count += 1
        created_audio = np.random.normal(size = (AUDIO_LENGTH,))
        print('audio processed')
        sys.stdout.flush()
        
        # Send the frame to queue
        audio_queue.put(created_audio)
        
        # Crying detected
        with baby_is_crying.get_lock():
            baby_is_crying.value = random.choice([True, False])