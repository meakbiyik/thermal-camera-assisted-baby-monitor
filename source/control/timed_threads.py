import random
from queue import Empty
from skimage import transform
from control.transform_matrix import _calculate_transform_matrix
import sys
import cv2
import Adafruit_DHT
import numpy as np
from scipy import stats
from subprocess import Popen, PIPE


def record_temp_humid_offset(DHT_sensor, DHT_pin,
                             room_temp, room_humid, temp_offset,
                             temp_dict, thermal_frame):
    '''
    Get the room temperature and humidity from the DHT sensor, calculate
    the temperature offset of the model with redpect to the room temperature.

    Parameters
    ----------
    DHT_sensor : int(?)
        DHT sensor value parsed from Adafruit_DHT.DHT22 property. Probably integer. 
    DHT_pin : int
        Pin of the DHT sensor.
    room_temp : multiprocessing.Value
        Shared memory of room temperature with lock.
    room_humid : multiprocessing.Value
        Shared memory of room humidity with lock.
    temp_offset : multiprocessing.Value
        Shared memory of temperature offset with lock.
    temp_dict : dictionary
        Piecewise quadratic mapping of the temperature model.
    thermal_frame: ndarray
        Thermal frame to calculate the offset of the model.
    
    Returns
    -------
    None
    
    '''
    print('thread 1')
    sys.stdout.flush()

    #room_humidity, room_temperature = Adafruit_DHT.read(DHT_sensor, DHT_pin)
    
    room_humidity = random.uniform(30,40)
    room_temperature = random.uniform(20,30)
    
    p = Popen(['sudo ./source/control/raspberrypi_video/raspberrypi_video'], shell = True, stdout = PIPE, stdin = PIPE)
    chip_temp_raw = int(p.stdout.readline().strip())
    chip_temp = (chip_temp_raw/100)-273
    print('***************************************')
    print('Chip Temperature= {}'.format(chip_temp))
    
    if room_humidity is not None:
    
        room_temp.value = float(room_temperature)
        room_humid.value = float(room_humidity)
        
        #temperature_offset = chip_temp - temp_dict[8192]
        temperature_offset = chip_temp
        temp_offset.value = float(round(temperature_offset, 1))

        print('Temperature Offset: {}'.format(temperature_offset))
        print('***************************************')
        sys.stdout.flush()


def calculate_transform_matrix(shared_transform_matrix,
                               bgr_frame, thermal_frame):
    '''
    Get the room temperature and humidity from the DHT sensor, calculate
    the temperature offset of the model with redpect to the room temperature.

    Parameters
    ----------
    thermal_frame: ndarray
        Thermal frame to calculate the offset of the model.
    bgr_frame: ndarray
        Thermal frame to calculate the offset of the model.
    shared_transform_matrix : multiprocessing.Array
        Shared memory of transformation matrix with lock.
    
    
    Returns
    -------
    None
    
    '''
            
    # Process the thermal frame
    normalized_thermal = cv2.normalize(thermal_frame, None, 0, 255, cv2.NORM_MINMAX)
    
    # Increasing the scale factor makes the canny hysteresis thresholds'
    # calculation unstable. 3 is determined to be an empirically sufficient
    # number for matriix calculation.
    scale_factor_of_thermal = 3
    
    # override max height and width. 
    max_height = 60*scale_factor_of_thermal
    
    # Expand-reduce frames to have the same size. Do not apply Gaussian smoothing,
    # since a total-variation denoising will be done later
    if(bgr_frame.shape[0]/max_height > 1):
        frame_BGR_res = transform.pyramid_reduce(bgr_frame, sigma = 0,
                                                 downscale = bgr_frame.shape[0]/max_height)
    else:
        frame_BGR_res = bgr_frame 
    frame_thermal_res = transform.pyramid_expand(normalized_thermal/255, sigma = 0,
                                                 upscale = scale_factor_of_thermal)#[:,:,0]
    
    # Calculate the transform matrix. Depth 8 is accurate enough for the task.
    # Increasing does not improve the results, and sometimes makes things
    # worse since the frames are not homogenously informative enough.
    transform_matrix = _calculate_transform_matrix(frame_BGR_res, frame_thermal_res,
                                                   division_depth = 8,
                                                   desired_thermal_scale = 1/scale_factor_of_thermal)

            
    with shared_transform_matrix.get_lock(): 
        shared_transform_matrix[:] = transform_matrix.flatten()
    
    print(transform_matrix)
    sys.stdout.flush()
    
    

def detect_face_location(bgr_frame, face_detector, faces_queue):
    
    print('thread 3')
    sys.stdout.flush()
    
    faces = face_detector.detectMultiScale(bgr_frame,1.2,3)

    if not isinstance(faces,tuple):  # if faces are returned
         
        faces_queue.put(faces)
        
    else:
        
        faces_queue.put(None)
        
        
        
        
