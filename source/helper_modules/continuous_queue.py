from multiprocessing.queues import Queue
import multiprocessing
import sys

class ContinuousQueue(Queue):
    
    '''A class inheriting Queue (from multiprocessing package). Instead of giving
    an exception when user tries to put a new object to a full queue, this version
    dumps the last object to free a slot for the incoming data.'''
    
    def __init__(self, maxsize):
        
        # A necessary evil. Do not question it.
        ctx = multiprocessing.get_context()
        
        super().__init__(maxsize, ctx = ctx)
    
    def dump(self):
        '''Dump the object at the end of the queue. This is basically get()
        without a return functionality.'''
        
        with self._rlock:
            self._recv_bytes()
        self._sem.release()
    
    # Override put function
    def put(self, obj, block=True, timeout=None):
        '''Instead of just queuing the object and blocking if the queue
        is full, this method checks whether the queue is full first and
        dumps the oldest object if so.'''
        
        if(self.full()):
            self.dump()
        
        super().put(obj, block, timeout)