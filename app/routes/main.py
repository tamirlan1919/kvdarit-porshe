from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.forms.registration_form import RegistrationForm
from app.services.location_service import is_in_allowed_location, get_location_by_ip, get_formatted_location
from app.services.registration_service import process_registration, check_user_in_table
from app.database.engine import db
from flask_login import login_required, current_user
from app.database.models import Participant
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm()

    if form.validate_on_submit():
        # Получаем IP-адрес пользователя
        ip = request.remote_addr
        
        # Получаем данные о местоположении
        city, region, country = get_location_by_ip(ip)
        
        if not city:
            flash("Не удалось определить ваше местоположение. Пожалуйста, попробуйте позже.", "error")
            return render_template('index.html', form=form)

        # Проверяем, находится ли пользователь в разрешенном городе/районе
        if not is_in_allowed_location(city, region):
            return render_template('not_allowed.html')

        # Проверяем, не зарегистрирован ли уже пользователь
        if check_user_in_table(form.phone.data):
            flash("Этот номер телефона уже зарегистрирован. Пожалуйста, используйте другой номер.", "error")
            return render_template('index.html', form=form)

        # Форматируем местоположение для сохранения
        formatted_location = get_formatted_location(city, region)
        
        # Регистрируем пользователя
        process_registration(form=form, city=formatted_location, region=region, country=country)
        flash('Регистрация прошла успешно!', 'success')
        return redirect("https://chat.whatsapp.com/D5YlUS1y9MIKkIB3oq8Vh8")

    return render_template('index.html', form=form)
