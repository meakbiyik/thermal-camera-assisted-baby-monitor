## -*- coding: utf-8 -*-
"""
Created on Sun Feb 10 16:44:07 2019

@author: ASUS PC
"""




class Camera(object):


    def __init__(self):
        self.want_image = b'w'
        self.send_image = b's'
        self.got_image = b'gi'
        self.img_not_received = b'ni'


    def get_frame(self, connection, time):

        import struct
        import io

        start = time.time()


        # Read the length of the image as a 32-bit unsigned int.
        
        image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        # print(image_len)
        if  image_len:
            # Construct a stream to hold the image data and read the image
            # data from the connection
            image_stream = io.BytesIO()
            # print('here0')
            image_stream.write(connection.read(image_len))
            # print('here1')
            image_stream.seek(0)
            # print('here2')
            data_f = image_stream.getvalue()
            finish = time.time()
            elapsed_time = finish - start
            # print('Time_elapsed: ' + str(elapsed_time))


        else :
            data_f = None


        return data_f





