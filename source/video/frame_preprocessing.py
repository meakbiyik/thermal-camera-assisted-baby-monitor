'''
Helper functions for frame preprocessing.

Optimized by Just-in-Time (JIT) compilation and fastmath.
'''

import numba
from numba import njit
import numpy as np

def float_to_uint8(frame):
    '''
    Convert float64 frame to uint8.
    
    Numba does not optimize this function, as it is pretty optimized by itself.
    '''
    
    conv_frame = (frame*256).astype(np.uint8)

    return conv_frame

@njit(numba.uint8[:,:](numba.uint16[:,:]), fastmath = True)
def preprocess_thermal_frame(frame):
    
    threshold_low = 7250 
    threshold_high = 7400 
    
    h,w = frame.shape
    for i in range(h):
        for j in range(w):
            elem = frame[i,j]
            if(elem > threshold_high):
                frame[i,j] = threshold_high
            elif(elem < threshold_low):
                frame[i,j] = threshold_low
    
    norm_frame = (frame - threshold_low) / (threshold_high - threshold_low)
    shift_frame = (norm_frame*256).astype(np.uint8)
    
    ## maybe use this?
    ## cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX) # extend contrast
    ## np.right_shift(a, 8, a) # fit data into 8 bits

    return shift_frame