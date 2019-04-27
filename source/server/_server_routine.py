import random
import sys
import numpy as np
import cv2

import io
import socket

import struct
import time

import urllib.request
import json      

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
    
    # Connect a client socket to my_server:2000 (change my_server to the
    # hostname of your server)
    client_socket_video = socket.socket()
##    client_socket_audio = socket.socket()
    client_socket_video.connect(('167.99.215.27', 2000))
##    client_socket_audio.connect(('188.166.17.65', 3000))

    # Make a file-like object out of the connection
    connection_video = client_socket_video.makefile('wb')
##    connection_audio = client_socket_audio.makefile('wb')
    start_stream_video = False
    start_stream_audio = False
    want_data = b'w'
    send_data = b's'

    current_time = time.perf_counter()

    try:
        stream_video = io.BytesIO()
        stream_audio = io.BytesIO()
        while True:        


            if not start_stream_video:

                # Possible addition of non-blocking arguments and select will be considered
                answer = client_socket_video.recv(128)

                if answer == want_data:
                    start_stream_video = True
                    client_socket_video.send(send_data)

            else:
                frame = frame_queue.get()
                _, encoded_frame = cv2.imencode('.jpg', frame)
                stream_video.write(encoded_frame.tobytes())
                # Write the length of the capture to the stream and flush to
                # ensure it actually gets sent
                connection_video.write(struct.pack('<L', stream_video.tell()))
                connection_video.flush()
                # Rewind the stream and send the image data over the wire
                stream_video.seek(0)
                connection_video.write(stream_video.read())
                # Reset the stream for the next capture
                stream_video.seek(0)
                stream_video.truncate()
                
            # Reading the values
            current_room_temperature = room_temp.value
            current_room_humidity = room_humid.value
            current_baby_temperature = baby_temp.value
            # with baby_is_crying.get_lock():
            #     crying_detected = baby_is_crying.value    
            
            print('giris')
            sys.stdout.flush()
            
            if(time.perf_counter() - current_time > 1):
                
                print('if')
                sys.stdout.flush()
                
                current_time = time.perf_counter()
            
                body = {'device_id': 26082007,
                        'room_temp': current_room_temperature,
                        'room_humd': current_room_humidity,
    #                    'baby_temp': current_baby_temperature}
                        'baby_temp': random.uniform(36,40)}

                myurl = "http://167.99.215.27:8000/api/data"
                req = urllib.request.Request(myurl)
                req.add_header('Content-Type', 'application/json')
                jsondata = json.dumps(body)
                jsondataasbytes = jsondata.encode('utf-8')
                req.add_header('Content-Length', len(jsondataasbytes))
                response = urllib.request.urlopen(req, jsondataasbytes)
                
                print('ifend')
                sys.stdout.flush()
                    
        
##            if not start_stream_audio:
##
##                
##                # Possible addition of non-blocking arguments and select will be considered
##                answer = client_socket_audio.recv(128)
##
##                if answer == want_data:
##                    start_stream_audio = True
##                    client_socket_audio.send(send_data)
##
##            else:
##                chunk = audio_queue.get()
##                stream_audio.write(chunk)
##                # Write the length of the capture to the stream and flush to
##                # ensure it actually gets sent
##                connection_audio.write(struct.pack('<L', stream_audio.tell()))
##                connection_audio.flush()
##                # Rewind the stream and send the image data over the wire
##                stream_audio.seek(0)
##                connection_audio.write(stream_audio.read())
##                # Reset the stream for the next capture
##                stream_audio.seek(0)
##                stream_audio.truncate()
##            
            

    finally:
##        connection_audio.close()
##        client_socket_audio.close()
        connection_video.close()
        client_socket_video.close()

