import random
from multiprocessing.queues import Queue
from skimage import transform
from transform_matrix import calculate_transform_matrix
import sys

def control_routine(bgr_thermal_queue,
                    shared_transform_matrix,
                    room_temp, room_humid, baby_temp):
    
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
    
    while True:
        
        # Get the frames
        try:
            # If no frame is fed to the queue by the video process for 10 seconds,
            # the method timeouts and gives an exception, which is caught below.
            bgr_frame, thermal_frame = bgr_thermal_queue.get(timeout = 10)
                    
            ##########################################################
            ############# Calculate the transform matrix #############
            ##########################################################
            
            # Increasing the scale factor makes the canny hysteresis thresholds'
            # calculation unstable. 3 is determined to be an empirically sufficient
            # number for matriix calculation.
            scale_factor_of_thermal = 3
            
            # override max height and width. 
            max_height = 60*scale_factor_of_thermal
            
            # Expand-reduce frames to have the same size. Do not apply Gaussian smoothing,
            # since a total-variation denoising will be done later
            frame_BGR_res = transform.pyramid_reduce(bgr_frame, sigma = 0,
                                                     downscale = bgr_frame.shape[0]/max_height)
            frame_thermal_res = transform.pyramid_expand(thermal_frame, sigma = 0,
                                                         upscale = max_height/thermal_frame.shape[0])
            
            # Calculate the transform matrix. Depth 8 is accurate enough for the task.
            # Increasing does not improve the results, and sometimes makes things
            # worse since the frames are not homogenously informative enough.
            transform_matrix = calculate_transform_matrix(frame_BGR_res, frame_thermal_res,
                                                          division_depth = 8)
            
            ##########################################################
            ######## Put the acquired data into the variables ########
            ##########################################################
            
            with room_temp.get_lock():
                room_temp.value = random.randint(20,30)
            with room_humid.get_lock():
                room_humid.value = random.randint(800,1000)
            with baby_temp.get_lock():
                baby_temp.value = random.randint(36,42)
                
            with shared_transform_matrix.get_lock(): 
                shared_transform_matrix[:] = transform_matrix

        except Queue.empty:
            print('Timeout -- frames could not be parsed to the control routine')
            sys.stdout.flush()
        
        finally:
            print('control routine stopped.')
            sys.stdout.flush()