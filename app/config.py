import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', "postgresql://gen_user:%3BC%3C4ju%7B-XC_%7BN4@92.53.107.41:5432/default_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False