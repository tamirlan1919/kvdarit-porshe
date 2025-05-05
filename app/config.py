import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql+psycopg2://gen_user:!%3ENx3hDOOh%3D0h%5C@178.253.40.153:5432/default_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
