import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.forms.registration_form import RegistrationForm
from app.services.registration_service import process_registration, check_user_in_table
from app.database.engine import db
from sqlalchemy.exc import DatabaseError
import requests

main_bp = Blueprint('main', __name__)

# Список разрешённых районов (в нижнем регистре)
ALLOWED_DISTRICTS = [
    'хасаюртовский район',
    'кизлярский район',
    'бабаюртовский район',
    'ахматовский район'
]

# Алиасы для нормализации названий районов
DISTRICT_ALIASES = {
    'хасаюрт': 'хасаюртовский район',
    'кизляр': 'кизлярский район',
    'бабаюрт': 'бабаюртовский район',
    'грозный': 'ахматовский район'
}

def normalize_district_name(district):
    if not district:
        return None
        
    district = district.lower().strip()
    for alias, normalized in DISTRICT_ALIASES.items():
        if alias in district:
            return normalized
    return district

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm()
    is_registered = None
    
    try:
        if form.validate_on_submit():
            # Получаем и нормализуем выбранный район
            selected_district = normalize_district_name(form.district.data)
            
            if not selected_district or selected_district not in ALLOWED_DISTRICTS:
                flash("Регистрация возможна только для жителей Хасаюртовского, Кизлярского или Бабаюртовского районов.", "error")
                return render_template('index.html', form=form, is_registered=is_registered)
            
            # Устанавливаем значения по умолчанию
            city = selected_district  # Используем район как город по умолчанию
            region = "Дагестан"  # Регион по умолчанию
            country = "Россия"  # Страна по умолчанию
            
            # Проверяем геолокацию
            latitude = form.latitude.data
            longitude = form.longitude.data
            
            if latitude and longitude:
                address = get_full_address_by_coordinates(latitude, longitude)
                if address:
                    city, district, region_from_geo, country_from_geo = extract_location_info(address)
                    actual_district = normalize_district_name(district)
                    
                    # Если получили регион и страну из геолокации - используем их
                    if region_from_geo:
                        region = region_from_geo
                    if country_from_geo:
                        country = country_from_geo
                    
                    if actual_district and actual_district != selected_district:
                        flash(f"Ваше местоположение ({district}) не соответствует выбранному району.", "error")
                        return render_template('index.html', form=form, is_registered=is_registered)
            
            # Проверяем регистрацию и сохраняем данные
            if check_user_in_table(form.phone.data):
                is_registered = '#alreadyRegisteredModal'
            else:
                process_registration(
                    form=form,
                    district=selected_district,
                    city=city,
                    region=region,
                    country=country
                )
                is_registered = '#registrationSuccessModal'
                
    except DatabaseError as e:
        logging.error(f"Ошибка базы данных: {e}")
        flash("Ошибка подключения к базе данных. Пожалуйста, попробуйте снова.", "error")
    except Exception as e:
        logging.error(f"Общая ошибка при обработке формы: {e}")
        flash("Ошибка сервера. Попробуйте позже.", "error")

    return render_template('index.html', form=form, is_registered=is_registered)

def get_full_address_by_coordinates(latitude, longitude):
    url = f'https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json&addressdetails=1'
    headers = {'User-Agent': 'RaffleApp/1.0'}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        return data.get('address') if response.status_code == 200 else None
    except Exception as e:
        logging.error(f"Ошибка запроса к Nominatim: {e}")
        return None

def extract_location_info(address):
    if not address:
        return None, None, None, None  # Теперь возвращаем 4 значения

    district = (
        address.get('city_district') or 
        address.get('suburb') or
        address.get('district') or
        None
    )
    
    city = address.get('city') or address.get('town') or address.get('village') or None
    region = address.get('state') or address.get('region') or None  # Добавляем извлечение региона
    country = address.get('country') or None

    return city, district, region, country  # Возвращаем region

def format_full_address(address):
    if not address:
        return None

    components = [
        address.get('road'),
        address.get('city_district'),
        address.get('city'),
        address.get('state'),
        address.get('country')
    ]
    return ', '.join([comp for comp in components if comp])