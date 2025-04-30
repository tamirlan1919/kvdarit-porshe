from flask import redirect, url_for, Blueprint
from flask_login import logout_user

logout_bp = Blueprint('logout', __name__)

@logout_bp.route('/logout')
def logout():
    logout_user()  # Выход из системы
    return redirect(url_for('main.index'))  # Перенаправление на главную страницу
