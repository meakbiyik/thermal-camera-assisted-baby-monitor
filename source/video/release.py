import sys
sys.path.append("..")

#import packs

from helper_modules.pylepton import Lepton

from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import numpy as np
import cv2
from matplotlib import pyplot as plt
import socket
import sys
import pickle
import struct
import numba
from numba import njit
from frameAligner import get_alignment_vector

import io
import json
import scipy.io as scio
#
#RESOLUTION = (640,480)
#diff_h,diff_w = 65,0
#tape_mask = np.zeros((640-diff_h,480))
#rgb_camera = PiCamera()
#rgb_camera.resolution = RESOLUTION
#thermal_camera = Lepton("/dev/spidev0.1")
#thermal_camera.create_handle()   # do not forget to destroy the handle!
##camera.framerate = 25
#rawCapture = PiRGBArray(rgb_camera, size=RESOLUTION)
##Temperature LUT
#temple = scio.loadmat('temp_table.mat')['temp_table'] 
##camera warmup
#time.sleep(0.1)
#
###########################################################
#################### HELPER FUNCTIONS #####################
###########################################################
#
#@njit(numba.uint8[:,:](numba.uint16[:,:]), fastmath = True)
#def preprocess_thermal_frame(frame):
#    
#
#    threshold_low = 7250 
#    threshold_high = 7400 
#    
#    h,w = frame.shape
#    for i in range(h):
#        for j in range(w):
#            elem = frame[i,j]
#            if(elem > threshold_high):
#                frame[i,j] = threshold_high
#            elif(elem < threshold_low):
#                frame[i,j] = threshold_low
#    
#    min_v = np.min(frame)
#    max_v = np.max(frame)
#    
#    norm_frame = (frame - threshold_low) / (threshold_high - threshold_low)
#    shift_frame = (norm_frame*255).astype(np.uint8)
#
#    return shift_frame
#
#@njit(numba.uint8[:,:,:](numba.uint8[:,:,:], numba.uint8[:,:,:]), fastmath = True)
#def overlay_frames(thermal,rgb):
#    
#    weight = 0.3
#    weight_inverse = 1-weight
#    overlay = (rgb*weight_inverse + thermal*weight).astype(np.uint8)
#    
#    return overlay
#
#def firstTimeTapeMask(rgb_first):
#    rgb_first = rgb_first[:-diff_h,:,:]
###    tape_mask = rgb_first[rgb_first< 20)]
#    tape_mask = (rgb_first[:,:,0] < 40)*(rgb_first[:,:,1] < 40)*(rgb_first[:,:,2] < 40)
#    return tape_mask
#
#def tempMeasure(mask,raw_thermal):
#    global temple
#    thermal = cv2.resize(raw_thermal,RESOLUTION)
#    thermal = thermal[diff_h:,:]
#    masked_thermal = thermal*tape_mask
#    avg = masked_thermal[masked_thermal!=0].max()
#    temp_table = temple
#    print('Average pixel value ' + str(avg))
#    for p in range(temp_table.shape[0]):
#        if temp_table[p,1] >= avg:
#            return temp_table[p,0]            
#    
#    
#    
###clientsocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
###clientsocket.connect(('207.154.226.66',8089))
#
#VIDEO_DUR = 100 #seconds
#FPS_LIMIT = 5
#
#
#thermal_capture_flag = (True,0)
#thermal = None
#calibrated = False
#
##CREATE VIDEO WRITER
#writer = cv2.VideoWriter('video.mp4', cv2.VideoWriter_fourcc(*'MJPG'), float(FPS_LIMIT), (640,415))
#frmcnt = 0
#tmp = 0
#for frame in rgb_camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
#    
#    if( not calibrated):
#    # Find the alignment parameters:
#        raw_thermal = thermal_camera.capture(retry_reset = False, return_false_if_error = True)
#        if(raw_thermal):
#            thermal = preprocess_thermal_frame(raw_thermal[0][:,:,0])
#            #diff_h, diff_w = get_alignment_vector(frame.array.copy(), thermal)
#            diff_h, diff_w = 65,0
#            print(diff_h, diff_w)
#            calibrated = True
#            rawCapture.truncate(0)
#            # DETERMINE START TIME
#            START_TIME = time.time()
#            
#    elif (time.time() - START_TIME < VIDEO_DUR):
#    
#        timeStamp = time.time()
#        rgb = frame.array.copy()
#        
#        timeStamp2 = time.time()
#        if( thermal_capture_flag[0]):
#            raw_thermal, _ = thermal_camera.capture(retry_reset = False, return_false_if_error = True)
#            if( raw_thermal is False): #if output is invalid, do not invoke the capture method for 185 ms
#                print('BAD')
#                thermal_capture_flag = (False, time.time())
#            else:
#                print('GOOD')
#                if frmcnt == 0:
###                    tape_mask = firstTimeTapeMask(rgb)
#                    frmcnt +=1
#                tape_mask = firstTimeTapeMask(rgb)
#                tmp = tempMeasure(tape_mask,raw_thermal) -19.25
#                print('Temperature of dark pixels: ' + str(tmp))
#
#                
#                #cv2.imwrite('thermal.jpg', np.flip(raw_thermal,0))
#                
#                thermal = preprocess_thermal_frame(raw_thermal[:,:,0])
#        else:
#            if(time.time() - thermal_capture_flag[1] >= 0.25):
#                print('BAD-REST')
#                thermal_capture_flag = (True,0)
#
#        ################################################################
#        # Overlay
#        ################################################################
#        
#        # Capture Images from the Camera and save files
#        if(thermal is not None):
#            thermal[thermal < 170] = 0
#            thermal_colormap = cv2.applyColorMap(thermal, cv2.COLORMAP_JET)
#            thermal_resized = cv2.resize(thermal_colormap,RESOLUTION)
#            
#            if(diff_h < 0 and diff_w == 0):
#            
#                overlay = overlay_frames(thermal_resized[:diff_h,:,:], rgb[-diff_h:,:,:])
#            
#            elif(diff_h < 0 and diff_w > 0):
#                
#                overlay = overlay_frames(thermal_resized[:diff_h,diff_w:,:], rgb[-diff_h:,:-diff_w,:])
#            
#            elif(diff_h > 0 and diff_w > 0):
#                
#                overlay = overlay_frames(thermal_resized[diff_h:,:diff_w,:], rgb[:-diff_h,-diff_w:,:])
#            
#            elif(diff_h > 0 and diff_w == 0):
#                
#                overlay = overlay_frames(thermal_resized[diff_h:,:,:], rgb[:-diff_h,:,:])
#                
#            #elapsedTime = time.time() - timeStamp
#            #print('Elapsed time: ' + str(elapsedTime))
#            rawCapture.truncate(0)
#            
#        while (time.time() - timeStamp) < (1/FPS_LIMIT):
#            time.sleep(1/FPS_LIMIT*0.01)
#        
#        print('Total time: ' + str(time.time() - timeStamp))
#        fliplay = np.array(np.flip(overlay,0))
#        cv2.putText(fliplay, 'Average Temperature: ' + '{0:.1f}'.format(round(tmp,2)),(50,50),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,255))
#        writer.write(fliplay)
#        
#    else:
#        
#        #cv2.imwrite('overlay.jpg', np.flip(overlay,0))
#        writer.release()
#        thermal_camera.close_handle()
#        break
######################################################################################
#### Overlay ended
######################################################################################
###
####Server codeee
### 
###
###    memfile = io.BytesIO()
###    np.save(memfile, gray_overlay)
###    memfile.seek(0)
###    data = json.dumps(memfile.read().decode('latin-1'))
###
###    # clientsocket.sendall(struct.pack("L", len(data))+data)
###    z = struct.pack("L", len(data))
###  
###    data = bytes(data, 'latin-1')
###  
###    
###    clientsocket.sendall(z+data)
###
###
####Server code end
###
###     
###    key = cv2.waitKey(1) & 0xFF
###    rawCapture.truncate(0)
###    
###               
###    if key == ord("q"):
###        break

