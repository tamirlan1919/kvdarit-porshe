# app/forms/registration_form.py

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, IntegerField, RadioField
from wtforms.validators import DataRequired, Length, Regexp, NumberRange

class RegistrationForm(FlaskForm):
    # Убедитесь, что поле full_name правильно определено
    full_name = StringField('Фамилия и Имя', validators=[DataRequired(), Length(min=2)])
    phone = StringField('Номер телефона', 
                        validators=[DataRequired()])
    age = IntegerField('Возраст', validators=[DataRequired(), NumberRange(min=16, max=100)])
    gender = RadioField('Пол', choices=[('male', 'Мужской'), ('female', 'Женский')], validators=[DataRequired()])
    district = SelectField(
        'Район проживания:', 
        choices=[
            ('', 'Выберите район'),
            ('Хасавюрт + район', 'Хасавюрт + район'),  # Значение для сохранения в БД: "Хасавюрт + район"
            ('Кизляр + район', 'Кизляр + район'),      # Значение для сохранения в БД: "Кизляр + район"
            ('Бабаюртовский район', 'Бабаюртовский район')  # Без изменений
        ],
        validators=[DataRequired(message="Выберите район")]
    )
    latitude = StringField('Latitude', default='', render_kw={'type': 'hidden'})
    longitude = StringField('Longitude', default='', render_kw={'type': 'hidden'})