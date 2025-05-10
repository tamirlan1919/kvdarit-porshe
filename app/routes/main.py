import logging
import re
from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.forms.registration_form import RegistrationForm
from app.services.registration_service import process_registration, check_user_in_table
from app.database.engine import db
from app.database.models import CommunityLink
from sqlalchemy.exc import DatabaseError
import requests

main_bp = Blueprint('main', __name__)

# Ключи: нормализованные названия районов. Значения: ключевые слова для сопоставления.
ALLOWED_DISTRICTS = {
    'Хасавюртовский район': {
        'keywords': ['хасавюрт'],
        'localities': [
            "абдурашид", "аджимажагатюрт", "адильотар", "акбулатюрт", "аксай",
            "байрам", "байрамаул", "бамматюрт", "баташюрт", "батаюрт",
            "борагангечув", "генжеаул", "гоксув", "гребенской мост", "дзержинское",
            "кадыротар", "казмааул", "кандаураул", "карланюрт", "карланюрт",
            "кемсиюрт", "кокрек", "костек", "куруш", "лаклакюрт",
            "могилевское", "моксоб", "муцалаул", "новогагатли", "новосельское",
            "новососитли", "новый костек", "нурадилово", "октябрьское", "османюрт",
            "первомайское", "петраковское", "покровское", "пятилетка", "садовое",
            "симсир", "сиух", "советское", "солнечное", "сулевкент",
            "темираул", "теречное", "тотурбийкала", "тукита", "тутлар",
            "умаротар", "умашаул", "хамавюрт", "цияб ичичали", "чагаротар",
            "шагада", "шулькевич", "эндирей", 'хасавюрт', 'городской округ хасавюрт', 'хасавюртовский район',
            'хасавюртовский', 'сельское поселение cело аксай', 'сельское поселение Село Аксай'
        ]
    },
    'Кизлярский район': {
        'keywords': ['кизляр'],
        'localities': [
            "аверьяновка", "александрийская", "большая арешевка", "большебредихинское", "большезадоевское",
            "большекозыревское", "бондареновское", "брянск", "брянский рыбозавод", "бурумбай", "виноградное",
            "вперёд", "выше-таловка", "грузинское", "дагестанское", "дальнее", "ефимовка", "заречное", "заря коммуны", "кардоновка",
            "кенафный завод", "керликент", "коллективизатор", "косякино", "кохановское", "крайновка", "красное",
            "краснооктябрьское", "красный восход", "красный рыбак", "курдюковское", "лопуховка", "макаровское",
            "малая арешевка", "малая задоевка", "малое казыревское", "мангулаул", "мирное", "михеевское", "мулла-али",
            "некрасовка", "новая серебряковка", "нововладимирское", "новогладовка", "новое", "новокохановское", "новокрестьяновское",
            "новомонастырское", "новонадеждовка", "ново-теречное", "новый бахтемир", "новый бирюзяк", "новый чечень",
            "огузер", "октябрьское", "опытно-мелиоративная станция", "первокизлярское", "первомайское",
            "персидское", "пригородное", "пролетарское", "речное", "рыбалко", "сангиши", "сар-сар", "имени жданова",
            "имени калинина", "имени карла маркса", "имени кирова", "имени шаумяна", "серебряковка", "советское", "старо-теречное", "степное",
            "судоремонтная техническая станция", "суюткино", "тушиловка", "украинское", "хуцеевка",
            "цветковка", "черняевка", "школьное", "юбилейное", "южное", "ясная поляна", 'кизляр'
        ]
    },
    'Бабаюртовский район': {
        'keywords': ['бабаюрт'],
        'localities': [
            'адиль-янгиюрт', 'алимпашаюрт', 'бабаюрт', 'геметюбе', 'герменчик', 'львовский № 1',
            'люксембург', 'мужукай', 'новая коса', 'новокаре', 'оразгулаул', 'советское', 'тавлу-отар',
            'тамазатюбе', 'татаюрт', 'туршунай', 'уцмиюрт', 'хамаматюрт', 'хасанай', 'чанкаюрт',
            'шахбулатотар', 'янгылбай', 'Шава', 'Цумадинский', 'Цумадинский район', 'тамазатюбинский сельсовет', 'бабаюртовский район',
            'Кутан Бутуш', 'кутан бутуш', 'ибрагимотар', 'тляратинский', 'бабаюртовский', 'бюрукутан'
        ]
    }
}

def normalize_district_name(location):
    if not location:
        return None
    
    location = location.lower().strip()
    
    # Удаляем префиксы и суффиксы, связанные с административным делением
    location = re.sub(
        r'(городской округ|муниципальный район|район|муниципальное образование)\s*', 
        '', 
        location, 
        flags=re.IGNORECASE
    ).strip()
    
        # Ручное сопоставление для Цумадинского района
    if 'цумадинский' in location:
        return 'Бабаюртовский район'  # Сопоставляем с Бабаюртовским

    if 'тляратинский' in location:
        return 'Бабаюртовский район'
    # Проверяем ключевые слова для каждого района
    for district, data in ALLOWED_DISTRICTS.items():
        for keyword in data['keywords']:
            if keyword in location:
                return district
    return None

def is_location_allowed(location, district):
    normalized_district = normalize_district_name(district) if district else None
    
    # Проверяем, что район разрешен
    if not normalized_district:
        return False
    
    # Проверяем, что населенный пункт есть в списке для района
    return location.lower() in [loc.lower() for loc in ALLOWED_DISTRICTS[normalized_district]['localities']]

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm()
    is_registered = None
    community_link = None
    
    try:
        if form.validate_on_submit():
            if not form.latitude.data or not form.longitude.data:
                flash("Не удалось определить ваше местоположение. Включите геолокацию!", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)
                
            address = get_full_address_by_coordinates(form.latitude.data, form.longitude.data)
            if not address:
                flash("Ошибка проверки адреса. Попробуйте позже.", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

            # Извлекаем населенный пункт и район
            locality = extract_locality_from_address(address)
            district = address.get('county', '')
            
            if not locality or not is_location_allowed(locality, district):
                flash(f"Регистрация недоступна для вашего населённого пункта ({locality})!", "error")
                logging.warning(f"Попытка регистрации из запрещённого района: {district}, населённый пункт: {locality}")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

            # Получаем выбранный район из формы
            selected_district = form.district.data
            
            # Проверяем соответствие выбранного района и геолокации
            normalized_geo = normalize_district_name(district)
            if normalized_geo != selected_district:
                flash("Выбранный район не соответствует вашей геолокации!", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

            # Получаем ссылку на сообщество
            community_link_obj = CommunityLink.query.filter_by(district=selected_district).first()
            community_link = community_link_obj.link if community_link_obj else '#'
            
            # Сохраняем данные
            if check_user_in_table(form.phone.data):
                is_registered = '#alreadyRegisteredModal'
            else:
                process_registration(
                    form=form,
                    district=selected_district,
                    city=locality,
                    region=address.get('state', 'Дагестан'),
                    country=address.get('country', 'Россия')
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
    print(f"URL: {url}")
    headers = {'User-Agent': 'RaffleApp/1.0 tchinchaev@bk.ru'}
    try:
        response = requests.get(url, headers=headers)
        return response.json()['address'] if response.status_code == 200 else None
    except Exception as e:
        logging.error(f"Ошибка запроса к Nominatim: {e}")
        return None

def extract_locality_from_address(address):
    fields = ['village', 'town', 'city', 'suburb', 'municipality']
    for field in fields:
        if address.get(field):
            return address[field]
    return address.get('county', '')