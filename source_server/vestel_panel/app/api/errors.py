from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

def bad_request(message):
    print('errorita')
    return 'Bad request.'