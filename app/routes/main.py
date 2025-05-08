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
ALLOWED_DISTRICTS = {
    'Хасавюрт + район': [
        "абдурашид", "аджимажагатюрт", "адильотар", "акбулатюрт", "аксай",
        "байрам", "байрамаул", "бамматюрт", "баташюрт", "батаюрт",
        "борагангечув", "генжеаул", "гоксув", "гребенской мост", "дзержинское",
        "кадыротар", "казмааул", "кандаураул", "карланюрт", "карланюрт",
        "кемсиюрт", "кокрек", "костек", "куруш", "лаклакюрт",
        "могилёвское", "моксоб", "муцалаул", "новогагатли", "новосельское",
        "новососитли", "новый костек", "нурадилово", "октябрьское", "османюрт",
        "первомайское", "петраковское", "покровское", "пятилетка", "садовое",
        "симсир", "сиух", "советское", "солнечное", "сулевкент",
        "темираул", "теречное", "тотурбийкала", "тукита", "тутлар",
        "умаротар", "умашаул", "хамавюрт", "цияб ичичали", "чагаротар",
        "шагада", "шулькевич", "эндирей"
    ],
    'Кизляр + район': [
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
        "цветковка", "черняевка", "школьное", "юбилейное", "южное", "ясная поляна"
    ],
    'Бабаюртовский район': [
        'адиль-янгиюрт', 'алимпашаюрт', 'бабаюрт', 'геметюбе', 'герменчик', 'львовский № 1',
        'люксембург', 'мужукай', 'новая коса', 'новокаре', 'оразгулаул', 'советское', 'тавлу-отар',
        'тамазатюбе', 'татаюрт', 'туршунай', 'уцмиюрт', 'хамаматюрт', 'хасанай', 'чанкаюрт',
        'шахбулатотар', 'янгылбай'
    ]
}



# Нормализация названий районов
def normalize_district_name(location):
    if not location:
        return None
    
    location = location.lower().strip()
    for normalized_name, aliases in ALLOWED_DISTRICTS.items():
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
            # 2. Обязательная проверка геолокации
            if not form.latitude.data or not form.longitude.data:
                flash("Не удалось определить ваше местоположение. Включите геолокацию!", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)
                
            address = get_full_address_by_coordinates(form.latitude.data, form.longitude.data)
            if not address:
                flash("Ошибка проверки адреса. Попробуйте позже.", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

            # 3. Извлекаем район из геоданных
            geo_locality = extract_locality_from_address(address)
            if not geo_locality:
                flash("Не удалось определить ваш район. Попробуйте еще раз.", "error")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

      
            if not is_location_allowed(geo_locality):
                flash(f"Регистрация недоступна для вашего населённого пункта ({geo_locality})!", "error")
                logging.warning(f"Попытка регистрации из запрещённого населённого пункта: {geo_locality}")
                return render_template('index.html', form=form, is_registered=is_registered, community_link=community_link)

            normalized_geo = normalize_district_name(geo_locality)
            print(f"normalized_geo: {normalized_geo}")

           

            # 6. Получаем ссылку на сообщество для района
            community_link_obj = CommunityLink.query.filter_by(district=selected_district).first()
            community_link = community_link_obj.link if community_link_obj else 'https://chat.whatsapp.com/default'

            # 7. Проверяем и сохраняем данные
            if check_user_in_table(form.phone.data):
                is_registered = '#alreadyRegisteredModal'
            else:
                process_registration(
                    form=form,
                    district=selected_district,
                    city=geo_locality,
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
    print(url)
    headers = {'User-Agent': 'RaffleApp/1.0 tchinchaev@bk.ru'}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if response.status_code == 200 and 'address' in data:
            return data['address']
        return None
    except Exception as e:
        logging.error(f"Ошибка запроса к Nominatim: {e}")
        return None

def extract_locality_from_address(address):
    """Извлекает населённый пункт из ответа Nominatim"""
    if not address:
        return None
    
    fields_to_check = [
        'village', 'town', 'city', 'suburb', 'municipality', 'county'
    ]
    
    for field in fields_to_check:
        val = address.get(field)
        if val:
            return val.strip().lower()
    
    return None



def format_full_address(address):
    if not address:
        return None
    components = [address.get(field) for field in ['road', 'village', 'county', 'state', 'country']]
    return ', '.join([comp for comp in components if comp])