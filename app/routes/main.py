import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.forms.registration_form import RegistrationForm
from app.services.registration_service import process_registration, check_user_in_table
from app.database.engine import db
from sqlalchemy.exc import DatabaseError
import requests

main_bp = Blueprint('main', __name__)

# Обновленный словарь разрешенных локаций с учетом новых названий
ALLOWED_LOCATIONS = {
    'Хасавюрт + район': ['хасавюрт', 'хасавюртовский район', 'хасавюрт + район'],
    'Кизляр + район': ['кизляр', 'кизлярский район', 'кизляр + район'],
    'Бабаюртовский район': ['бабаюрт', 'бабаюртовский район']
}

# Словарь для преобразования выбранного значения в нормализованное название
DISTRICT_MAPPING = {
    'Хасавюрт + район': 'Хасавюрт + район',
    'Кизляр + район': 'Кизляр + район',
    'Бабаюртовский район': 'Бабаюртовский район'
}

def normalize_location_name(location):
    if not location:
        return None
        
    location = location.lower().strip()
    
    # Сначала проверяем точные совпадения с новыми названиями
    for normalized_name, aliases in ALLOWED_LOCATIONS.items():
        if location in [a.lower() for a in aliases]:
            return normalized_name
            
    # Затем проверяем частичные совпадения
    for normalized_name, aliases in ALLOWED_LOCATIONS.items():
        for alias in aliases:
            if alias in location:
                return normalized_name
                
    return None

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm()
    is_registered = None
    
    try:
        if form.validate_on_submit():
            # Получаем выбранное значение из формы
            selected_value = form.district.data
            
            # Преобразуем выбранное значение в нормализованное название
            selected_location = DISTRICT_MAPPING.get(selected_value, None)
            
            # Дополнительная нормализация (на случай ручного ввода)
            if not selected_location:
                selected_location = normalize_location_name(selected_value)
            
            if not selected_location:
                flash("Регистрация возможна только для жителей Хасавюрта, Кизляра или Бабаюртовского района.", "error")
                return render_template('index.html', form=form, is_registered=is_registered)
            
            # Устанавливаем значения по умолчанию
            city = selected_location.split('+')[0].strip() if '+' in selected_location else selected_location
            region = "Дагестан"
            country = "Россия"
            
            # Проверка геолокации (остается без изменений)
            latitude = form.latitude.data
            longitude = form.longitude.data
            
            if latitude and longitude:
                address = get_full_address_by_coordinates(latitude, longitude)
                if address:
                    geo_city, geo_district, geo_region, geo_country = extract_location_info(address)
                    geo_location = normalize_location_name(geo_district or geo_city)
                    
                    if geo_region:
                        region = geo_region
                    if geo_country:
                        country = geo_country
                    
                    if geo_location and geo_location != selected_location:
                        flash(f"Ваше местоположение ({geo_district or geo_city}) не соответствует выбранному району.", "error")
                        return render_template('index.html', form=form, is_registered=is_registered)
            
            # Проверяем и сохраняем данные
            if check_user_in_table(form.phone.data):
                is_registered = '#alreadyRegisteredModal'
            else:
                process_registration(
                    form=form,
                    district=selected_location,
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

# Остальные функции остаются без изменений
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
        return None, None, None, None

    district = (
        address.get('city_district') or 
        address.get('suburb') or
        address.get('district') or
        None
    )
    
    city = address.get('city') or address.get('town') or address.get('village') or None
    region = address.get('state') or address.get('region') or None
    country = address.get('country') or None

    return city, district, region, country

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