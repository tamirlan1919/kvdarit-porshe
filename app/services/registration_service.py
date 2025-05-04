from flask import request
from app.database.models import Participant
from app.database.engine import db
from datetime import datetime

def process_registration(form, city, region, country, district=None):
    try:
        user = Participant(
            full_name=form.full_name.data,
            phone=form.phone.data,
            age=form.age.data,
            gender=form.gender.data,
            registration_time=datetime.now(),
            ip_address=request.remote_addr,
            city=city,
            district=district,  # Добавляем сохранение района
            region=region,
            country=country
        )
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print(f"Error processing registration: {e}")
        db.session.rollback()
        raise

def check_user_in_table(phone):
    # Используем first() для получения первого совпадения
    user = Participant.query.filter(Participant.phone == phone).first()
    # Если пользователь найден, возвращаем True
    if user:
        return True
    return False