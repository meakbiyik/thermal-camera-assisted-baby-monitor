from multiprocessing import Process, Value, Array
from helper_modules.continuous_queue import ContinuousQueue as Queue

from ctypes import c_bool
from pexpect import pxssh
import sys

from audio._audio_routine import audio_routine
from video._video_routine import video_routine
from server._server_routine import server_routine
from control._control_routine import control_routine

from scipy.io import loadmat

# BEWARE! This code cannot be run from an IDE, as using an editor such as IPython
# prevents multiprocessing. Use command prompt or a similar environment, or run
# directly by python.exe

if __name__ == '__main__':
    
    # open server connection for test purposes
    s = pxssh.pxssh()

    hostname = '188.166.17.65'
    username = 'root'
    password = 'eee493494'

    s.login(hostname,username,password)
    s.sendline('cd enki_web')
    s.prompt()
    print('Server login.')

    s.sendline('source venv/bin/activate')
    s.prompt()
    
    s.sendline('kill $(lsof -t -i:8000)')
    s.prompt()
    
    s.sendline('cd VideoServer')
    s.prompt()

    s.sendline('python main3.py')
    print(s.prompt(timeout = 10))
    print('Server connected.')
    sys.stdout.flush()
    
    # Initialize queues. Frame and Audio queues are connected to server process,
    # but rgb and thermal frames are also fed into to control process via 
    # rgb_thermal_queue
    bgr_thermal_queue = Queue(2)
    frame_queue = Queue(5)
    audio_queue = Queue(10)
    
    # Initialize transform matrix, a shared memory for video and control processes.
    # NOTE TO SELF: give a sensible transform matrix for the initial case
    shared_transform_matrix = Array('d', [ 1.2e-10, 1.0, -1.678e-12,  4.914e-16, 2.2148e-15,  5.37e-15,
                                           -43.0823, -0.09724,  1.0, 0.00044159, -2.12523e-15,  7.937e-15])
    
    # Initialize shared memories for value types.
    room_temp = Value('f', 23.5)
    room_humid = Value('f', 36.09)
    baby_temp = Value('f', 0.0)
    baby_is_crying = Value(c_bool, False)
    temp_offset = Value('f', 0.0)
    
    # Load temperature map
    temp_table = loadmat('source/control/temperature_map.mat')['temp_table']
    temp_dict = {int(a[1]):a[0] for a in temp_table}
    
    
    # Initialize Process objects and target the necessary routines
    audio_process = Process(name = 'audio_process',
                            target=audio_routine, args=(audio_queue, baby_is_crying))
    video_process = Process(name = 'video_process',
                            target=video_routine, args=(frame_queue, bgr_thermal_queue,
                                                        temp_offset, temp_dict,
                                                        shared_transform_matrix))
    server_process = Process(name = 'server_process',
                             target=server_routine, args=(frame_queue, audio_queue,
                                                          room_temp, room_humid, baby_temp,
                                                          baby_is_crying))
    control_process = Process(name = 'control_process',
                              target=control_routine, args=(bgr_thermal_queue,
                                                            shared_transform_matrix,
                                                            room_temp, room_humid, baby_temp, temp_offset,
                                                            temp_dict))
    
    # Start the processes.
    video_process.start()
    audio_process.start()
    control_process.start()
    server_process.start()


