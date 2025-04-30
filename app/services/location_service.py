# /app/services/location_service.py
import requests
from geopy.distance import geodesic
from flask import request
from geopy.geocoders import Nominatim
import json

# Координаты Махачкалы и Каспийска
# mahachkala_coords = (42.9850, 47.5039)  # Махачкала
# kaspiysk_coords = (42.8675, 47.7185)   # Каспийск
IPINFO_TOKEN = 'b27ebec3857a9b'
mahachkala_coords = (43.312, 45.6889)  # Махачкала
kaspiysk_coords = (42.8675, 47.7185)   # Каспийск

# Список разрешенных городов и районов
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
    'турали',

    # Районы Грозного
    'заводской район', 'ленинский район', 'октябрьский район', 'старопромысловский район',
    
    # Посёлки и микрорайоны Грозного
    'алды', 'беркат-юрт', 'гикало', 'грозненский', 'катаяма', 'кермен-юрт', 'майртуп',
    'новые алды', 'победилово', 'пригородное', 'пролетарское', 'рудня', 'старая сунжа',
    'терское', 'черноречье', 'юбилейное',
    
    # Микрорайоны Грозного
    'восточный', 'западный', 'северный', 'южный', 'центральный',
    'авиагородок', 'беркат', 'грозненское море', 'заводской', 'ипподром',
    'катаяма', 'кермен', 'кировка', 'майртуп', 'новые алды', 'победилово',
    'пригородное', 'пролетарское', 'рудня', 'старая сунжа', 'терское',
    'черноречье', 'юбилейное'
]

def normalize_location_name(name: str) -> str:
    """
    Нормализует название местоположения для сравнения.
    """
    if not name:
        return ""
    return name.lower().strip()

def is_in_allowed_location(city: str, district: str = None) -> bool:
    """
    Проверяет, находится ли пользователь в разрешенном городе или районе.
    """
    if not city:
        return False
        
    normalized_city = normalize_location_name(city)
    normalized_district = normalize_location_name(district) if district else ""
    
    # Проверяем основной город
    if normalized_city in ['махачкала', 'каспийск', 'грозный']:
        return True
        
    # Проверяем районы и микрорайоны
    full_location = f"{normalized_city} {normalized_district}".strip()
    return any(allowed in full_location for allowed in ALLOWED_CITIES)

def get_location_by_ip(ip: str):
    """
    Возвращает (city, region, country) по запросу к ipinfo.io/<ip>/json.
    Если ipinfo.io недоступен, использует альтернативный сервис.
    """
    print(f'Your IP - {ip}')
    
    # Пробуем сначала ipinfo.io
    try:
        url = f"https://ipinfo.io/{ip}/json?token={IPINFO_TOKEN}"    
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        
        city = data.get("city")
        region = data.get("region")
        country = data.get("country")
        return city, region, country
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("Превышен лимит запросов к ipinfo.io, пробуем альтернативный сервис")
            # Пробуем альтернативный сервис
            try:
                url = f"http://ip-api.com/json/{ip}"
                resp = requests.get(url)
                resp.raise_for_status()
                data = resp.json()
                
                city = data.get("city")
                region = data.get("regionName")
                country = data.get("country")
                return city, region, country
            except Exception as e:
                print(f"Ошибка при запросе к ip-api.com: {e}")
                return None, None, None
        else:
            print(f"Ошибка при запросе к ipinfo.io: {e}")
            return None, None, None
    except Exception as e:
        print(f"Неожиданная ошибка при получении геолокации: {e}")
        return None, None, None

def get_formatted_location(city: str, district: str = None) -> str:
    """
    Форматирует местоположение в нужный формат для сохранения.
    """
    if not city:
        return ""
        
    if city.lower() == 'махачкала' and district:
        return f"Махачкала/{district}"
    elif city.lower() == 'каспийск' and district:
        return f"Каспийск/{district}"
    elif city.lower() == 'грозный' and district:
        return f"Грозный/{district}"
    else:
        return city

def get_city_by_ip(ip: str) -> str:
    """
    Возвращает город по IP-адресу.
    """
    city, _, _ = get_location_by_ip(ip)
    return city

# def is_in_city(user_coords):
#     """
#     Проверяет, находится ли человек в пределах 20 км от Махачкалы или Каспийска.
#     :param user_coords: tuple (latitude, longitude)
#     :return: True, если в пределах 20 км от Махачкалы или Каспийска, иначе False
#     """
#     distance_to_mahachkala = geodesic(user_coords, mahachkala_coords).km
#     distance_to_kaspiysk = geodesic(user_coords, kaspiysk_coords).km
#     print(distance_to_kaspiysk, distance_to_kaspiysk)

#     # Допустим, радиус 20 км для проверки
#     if distance_to_mahachkala <= 20 or distance_to_kaspiysk <= 20:
#         return True
#     return False



def is_in_city(city):
    """
    Проверяет, находится ли пользователь в одном из разрешенных городов.
    Проверяет как английские, так и русские названия городов.
    """
    allowed_cities = [
        'Makhachkala', 'Махачкала',
        'Kaspiysk', 'Каспийск',
        'Grozny', 'Грозный'
    ]
    
    if city in allowed_cities:
        return True
    return False

def get_location_by_ip(ip: str):
    """
    Возвращает (city, region, country) по запросу к ipinfo.io/<ip>/json.
    """
    
    url = f"https://ipinfo.io/{ip}/json"    
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        
        city = data.get("city")
        region = data.get("region")
        country = data.get("country")
        return city, region, country
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к ipinfo.io: {e}")
        return None, None, None
    except Exception as e:
        print(f"Неожиданная ошибка при получении геолокации: {e}")
        return None, None, None
    

def get_city_by_ip():
    """
    Получает город по IP-адресу пользователя.
    Использует несколько методов для определения IP и местоположения.
    """
    try:
        # Получаем IP-адрес
        ip = get_client_ip()
        if not ip:
            print("Не удалось получить IP-адрес")
            return None

        # Получаем данные о местоположении
        city, _, _ = get_location_by_ip(ip)
        if city:
            print(f"Успешно определен город: {city}")
            return city
        
        # Если не удалось получить данные через ipinfo.io, пробуем альтернативный метод
        try:
            response = requests.get('http://ip-api.com/json/', timeout=5)
            data = response.json()
            city = data.get('city')
            print(f"Город определен через ip-api.com: {city}")
            return city
        except Exception as e:
            print(f"Ошибка при использовании ip-api.com: {e}")
            return None

    except Exception as e:
        print(f"Общая ошибка при определении города: {e}")
        return None
    


