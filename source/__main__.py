from multiprocessing import Process, Value, Array
from helper_modules.continuous_queue import ContinuousQueue as Queue

from ctypes import c_bool

from audio._audio_routine import audio_routine
from video._video_routine import video_routine
from server._server_routine import server_routine
from control._control_routine import control_routine

# BEWARE! This code cannot be run from an IDE, as using an editor such as IPython
# prevents multiprocessing. Use command prompt or a similar environment, or run
# directly by python.exe

if __name__ == '__main__':
    
    # Initialize queues. Frame and Audio queues are connected to server process,
    # but rgb and thermal frames are also fed into to control process via 
    # rgb_thermal_queue
    bgr_thermal_queue = Queue(2)
    frame_queue = Queue(5)
    audio_queue = Queue(10)
    
    # Initialize transform matrix, a shared memory for video and control processes.
    # NOTE TO SELF: give a sensible transform matrix for the initial case
    shared_transform_matrix = Array('d', [ 2.81291628e-11, 1.00000000e+00, -5.06955742e-13,  8.35398829e-16, -1.56637280e-15,  2.92389590e-15,
                                          -3.00482974e+01, 1.20000000e-01,  1.00000000e+00, -5.00000000e-04, 6.40729980e-16,  6.20157957e-16])
    
    # Initialize shared memories for value types.
    room_temp = Value('f', 0.0)
    room_humid = Value('f', 0.0)
    baby_temp = Value('f', 0.0)
    baby_is_crying = Value(c_bool, False)
    
    # Initialize Process objects and target the necessary routines
    audio_process = Process(name = 'audio_process',
                            target=audio_routine, args=(audio_queue, baby_is_crying))
    video_process = Process(name = 'video_process',
                            target=video_routine, args=(frame_queue, bgr_thermal_queue,
                                                        shared_transform_matrix))
    server_process = Process(name = 'server_process',
                             target=server_routine, args=(frame_queue, audio_queue,
                                                          room_temp, room_humid, baby_temp,
                                                          baby_is_crying))
    control_process = Process(name = 'control_process',
                              target=control_routine, args=(bgr_thermal_queue,
                                                            shared_transform_matrix,
                                                            room_temp, room_humid, baby_temp))
    
    # Start the processes.
    video_process.start()
    audio_process.start()
    control_process.start()
    server_process.start()


