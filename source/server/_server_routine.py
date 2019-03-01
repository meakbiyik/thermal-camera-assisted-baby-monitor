import sys
import numpy as np

def server_routine(frame_queue, audio_queue,
                   room_temp, room_humid, baby_temp,
                   baby_is_crying):
    
    '''
    Routine that:
        + Parses the data from all other routines
        + Synchronizes them if necessary
        + Sends the data to the server
       
    This routine needs continuous optimization. Do not overburden it. 
    Maybe multithreading can be added?
    '''
    
    while True:
        
        # Reading the frame 
        frame = frame_queue.get()
        
        # Reading the audio
        audio = audio_queue.get()
        
        # Reading the values
        with room_temp.get_lock():
            current_room_temperature = room_temp.value
        with room_humid.get_lock():
            current_room_humidity = room_humid.value
        with baby_temp.get_lock():
            current_baby_temperature = baby_temp.value
        with baby_is_crying.get_lock():
            crying_detected = baby_is_crying.value
        
        # Print the current inputs to the server to observe the changes
        print('room temperature: {}'.format(current_room_temperature))
        print('room humidity: {}'.format(current_room_humidity))
        print('baby temperature: {}'.format(current_baby_temperature))
        print('crying detected: {}'.format(crying_detected))
        print('frame mean: {}'.format(np.mean(frame)))
        print('audio mean: {}'.format(np.mean(audio)))
        sys.stdout.flush()
        