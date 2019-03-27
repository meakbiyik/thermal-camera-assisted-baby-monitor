import random
from queue import Empty
from skimage import transform
from transform_matrix import calculate_transform_matrix
import sys
import cv2
import scipy.io as scio
import numpy as np

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
    try:
        
        ## Generate Temperature Dictionary from Black Body Calibrated Regression Data
        temp_data = scio.loadmat('temp_lut.mat')
        temp_vals = temp_data['temp_vals'][0,:]
        vals = temp_data['vals'][0,:]
        faceDetector = cv2.CascadeClassifier('C:\\Users\\toshiba\\Anaconda3\\Library\\etc\\haarcascades\\haarcascade_frontalface_default.xml')
        
        while True:
            
            # Get the frames
            try:
                # If no frame is fed to the queue by the video process for 10 seconds,
                # the method timeouts and gives an exception, which is caught below.
                bgr_frame, thermal_frame = bgr_thermal_queue.get(timeout = 10)
                thermal_raw = thermal_frame
                bgr_shp = bgr_frame.shape
                thermal_shp = thermal_frame.shape
                scale_factor = bgr_shp[0]/thermal_shp[0]
                ##########################################################
                ############# Calculate the transform matrix #############
                ##########################################################
                

                # Process the thermal frame
                cv2.normalize(thermal_frame, 
                              thermal_frame, 0, 255, cv2.NORM_MINMAX)
                
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
                # Try face detection
                
                faces = faceDetector.detectMultiScale(bgr_frame,1.3,8)
                trans_obj = transform.PolynomialTransform(transform_matrix)
                temperature = 36.5
                
                if isinstance(faces,tuple):# no face is detected
                    low = 30
                    high = 42
                    v_low = vals[temp_vals == low]
                    v_high = vals[temp_vals == high]
                    thermal_roi = thermal_raw[(thermal_raw <= v_high) & (thermal_raw >= v_low)]
                    maxval = np.max(thermal_roi)
                    tempreature = np.mean(temp_vals[(vals > maxval-0.75) && (vals < maxval+0.75)])                    
                                        
                else: # face is detected
                    for (x,y,w,h) in faces:
                        thermal_rect = np.array([(x,y),(x+w,y),(x,y+h),(x+w,y+h)]/scale_factor,dtype='float')
                        thermal_rect = trans_obj(thermal_rect).astype('int') # transform the bgr face region into thermal
                        tx = thermal_rect[0,0]
                        ty = thermal_rect[0,1]
                        tx_1 = thermal_rect[3,0]
                        ty_1 = thermal_rect[3,1]
                        thermal_face = thermal_raw[tx:tx_1,ty:ty_1]
                        maxval = np.max(thermal_face)
                        temperature = np.mean(temp_vals[(vals > maxval-0.75) && (vals < maxval+0.75)])
                ##########################################################
                ######## Put the acquired data into the variables ########
                ##########################################################
                
                with room_temp.get_lock():
                    room_temp.value = temperature
                with room_humid.get_lock():
                    room_humid.value = random.randint(800,1000)
                with baby_temp.get_lock():
                    baby_temp.value = random.randint(36,42)
                    
                with shared_transform_matrix.get_lock(): 
                    shared_transform_matrix[:] = transform_matrix.flatten()
                
            except Empty:
                print('Timeout -- frames could not be parsed to the control routine')
                sys.stdout.flush()
        
    finally:
        print('control routine stopped.')
        sys.stdout.flush()