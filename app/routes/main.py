from flask import Blueprint,  render_template, request, flash, redirect, url_for
from app.forms.registration_form import RegistrationForm
from app.services.location_service import is_in_city, get_location_by_ip, get_city_by_ip, get_client_ip
from app.services.registration_service import process_registration, check_user_in_table
from app.database.engine import db
from flask_login import login_required, current_user
from app.database.models import Participant
from datetime import datetime
from geopy.geocoders import Nominatim
import json


main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm()

    if form.validate_on_submit():
        client_ip = get_client_ip()
        print(f"IP клиента: {client_ip}")
    
        # Вызываем функцию для получения данных о местоположении
        city, region, country = get_location_by_ip(client_ip)
        
        if not (city and region and country):
            return render_template('not_allowed.html')

        if not is_in_city(city=city):
            return render_template('not_allowed.html')

        if check_user_in_table(form.phone.data):
            flash("Этот номер телефона уже зарегистрирован. Пожалуйста, используйте другой номер.", "error")
            return render_template('index.html', form=form)

        process_registration(form=form, city=city, region=region, country=country)
        flash('Регистрация прошла успешно!', 'success')
        return redirect("https://chat.whatsapp.com/D5YlUS1y9MIKkIB3oq8Vh8")

    return render_template('index.html', form=form)