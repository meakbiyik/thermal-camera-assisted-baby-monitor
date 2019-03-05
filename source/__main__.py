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
    shared_transform_matrix = Array('d', [1.488387477669542e-10,0.999999999999626,-1.9870623558887407e-12,
                                          3.850823241355083e-16,2.102969679454136e-15,6.344844602420193e-15,
                                          -49.96998927342663,0.08376337829892767,1.0000000000002376,
                                          -0.00028744912595213376,-1.5893570880750632e-15,3.3603285430256703e-15])
    
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


