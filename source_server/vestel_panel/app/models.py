from app import db,login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User(UserMixin,db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(254), unique=True, nullable=False, index=True)
	name = db.Column(db.String(20), nullable =False)
	surname = db.Column(db.String(20), unique = True, nullable=False)
	device_id = db.Column(db.String(64), db.ForeignKey('device.id'))
	password_hash = db.Column(db.String(128))
	notifications = db.relationship('Notification', backref='user', lazy='dynamic')

	def __repr__(self):
		return f"User(E-mail: '{self.email}', Device ID: '{self.device_id}', Name: '{self.name}' , Surname: '{self.surname}', Notifications: '{self.notifications}') \n"

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

class Device(db.Model):
	id = db.Column(db.String(64),primary_key=True)
	users = db.relationship('User', backref='user', lazy='dynamic')
	data_record = db.relationship('Data', backref='device', lazy='dynamic')
	update_period = db.Column(db.Integer)
	ir_led = db.Column(db.Integer)
	device_status = db.Column(db.Boolean)
	baby_status = db.Column(db.Integer, nullable=False)

	def __repr__(self):
		return f"Device(ID: '{self.id}', Users: {self.users}) \n"

class Data(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	room_temp = db.Column(db.Float(), nullable=False)
	room_humd = db.Column(db.Float(), nullable=False)
	baby_temp = db.Column(db.Float(), nullable=False)
	timestamp = db.Column(db.DateTime, index=True, nullable=False, default=datetime.utcnow)
	device_id = db.Column(db.String(64), db.ForeignKey('device.id'))

	def from_dict(self, data):
		for field in ['room_temp', 'baby_temp', 'room_humd', 'device_id']:
			if field in data:
				setattr(self, field, data[field])

	def __repr__(self):
		return f"Data('ID: {self.id}', Device ID: '{self.device_id}' , Room Temp: '{self.room_temp}' C , " \
			f" Room Humidity: '{self.room_humd}', Baby Temp:'{self.baby_temp}' ,  at '{self.timestamp}') \n"


class Notification(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	code = db.Column(db.Integer, nullable=False)
	timestamp = db.Column(db.DateTime, index = True, nullable=False, default=datetime.utcnow)
	is_opened = db.Column(db.Boolean, default=False)

	def from_dict(self, data):

		for field in ['user_id', 'code']:
			if field in data:
				setattr(self, field, data[field])

	def __repr__(self):
		return f"Notification(''ID: {self.id}', User: '{self.user_id}', Code: '{self.code}', at '{self.timestamp}' \n"

class Subscriber(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	created = db.Column(db.DateTime, index = True, nullable=False, default=datetime.utcnow)
	modified = db.Column(db.DateTime, index = True, nullable=False, default=datetime.utcnow)
	subscription_info = db.Column(db.String(2000))
	is_active = db.Column(db.Boolean(), default=True)
	device_id = db.Column(db.String(64), db.ForeignKey('device.id'), default='26082007')

	def set_subsinfo(self, info):

		setattr(self, 'subscription_info', info)

	def __repr__(self):
		return f"Subscriber(''ID: {self.id}', User: '{self.subscription_info}' \n"
