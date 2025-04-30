from flask import Blueprint,  render_template, request, flash, redirect, url_for
from app.forms.registration_form import RegistrationForm
from app.services.location_service import is_in_city, get_location_by_ip, get_city_by_ip
from app.services.registration_service import process_registration, check_user_in_table
from app.database.engine import db


main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm()

    if form.validate_on_submit():
        city, region, country = get_location_by_ip()
        if city is None or region is None or country is None:
            flash("Не удалось получить ваше местоположение. Пожалуйста, включите доступ к геолокации.", "error")
            return render_template('not_allowed.html')

        # Проверяем, что пользователь находится в нужном городе
        if not is_in_city(city=city):
            return render_template('not_allowed.html')

        if check_user_in_table(form.phone.data):
            flash("Этот номер телефона уже зарегистрирован. Пожалуйста, используйте другой номер.", "error")
            return render_template('index.html', form=form)  # Возвращаем на форму регистрации с ошибкой
       
        process_registration(form=form, city=city, region=region, country=country)
        flash('Регистрация прошла успешно!', 'success')  # Flash-сообщение
        return redirect("https://chat.whatsapp.com/EIa4wkifsVQDttzjOKlOY3")  # Замените на ссылку вашей группы

    return render_template('index.html', form=form)