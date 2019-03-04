import random
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
    
    import cv2
    writer = cv2.VideoWriter('video.mp4', 0x00000021, float(10.0), (640,480))
    i = 0
    
    try:
            
        while True:
            
            # Reading the frame 
            frame = frame_queue.get()
            
            # Reading the audio
            # audio = audio_queue.get()
            
            # Reading the values
            with room_temp.get_lock():
                current_room_temperature = room_temp.value
            with room_humid.get_lock():
                current_room_humidity = room_humid.value
            with baby_temp.get_lock():
                current_baby_temperature = baby_temp.value
            with baby_is_crying.get_lock():
                crying_detected = baby_is_crying.value
    
            writer.write(frame)
    
    finally:
        
            writer.release()
        
        
        