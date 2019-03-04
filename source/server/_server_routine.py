import random
import sys
import numpy as np

import io
import socket

import struct
from time import time
from time import sleep
from PIL import Image

def server_routine(frame_queue, audio_queue,
                   room_temp, room_humid, baby_temp,
                   baby_is_crying):
    '''
       Routine that:
           + Parses the data from all other routines
           + Synchronizes them if necessary
           + Sends the data to the server

       This routine needs continuous optimization. Do not overburden it.
       Maybe multithreading can be added?
    '''

    # Connect a client socket to my_server:8000 (change my_server to the
    # hostname of your server)
    client_socket = socket.socket()
    client_socket.connect(('188.166.17.65', 8000))

    # Make a file-like object out of the connection
    connection = client_socket.makefile('wb')


    start_stream = False
    want_image = b'w'
    send_image = b's'


    try:
        stream = io.BytesIO()
        while True:
            #         #
            # # Reading the audio
            # audio = audio_queue.get()
            #
            # # Reading the values
            # with room_temp.get_lock():
            #     current_room_temperature = room_temp.value
            # with room_humid.get_lock():
            #     current_room_humidity = room_humid.value
            # with baby_temp.get_lock():
            #     current_baby_temperature = baby_temp.value
            # with baby_is_crying.get_lock():
            #     crying_detected = baby_is_crying.value

            if not start_stream:


                start = time()

                # Possible addition of non-blocking arguments and select will be considered
                answer = client_socket.recv(128)


                if answer == want_image:
                    start_stream = True
                    client_socket.send(send_image)

            else:
                frame = frame_queue.get()


                stream.write(frame.tobytes())
                # Write the length of the capture to the stream and flush to
                # ensure it actually gets sent
                connection.write(struct.pack('<L', stream.tell()))
                connection.flush()
                # Rewind the stream and send the image data over the wire
                stream.seek(0)
                connection.write(stream.read())
                # Reset the stream for the next capture
                stream.seek(0)
                stream.truncate()





    finally:
        connection.close()
        client_socket.close()