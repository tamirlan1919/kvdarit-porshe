import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.forms.registration_form import RegistrationForm
from app.services.registration_service import process_registration, check_user_in_table
from app.database.engine import db
from flask_login import login_required, current_user
from sqlalchemy.exc import DatabaseError
import requests

main_bp = Blueprint('main', __name__)

# Список разрешённых городов и районов
ALLOWED_CITIES = [
    # Основные города
    'махачкала', 'каспийск', 'грозный',
    
    # Районы Махачкалы
    'кировский район', 'ленинский район', 'советский район',
    
    # Посёлки городского типа Кировского района
    'ленинкент', 'семендер', 'сулак', 'шамхал',
    
    # Сёла Кировского района
    'богатырёвка', 'красноармейское', 'остров чечень', 'шамхал-термен',
    
    # Посёлки и сёла Ленинского района
    'новый кяхулай', 'новый хушет', 'талги',
    
    # Посёлки Советского района
    'альбурикент', 'кяхулай', 'тарки',
    
    # Микрорайоны и районы
    '5-й посёлок', '5 посёлок',
    
    # Дополнительные микрорайоны и кварталы
    'каменный карьер', 'афган-городок', 'кемпинг', 'кирпичный', 
    'ккоз', 'тау', 'центральный', 'южный', 'рекреационная зона', 'финский квартал',
    
    # Пригородные районы
    'турали'
]

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm()
    is_registered = None
    try:
        if form.validate_on_submit():
            latitude = form.latitude.data
            longitude = form.longitude.data
            logging.info(f"Получены координаты: latitude={latitude}, longitude={longitude}")

            if not latitude or not longitude:
                flash("Не удалось получить координаты. Разрешите доступ к геолокации.", "error")
                return render_template('index.html', form=form, is_registered=is_registered)

            address = get_full_address_by_coordinates(latitude, longitude)
            if address is None:
                flash("Не удалось определить местоположение. Попробуйте позже.", "error")
                return render_template('index.html', form=form, is_registered=is_registered)

            city, region, country = extract_location_info(address)
            full_address = format_full_address(address)
            logging.info(f"Местоположение: город={city}, регион={region}, страна={country}, полный адрес={full_address}")

            if not city:
                flash("Не удалось определить город. Попробуйте еще раз.", "error")
                return render_template('index.html', form=form, is_registered=is_registered)

            city_lower = city.lower().strip()
            if city_lower in ALLOWED_CITIES:
                if check_user_in_table(form.phone.data):
                    is_registered = '#alreadyRegisteredModal'
                    logging.info("Пользователь уже зарегистрирован, показываем модальное окно alreadyRegisteredModal")
                else:
                    process_registration(form=form, city=full_address, region=region, country=country)
                    is_registered = '#registrationSuccessModal'
                    logging.info("Регистрация успешна, показываем модальное окно registrationSuccessModal")
            else:
                flash("Регистрация возможна только в Махачкале, Каспийске или других разрешённых местах.", "error")
                return render_template('index.html', form=form, is_registered=is_registered)
    except DatabaseError as e:
        logging.error(f"Ошибка базы данных: {e}")
        flash("Ошибка подключения к базе данных. Пожалуйста, попробуйте снова.", "error")
        return redirect(url_for('main.index'))
    except Exception as e:
        logging.error(f"Общая ошибка при обработке формы: {e}")
        flash("Ошибка сервера. Попробуйте позже.", "error")
        return render_template('index.html', form=form, is_registered=is_registered)

    logging.info(f"Рендерим шаблон с is_registered={is_registered}")
    return render_template('index.html', form=form, is_registered=is_registered)

def get_full_address_by_coordinates(latitude, longitude):
    url = f'https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json&addressdetails=1'
    headers = {
        'User-Agent': 'RaffleApp/1.0 tchinchaev@bk.ru'
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if response.status_code == 200 and 'address' in data:
            return data['address']
        else:
            logging.error(f"Ошибка Nominatim: {data.get('error', 'Неизвестная ошибка')}")
            return None
    except Exception as e:
        logging.error(f"Ошибка запроса к Nominatim: {e}")
        return None

def format_full_address(address):
    if not address:
        return None

    components = [
        address.get('suburb'),  # Микрорайон
        address.get('city') or address.get('town') or address.get('village'),  # Город
        address.get('state_district'),  # Район
        address.get('state'),  # Регион
        address.get('country')  # Страна
    ]

    # Фильтруем None и пустые строки, объединяем компоненты
    full_address = ', '.join([comp for comp in components if comp])
    return full_address if full_address.strip() else None

def extract_location_info(address):
    if address is None:
        return None, None, None

    city = address.get('city') or address.get('town') or address.get('village') or None
    region = address.get('state') or address.get('region') or None
    country = address.get('country') or None

    return city, region, country