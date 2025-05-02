from datetime import datetime

from flask_login import UserMixin
from .engine import db

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Автоинкремент
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    registration_time = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    city = db.Column(db.String(500), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Ticket {self.id} - {self.full_name}>'
    

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Устанавливаем флаг для админа