import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', "postgresql+psycopg2://gen_user:%3BC%3C4ju%7B-XC_%7BN4@92.53.107.41:5432/default_db?sslmode=disable")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
    'connect_args': {
        'connect_timeout': 10  # Увеличьте тайм-аут до 10 секунд
    }
}