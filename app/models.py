from app import app
from app import db
from datetime import datetime
from flask_login import UserMixin
from flask_bcrypt import Bcrypt


bcrypt = Bcrypt(app)

options = db.Table('options', 
db.Column('tracker_id', db.Integer, db.ForeignKey('Tracker.id'), primary_key = True),
db.Column('settings_name', db.Integer, db.ForeignKey('Settings.name'), primary_key = True))

class Tracker(db.Model):
    __tablename__ = 'Tracker'
    id = db.Column(db.Integer)
    name = db.Column(db.String(80), primary_key=True, nullable = False)
    description = db.Column(db.String)
    tracker_type = db.Column(db.String)
    settings = db.relationship('Settings', secondary = 'options', backref=db.backref('tracker', lazy=True))
    logs = db.relationship('Logs', backref='tracker', lazy=True, cascade="all, delete")
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), primary_key = True)
    # last_logged = db.Column(db.String)

    def __init__(self, name, description, tracker_type, user_id):
        self.name = name
        self.description = description
        self.tracker_type = tracker_type
        self.user_id = user_id
    
class Settings(db.Model):
    __tablename__ = 'Settings'
    name = db.Column(db.String, primary_key = True)

    def __init__(self, name):
        self.name = name

class Logs(db.Model):
    __tablename__ = 'Logs'
    id = db.Column(db.Integer, primary_key=True)
    tracker_id = db.Column(db.Integer, db.ForeignKey('Tracker.id'))
    note = db.Column(db.String)
    value = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.String(16), nullable=False)

    def __init__(self, note, value, tracker_id, timestamp):
        self.note = note
        self.value = value
        self.tracker_id = tracker_id
        if(timestamp != None):
            self.timestamp = timestamp
        else:
            timestamp = datetime.utcnow()
            self.timestamp = timestamp.strftime("%Y-%m-%dT%H:%M")

class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80))
    email = db.Column(db.String, unique = True)
    password = db.Column(db.String)
    trackers = db.relationship('Tracker', backref='user', lazy=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password)



