from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import User

#class setUserSettings(FlaskForm):


#class SetDeviceSettings(FlaskForm):