from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150))
    age = db.Column(db.String(10))
    gender = db.Column(db.String(10))
    contact = db.Column(db.String(15))

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sections = db.Column(db.Text, nullable=False)  # stores JSON serialized section data
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
