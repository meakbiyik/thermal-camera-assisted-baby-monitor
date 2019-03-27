import sys
sys.path.append("..")

from helper_modules.pylepton import Lepton
from video.frame_preprocessing import float_to_uint8

from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import cv2
from skimage import transform
import time

def video_routine(frame_queue, bgr_thermal_queue, temp_offset, temp_dict, shared_transform_matrix):

    '''
    Routine that:
        + Acquires BGR and Thermal video frames,
        + Aligns them using the alignment vector provided by the control process,
        + overlaying them according to a predetermined colormap.
    
    It also feeds the frames into the control thread, but this action does not
    take much time (tested) and it doesn't need to be modified in the future.
    
    Beware that this routine takes the initial thermal frame first for better
    alignment, since the rgb is much faster. That is the reason for the thermal 
    capture before the 'while' loop.
    '''
        
    # IMPORTANT CONSTANTS
    RESOLUTION = (240,180) # Beware that this is the inverse of numpy ordering!
    NP_COMPAT_RES = (180,240)
    THERMAL_RES = (60,80)
    CHIP_DESELECT = 0.185 # Deselect duration after corruption, in miliseconds.
    
    # Initialize necessary variables
    transform_matrix = np.array([[ 2.81291628e-11, 1.00000000e+00, -5.06955742e-13,  8.35398829e-16, -1.56637280e-15,  2.92389590e-15],
                                 [-3.00482974e+01, 1.20000000e-01,  1.00000000e+00, -5.00000000e-04, 6.40729980e-16,  6.20157957e-16]])
    transform_obj = transform.PolynomialTransform(transform_matrix)
    
    # Initialize the BGR camera, set the resolution, create the empty memory 
    # array to get continuous frames
    bgr_camera = PiCamera()
    bgr_camera.resolution = RESOLUTION
    bgr_camera.sensor_mode = 4 # 4:3 aspect ratio, high frame rate, large FoV
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
        # Lepton sometimes return the same frame, so if the frame id is 
        # identical, no processing is necessary.
        # Walrus operator would be so nice to use here...
        raw_thermal_frame = False
        while not type(raw_thermal_frame) is np.ndarray:
            raw_thermal_frame, thermal_id = thermal_camera.capture(retry_reset = True,
                                                                   return_false_if_error = True)
            print('Waiting for correct frame')
            sys.stdout.flush()
            
        start_time = time.perf_counter()
        # Flag for the unique thermal frame and corrupted frame.
        # Corrupted frame flag carries a time value to leave
        # the chip deselected for CHIP_DESELECT duration
        thermal_frame_is_unique = True
        thermal_frame_is_corrupted = (False, time.perf_counter())
        
        # Start the loop! 
        # capture_continuous method just spits out the  BGR frames continuously. 
        for frame in bgr_camera.capture_continuous(bgr_output_array, format = 'bgr',
                                                   use_video_port = True):
            
            # Acquire the BGR frame
            # There was a copy() here. WAS IT NECESSARY, REALLY? CHECK.
            bgr_frame = np.flip(frame.array,0).astype(np.uint8)
            raw_thermal_frame = np.flip(raw_thermal_frame,0)
            
            # Do the processing if the thermal frame is unique. If not,
            # nothing much to do! 
            # BEWARE THAT raw_thermal_frame IS NOT USABLE! IF YOU WANT TO USE IT,
            # THEN A COPY IS NECESSARY!
            if( thermal_frame_is_unique):
                
                # Put them into the queue
                bgr_thermal_queue.put((bgr_frame, raw_thermal_frame))
                
                # Preprocess the thermal frame to clip the values into some
                # predetermined thresholds
                temperature_offset = temp_offset.value
                    
                # min_thresh = [x[0] for x in temp_dict.items() if x[1] == 32 + temperature_offset][0] # 32 and 42 degrees, respectively
                # max_thresh = [x[0] for x in temp_dict.items() if x[1] == 42 + temperature_offset][0]
                min_thresh = 7000
                max_thresh = 8000
                corrected_thermal_frame = np.clip(raw_thermal_frame, min_thresh, max_thresh)
        
                # Normalize thermal frame to 0-255
                cv2.normalize(corrected_thermal_frame, 
                              corrected_thermal_frame, 0, 255, cv2.NORM_MINMAX)
                
                # Acquire the transform matrix and if it is new, create transform object
                with shared_transform_matrix.get_lock(): 
                    new_transform_matrix = np.array(shared_transform_matrix).reshape((2,6))
                if not np.array_equal(new_transform_matrix, transform_matrix):
                    transform_matrix = new_transform_matrix
                    transform_obj = transform.PolynomialTransform(transform_matrix)
                
                # Warp the thermal image according to the transform object.
                # TODO: Correct the division by 255 thing, it is weird.
                warped_thermal_frame = transform.warp(corrected_thermal_frame.astype(float), transform_obj).astype(np.uint8)
                                
                # Scale the thermal frame to have the same size with the BGR.
                # Pyramid expand method from skimage creates a smoother output,
                # but the the difference in speed is more than 20x. So, we will
                # use this method from cv2.
                scale = NP_COMPAT_RES[0] / THERMAL_RES[0]
                scaled_thermal_frame = cv2.resize(warped_thermal_frame, None,
                                                  fx = scale, fy = scale,
                                                  interpolation = cv2.INTER_LINEAR)
                
                # Apply color map to the scaled frame
                # Beware that the output is also BGR.
                colored_thermal_frame = cv2.applyColorMap(scaled_thermal_frame,
                                                          cv2.COLORMAP_JET)
        
            # Sum the thermal and BGR frames (even if it is not unique)
            overlay = cv2.addWeighted(colored_thermal_frame, 0.25, bgr_frame, 0.75, 0)
            
            # Write temperature on overlay
            try:
                max_temp = temp_dict[int(np.max(raw_thermal_frame))] + temperature_offset
            except:
                pass
            
            cv2.putText(overlay, 'Max Temp: {}'.format(round(max_temp,2)),
                        (10,NP_COMPAT_RES[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.25, (255,255,255), 2)
                
            # Video processed!
            print('Unique frame' if thermal_frame_is_unique else 'Repeating frame')
            print('FPS: {}'.format(1/(time.perf_counter()- start_time)))
            start_time = time.perf_counter()
            sys.stdout.flush()
            
            # Send the frame to queue
            frame_queue.put(overlay)
            
            # Now, get the next thermal frame. First, check if the last thermal 
            # frame was corrupted. If not, just capture as usual.
            if( thermal_frame_is_corrupted[0]): 
                
                # If that is the case, check if CHIP_DESELECT time has passed since
                # the corruption. If so, take a new frame and turn the flag to False.
                # If not, just use the old frames as the new ones. The id's will 
                # be checked to prevent reprocessing in the next if block.
                if(time.perf_counter() - thermal_frame_is_corrupted[1] > CHIP_DESELECT):
                    new_raw_thermal_frame, new_thermal_id = thermal_camera.capture(retry_reset = False,
                                                                                   return_false_if_error = True)
                    thermal_frame_is_corrupted = (False, time.perf_counter())
                
                else:
                    new_raw_thermal_frame, new_thermal_id = raw_thermal_frame, thermal_id
            
            else:
                new_raw_thermal_frame, new_thermal_id = thermal_camera.capture(retry_reset = False,
                                                                               return_false_if_error = True)
            
            # If the capture was successful or the necessary time for the
            # corruption flag to be removed has not passed, check the uniqueness and 
            # continue. 
            if type(new_raw_thermal_frame) is np.ndarray:
                
                if thermal_id != new_thermal_id:
                    raw_thermal_frame = new_raw_thermal_frame
                    thermal_frame_is_unique = True
                else:
                    thermal_frame_is_unique = False
            
            # If the frame was corrupted, just use the old frames and set the 
            # corruption flag.
            else:
                thermal_frame_is_unique = False
                thermal_frame_is_corrupted = (True, time.perf_counter())
            
            # truncate the output array
            bgr_output_array.truncate(0)
    
    finally:
        
        thermal_camera.close_handle()
        bgr_camera.close()
        print('video routine stopped.')
        sys.stdout.flush()