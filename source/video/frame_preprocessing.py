'''
Helper functions for frame preprocessing.
'''

import numpy as np

def float_to_uint8(frame):
    '''
    Convert float64 frame to uint8.
    
    Numba does not optimize this function, as it is pretty optimized by itself.
    Faster than the generic version of skimage.
    '''
    
    conv_frame = (frame*256).astype(np.uint8)

    return conv_frame

