from flask import request
from app.database.models import Participant
from app.database.engine import db
from datetime import datetime

def process_registration(form, city, region, country):
    try:
        # Получаем данные из формы
        name = form.full_name.data
        phone = form.phone.data
        age = form.age.data
        gender = form.gender.data

        # Создаем нового участника
        user = Participant(
            full_name=name,
            phone=phone,
            age=age,
            gender=gender,
            registration_time=datetime.now(),  # Устанавливаем текущую дату и время
            ip_address=request.remote_addr,  # Получаем IP-адрес пользователя
            city=city,
            region=region,
            country=country
        )

        # Сохраняем участника в базе данных
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        # Логирование ошибки
        print(f"Error processing registration: {e}")
        db.session.rollback()
        raise  # Пробрасываем исключение дальше

def check_user_in_table(phone):
    # Используем first() для получения первого совпадения
    user = Participant.query.filter(Participant.phone == phone).first()
    # Если пользователь найден, возвращаем True
    if user:
        return True
    return False