import os
from flask import Flask
from flask_login import LoginManager
from .config import Config
from app.routes.main import main_bp
from app.routes.find_user import app as find_bp
from app.routes.login import login_bp
from app.routes.logout import logout_bp
from app.routes.admin import admin_bp
from app.database import models 
from app.database.engine import db
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.middleware.proxy_fix import ProxyFix


login_manager = LoginManager()
login_manager.login_view = 'login.login'  # Исправляем имя endpoint'а

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))  # Загружаем пользователя по его ID

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) 
        # Доверяем одному прокси-слою (Render), чтобы Flask брал клиентский IP из X-Forwarded-For
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Инициализация Flask-Login
    login_manager.init_app(app)

    # Инициализируем CSRF-защитник
    csrf = CSRFProtect(app)
    
    # Настраиваем CSRF-защитник для работы с JSON-запросами
    @app.after_request
    def add_csrf_token(response):
        if 'text/html' in response.headers.get('Content-Type', ''):
            response.set_cookie('csrf_token', generate_csrf())
        return response
    
    # Инициализируем базу данных
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Регистрируем маршруты
    app.register_blueprint(main_bp)
    app.register_blueprint(find_bp)
    app.register_blueprint(login_bp)  # Регистрируем Blueprint для логина
    app.register_blueprint(logout_bp)  # Регистрируем Blueprint для выхода
    app.register_blueprint(admin_bp)
    return app
