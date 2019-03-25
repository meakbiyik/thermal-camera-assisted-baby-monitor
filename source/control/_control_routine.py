import random
from queue import Empty
import sys
import cv2
import Adafruit_DHT
from control.timed_threads import record_temp_humid_offset, calculate_transform_matrix
from threading import Timer

def control_routine(bgr_thermal_queue,
                    shared_transform_matrix,
                    room_temp, room_humid, baby_temp, temp_offset,
                    temp_dict):
    
    '''
    Routine that:
        + Checks the room temperature and humidity,
        + Detects the baby temperature,
        + If possible, recognizes the face of the baby,
        + Creates an alignment vector centered on the baby.
       
    Please be careful on modifying this part, as arguments except for the
    bgr_thermal_queue are not pythonic variables but rather Value or Arrays
    which behaves like an object, including a value (ctype) and a lock. This
    prevents any usual multiprocessing pitfalls, so always try to use
    a 'with' clause when utilizing them.
    '''
    try:
        
        DHT_sensor = Adafruit_DHT.DHT22
        DHT_pin = 4
        
        bgr_frame, thermal_frame = bgr_thermal_queue.get()
        
        # Initiate and start timers.
        temp_hum_timer = Timer(1.0, record_temp_humid_offset, [DHT_sensor, DHT_pin, room_temp,
                                                               room_humid, temp_offset, temp_dict, thermal_frame])
        temp_hum_timer.start()
        
        alignment_timer = Timer(60.0, calculate_transform_matrix, [shared_transform_matrix,
                                                                   bgr_frame, thermal_frame])
        alignment_timer.start()
                
        
        while True:
            
            # Get the frames
            try:
                # If no frame is fed to the queue by the video process for 10 seconds,
                # the method timeouts and gives an exception, which is caught below.
                bgr_frame, thermal_frame = bgr_thermal_queue.get(timeout = 10)
             
##                if temp_hum_timer.finished:
##                    print('temp timer finished')
##                    sys.stdout.flush()
##                    temp_hum_timer.join()
##                    temp_hum_timer = Timer(1.0, record_temp_humid_offset, [DHT_sensor, DHT_pin,
##                                                                           room_temp, room_humid, temp_offset,
##                                                                           temp_dict, thermal_frame])
##                    temp_hum_timer.start()
##                
##                if alignment_timer.finished:
##                    print('alignment timer finished')
##                    sys.stdout.flush()
##                    alignment_timer.join()
##                    alignment_timer = Timer(60.0, calculate_transform_matrix, [shared_transform_matrix,
##                                                                               bgr_frame, thermal_frame])
##                    alignment_timer.start()
                
            except Empty:
                print('Timeout -- frames could not be parsed to the control routine')
                sys.stdout.flush()
        
    finally:
        # Cancel the timers
        temp_hum_timer.cancel()
        alignment_timer.cancel()
        
        print('control routine stopped.')
        sys.stdout.flush()
        