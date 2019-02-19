import random
import sys
import numpy as np
from skimage import transform

import release
        
FRAME_HEIGHT = 768
FRAME_WIDTH = 1024

def video_routine(frame_queue, rgb_thermal_queue, shared_transform_matrix):

    '''
    Routine that:
        + Acquires RGB and Thermal video frames,
        + Aligns them using the alignment vector provided by the control process,
        + overlaying them according to a predetermined colormap.
    
    It also feeds the frames into the control thread, but this action does not
    take much time (tested) and it doesn't need to be modified in the future.
    '''
    
    while True:
        
        # Acquire the frame
        rgb_frame = np.random.normal(size = (FRAME_HEIGHT,FRAME_WIDTH))
        thermal_frame = np.random.normal(size = (FRAME_HEIGHT,FRAME_WIDTH))
        
        # Put them into the queue
        rgb_thermal_queue.put((rgb_frame, thermal_frame))
        
        # Acquire the transform matrix and create tansform object
        with shared_transform_matrix.get_lock(): 
            transform_matrix = np.array(shared_transform_matrix)
        transform_obj = transform.PolynomialTransform(transform_matrix)
        print('transform_matrix: {}'.format(transform_matrix))
        sys.stdout.flush()
        
        # Warp the thermal image according to the transform object
        warped_thermal = transform.warp(thermal_frame, transform_obj)
        
        # Video processing 
        count = 0
        for i in range(random.randint(1,10) * 10**7):
            count += 1
        created_frame = np.random.normal(size = (FRAME_HEIGHT,FRAME_WIDTH))
        print('video processed')
        sys.stdout.flush()
        
        # Send the frame to queue
        frame_queue.put(created_frame)