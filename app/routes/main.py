import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.forms.registration_form import RegistrationForm
from app.services.registration_service import process_registration, check_user_in_table
from app.database.engine import db
from app.database.models import CommunityLink  # Добавляем импорт
from sqlalchemy.exc import DatabaseError
import requests

main_bp = Blueprint('main', __name__)

# Строгий белый список разрешенных районов (только точные совпадения)
STRICT_ALLOWED_DISTRICTS = {
    'Хасавюрт + район': ['хасавюрт', 'хасавюртовский район'],
    'Кизляр + район': ['кизляр', 'кизлярский район'],
    'Бабаюртовский район': ['бабаюрт', 'бабаюртовский район']
}

# Нормализация названий районов
def normalize_district_name(location):
    if not location:
        return None
    
    location = location.lower().strip()
    for normalized_name, aliases in STRICT_ALLOWED_DISTRICTS.items():
        if location in aliases:
            return normalized_name
    return None

# Проверка что район точно разрешен
def is_location_allowed(location):
    return normalize_district_name(location) is not None

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm()
    is_registered = None
    community_link = None  # Добавляем переменную для ссылки
    
    try:
        if form.validate_on_submit():
            # 1. Проверка выбранного района в форме
            selected_district = form.district.data
            if not is_location_allowed(selected_district):
                flash("Регистрация доступна только для Хасавюрта, Кизляра и Бабаюрта!", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

            # 2. Обязательная проверка геолокации
            if not form.latitude.data or not form.longitude.data:
                flash("Не удалось определить ваше местоположение. Включите геолокацию!", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)
                
            address = get_full_address_by_coordinates(form.latitude.data, form.longitude.data)
            if not address:
                flash("Ошибка проверки адреса. Попробуйте позже.", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

            # 3. Извлекаем район из геоданных
            geo_district = extract_district_from_address(address)
            if not geo_district:
                flash("Не удалось определить ваш район. Попробуйте еще раз.", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

            # 4. Проверяем что район из геолокации разрешен
            if not is_location_allowed(geo_district):
                flash(f"Регистрация недоступна для вашего района ({geo_district})!", "error")
                logging.warning(f"Попытка регистрации из запрещенного района: {geo_district}")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

            # 5. Проверяем соответствие выбранного района и геолокации
            normalized_selected = normalize_district_name(selected_district)
            normalized_geo = normalize_district_name(geo_district)
            
            if normalized_selected != normalized_geo:
                flash("Выбранный район не соответствует вашему местоположению!", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

            # 6. Получаем ссылку на сообщество для района
            community_link_obj = CommunityLink.query.filter_by(district=normalized_selected).first()
            community_link = community_link_obj.link if community_link_obj else 'https://chat.whatsapp.com/default'

            # 7. Проверяем и сохраняем данные
            if check_user_in_table(form.phone.data):
                is_registered = '#alreadyRegisteredModal'
            else:
                process_registration(
                    form=form,
                    district=normalized_selected,
                    city=geo_district,
                    region="Дагестан",
                    country="Россия"
                )
                is_registered = '#registrationSuccessModal'
                
    except DatabaseError as e:
        logging.error(f"Ошибка базы данных: {e}")
        flash("Ошибка подключения к базе данных. Пожалуйста, попробуйте снова.", "error")
    except Exception as e:
        logging.error(f"Общая ошибка при обработке формы: {e}")
        flash("Ошибка сервера. Попробуйте позже.", "error")

    return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

def get_full_address_by_coordinates(latitude, longitude):
    url = f'https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json&addressdetails=1'
    headers = {'User-Agent': 'RaffleApp/1.0'}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('address')
        return None
    except Exception as e:
        logging.error(f"Ошибка запроса к Nominatim: {e}")
        return None

def extract_district_from_address(address):
    """Извлекаем район из адреса с приоритетом по полям"""
    if not address:
        return None
    
    # Порядок проверки полей
    fields_to_check = [
        'county',        # Район (Карабудахкентский район)
        'municipality',  # Муниципальное образование
        'village',       # Село
        'city'           # Город
    ]
    
    for field in fields_to_check:
        if field in address:
            district = address[field].lower()
            # Удаляем лишние слова для точного сравнения
            district = district.replace('район', '').strip()
            return district
            
    return None

def format_full_address(address):
    if not address:
        return None
    components = [address.get(field) for field in ['road', 'village', 'county', 'state', 'country']]
    return ', '.join([comp for comp in components if comp])