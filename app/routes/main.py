import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.forms.registration_form import RegistrationForm
from app.services.location_service import get_client_ip, is_in_allowed_location, get_location_by_ip, get_formatted_location
from app.services.registration_service import process_registration, check_user_in_table
from app.database.engine import db
from flask_login import login_required, current_user
from app.database.models import Participant
from datetime import datetime
import requests
from sqlalchemy.exc import DatabaseError

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm()
    is_registered = None  # Инициализируем переменную
    try:
        if form.validate_on_submit():
            latitude = form.latitude.data
            longitude = form.longitude.data
            print(f"Получены координаты: latitude={latitude}, longitude={longitude}")

            if not latitude or not longitude:
                flash("Не удалось получить координаты. Разрешите доступ к геолокации.", "error")
                return render_template('index.html', form=form, is_registered=is_registered)

            full_address = get_full_address_by_coordinates(latitude, longitude)
            if full_address is None:
                flash("Не удалось определить местоположение. Попробуйте позже.", "error")
                return render_template('index.html', form=form, is_registered=is_registered)

            city, region, country = extract_location_info(full_address)
            print(f"Местоположение: город={city}, регион={region}, страна={country}")

            if not city:
                flash("Не удалось определить город. Попробуйте еще раз.", "error")
                return render_template('index.html', form=form, is_registered=is_registered)

            city_lower = city.lower().strip()
            if city_lower in ["махачкала", "каспийск"]:
                if check_user_in_table(form.phone.data):
                    is_registered = '#alreadyRegisteredModal'
                    print("Пользователь уже зарегистрирован, показываем модальное окно alreadyRegisteredModal")
                else:
                    process_registration(form=form, city=city, region=region, country=country)
                    is_registered = '#registrationSuccessModal'
                    print("Регистрация успешна, показываем модальное окно registrationSuccessModal")
            else:
                flash("Регистрация возможна только в Махачкале или Каспийске.", "error")
                return render_template('index.html', form=form, is_registered=is_registered)
    except DatabaseError as e:
        logging.error(f"Ошибка базы данных: {e}")
        flash("Ошибка подключения к базе данных. Пожалуйста, попробуйте снова.", "error")
        return redirect(url_for('main.index'))  # Редирект на главную страницу
    except Exception as e:
        logging.error(f"Общая ошибка при обработке формы: {e}")
        flash("Ошибка сервера. Попробуйте позже.", "error")
        return render_template('index.html', form=form, is_registered=is_registered)

    print(f"Рендерим шаблон с is_registered={is_registered}")
    return render_template('index.html', form=form, is_registered=is_registered)

# Функция для получения полного адреса по координатам с использованием Nominatim
def get_full_address_by_coordinates(latitude, longitude):
    url = f'https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json&addressdetails=1'
    headers = {
        'User-Agent': 'RaffleApp/1.0 tchinchaev@bk.ru'  # Укажите ваш email для соблюдения правил Nominatim
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if response.status_code == 200 and 'address' in data:
            return data['address']
        else:
            print(f"Ошибка Nominatim: {data.get('error', 'Неизвестная ошибка')}")
            return None
    except Exception as e:
        print(f"Ошибка запроса к Nominatim: {e}")
        return None

# Функция для извлечения города, региона и страны из адреса Nominatim
def extract_location_info(address):
    if address is None:
        return None, None, None

    city = address.get('city') or address.get('town') or address.get('village') or None
    region = address.get('state') or address.get('region') or None
    country = address.get('country') or None

    return city, region, country
