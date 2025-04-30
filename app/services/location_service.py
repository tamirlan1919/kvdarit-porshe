# /app/services/location_service.py
import requests
from geopy.distance import geodesic
from flask import request

# Координаты Махачкалы и Каспийска
# mahachkala_coords = (42.9850, 47.5039)  # Махачкала
# kaspiysk_coords = (42.8675, 47.7185)   # Каспийск
IPINFO_TOKEN = 'b27ebec3857a9b'
mahachkala_coords = (43.312, 45.6889)  # Махачкала
kaspiysk_coords = (42.8675, 47.7185)   # Каспийск

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

def get_client_ip():
    # Проверяем, если IP-адрес передан через прокси (например, балансировщик нагрузки)
    forwarded_ip = request.headers.get('X-Forwarded-For')
    if forwarded_ip:
        # X-Forwarded-For может содержать несколько адресов, первый из которых реальный
        return forwarded_ip.split(',')[0]
    return request.remote_addr

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
    print(f'Your IP - {ip}')
    
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
    


