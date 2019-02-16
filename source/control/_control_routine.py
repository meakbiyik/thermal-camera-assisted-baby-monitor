import random
from multiprocessing.queues import Queue

def control_routine(rgb_thermal_queue,
                    shared_alignment_vector,
                    room_temp, room_humid, baby_temp):
    
    '''
    Routine that:
        + Checks the room temperature and humidity,
        + Detects the baby temperature,
        + If possible, recognizes the face of the baby,
        + Creates an alignment vector centered on the baby.
       
    Please be careful on modifying this part, as arguments except for the
    rgb_thermal_queue are not pythonic variables but rather Value or Arrays
    which behaves like an object, including a value (ctype) and a lock. This
    prevents any usual multiprocessing pitfalls, so always try to use
    a 'with' clause when utilizing them.
    '''
    
    while True:
        
        # Get the frames
        try:
            # If no frame is fed to the queue by the video process for 60 seconds,
            # the method timeouts and gives an exception, which is caught below.
            rgb_frame, thermal_frame = rgb_thermal_queue.get(timeout = 60)
                    
            # Data processing
            count = 0
            for i in range(random.randint(1,10) * 10**6):
                count += 1
            alignment_vector = (random.randint(1,10),random.randint(1,10))
            
            # Put data into variables
            with room_temp.get_lock():
                room_temp.value = random.randint(20,30)
            with room_humid.get_lock():
                room_humid.value = random.randint(800,1000)
            with baby_temp.get_lock():
                baby_temp.value = random.randint(36,42)
                
            with shared_alignment_vector.get_lock(): 
                shared_alignment_vector[:] = alignment_vector

        except Queue.empty:
            print('Timeout -- frames could not be parsed to the control routine')