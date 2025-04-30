from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user
from werkzeug.security import check_password_hash
from app.database.models import User
from flask_wtf import FlaskForm

login_bp = Blueprint('login', __name__)

class LoginForm(FlaskForm):
    pass

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        print(user)
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Вход успешен!', 'success')
            return redirect(url_for('admin_panel.admin_panel'))  # Перенаправление в админ-панель
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('login.html', form=form)
