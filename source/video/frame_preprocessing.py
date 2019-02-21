'''
Helper functions for frame preprocessing.

Optimized by Just-in-Time (JIT) compilation and fastmath.
'''

import numba
from numba import njit
import numpy as np

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
    shift_frame = (norm_frame*255).astype(np.uint8)

    return shift_frame

import time
from skimage import img_as_ubyte
start = time.time()
b = img_as_ubyte(a)
mid = time.time()
c = (norm_frame*255).astype(np.uint8)
