# /app/services/location_service.py
import requests
from geopy.distance import geodesic

# Координаты Махачкалы и Каспийска
# mahachkala_coords = (42.9850, 47.5039)  # Махачкала
# kaspiysk_coords = (42.8675, 47.7185)   # Каспийск

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

def is_in_city(city):
    if city in ['Makhachkala', 'Kaspiysk', 'Grozny']:
        return True
    return False


def get_location_by_ip():
    try:
        # Отправляем запрос к ipinfo.io API для получения данных о местоположении
        ip_info_url = "http://ipinfo.io/json"
        response = requests.get(ip_info_url)
        data = response.json()
        
        # Извлекаем город, регион и страну
        city, region, country = data.get('city'), data.get('region'), data.get('country')
        
        # Возвращаем координаты и местоположение
        return city, region, country
    except Exception as e:
        print(f"Error fetching location by IP: {e}")
        return None, None, None
    
def get_city_by_ip():
    try:
        # Отправляем запрос к ipinfo.io API для получения данных о местоположении
        ip_info_url = "http://ipinfo.io/json"
        response = requests.get(ip_info_url)
        data = response.json()
        
        # Извлекаем город, регион и страну
        city = data.get('city')
        
        # Возвращаем координаты и местоположение
        return city
    except Exception as e:
        print(f"Error fetching location by IP: {e}")
        return None, None, None
    


