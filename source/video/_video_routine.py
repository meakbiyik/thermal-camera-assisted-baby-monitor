import sys
sys.path.append("..")

from helper_modules.pylepton import Lepton
from frame_preprocessing import preprocess_thermal_frame

from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import cv2
from skimage import transform
from skimage import img_as_ubyte

def _video_routine_without_exit(frame_queue, bgr_thermal_queue, shared_transform_matrix):

    '''
    Routine that:
        + Acquires RGB and Thermal video frames,
        + Aligns them using the alignment vector provided by the control process,
        + overlaying them according to a predetermined colormap.
    
    It also feeds the frames into the control thread, but this action does not
    take much time (tested) and it doesn't need to be modified in the future.
    
    Beware that this routine takes the initial thermal frame first for better
    alignment, since the rgb is much faster. That is the reason for the thermal 
    capture before the 'while' loop.
    '''
        
    # IMPORTANT CONSTANTS
    RESOLUTION = (640,480) # Beware that this is the inverse of numpy ordering!
    NP_COMPAT_RES = (480,640)
    THERMAL_RES = (60,80)
    
    # Initialize necessary variables
    transform_matrix = np.array([[ 2.81291628e-11, 1.00000000e+00, -5.06955742e-13,  8.35398829e-16, -1.56637280e-15,  2.92389590e-15],
                                 [-3.00482974e+01, 1.20000000e-01,  1.00000000e+00, -5.00000000e-04, 6.40729980e-16,  6.20157957e-16]])
    transform_obj = transform.PolynomialTransform(transform_matrix)
    
    # Initialize the BGR camera, set the resolution, create the empty memory 
    # array to get continuous frames
    bgr_camera = PiCamera()
    bgr_camera.resolution = RESOLUTION
    bgr_camera.framerate = 30
    bgr_output_array = PiRGBArray(bgr_camera, size=RESOLUTION)
    
    # Initialize the thermal camera, create the handle. 
    # DO NOT FORGET TO CLOSE IT MANUALLY!
    thermal_camera = Lepton("/dev/spidev0.1")
    thermal_camera.create_handle()
    
    # Wrap the function into a try/finally block to handle the exit
    try:
        
        # Take the first thermal frame to couple with the first BGR frame.
        # Wait if the frame is bad, until you get a good one.
        # Walrus operator would be so nice to use here...
        raw_thermal = False
        while not raw_thermal:
            raw_thermal_frame = thermal_camera.capture(retry_reset = True,
                                                       return_false_if_error = True)
        
        # Start the loop! 
        # capture_continuous method just spits out the  BGR frames continuously. 
        for frame in bgr_camera.capture_continuous(bgr_output_array, format = 'bgr',
                                                   use_video_port = True):
            
            # Acquire the BGR frame
            # There was a copy() here. WAS IT NECESSARY, REALLY? CHECK.
            bgr_frame = frame.array
            
            # Put them into the queue
            bgr_thermal_queue.put((bgr_frame, raw_thermal_frame))
            
            # Preprocess the thermal frame to be able to overlay it on the BGR frame.
            corrected_thermal_frame = preprocess_thermal_frame(raw_thermal)
    
            # Acquire the transform matrix and if it is new, create transform object
            with shared_transform_matrix.get_lock(): 
                new_transform_matrix = np.array(shared_transform_matrix)
            if( new_transform_matrix != transform_matrix):
                transform_matrix = new_transform_matrix
                transform_obj = transform.PolynomialTransform(transform_matrix)
            
            # Warp the thermal image according to the transform object
            warped_thermal_frame = transform.warp(corrected_thermal_frame, transform_obj)
            
            # Scale the thermal frame to have the same size with the RGB.
            scaled_thermal_frame = transform.pyramid_expand(warped_thermal_frame,
                                                            upscale = NP_COMPAT_RES[0]/THERMAL_RES[0])
            
            # Apply color map to the scaled frame
            # Beware that the output is also BGR.
            colored_thermal_frame = cv2.applyColorMap(img_as_ubyte(scaled_thermal_frame),
                                                      cv2.COLORMAP_JET)
    
            # Sum the thermal and BGR frames
            # Is BGR frame uint8? if not, CHANGE this part.
            overlay = cv2.addWeighted(colored_thermal_frame, 0.3, bgr_frame, 0.7, 0)
            
            # Flip the frames (necessary?)
            final_overlay = np.flip(overlay,0)
            
            # Video processed!
            print('video processed')
            sys.stdout.flush()
            
            # Send the frame to queue
            frame_queue.put(final_overlay)
            
            # Now, get the next thermal frame.
            # If you can't, use the old one.
            new_raw_thermal_frame = thermal_camera.capture(retry_reset = False,
                                                           return_false_if_error = True)
            if new_raw_thermal_frame:
                raw_thermal_frame = new_raw_thermal_frame
            
            # truncate the output array
            bgr_output_array.truncate(0)
    
    finally:
        
        thermal_camera.close_handle()