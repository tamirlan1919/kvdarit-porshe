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
        'Район регистрации',
        choices=[
            ('Хасавюртовский район', 'Хасавюртовский район'),
            ('Кизлярский район', 'Кизлярский район'),
            ('Бабаюртовский район', 'Бабаюртовский район')
        ],
        validators=[DataRequired(message="Выберите район из списка")]
    )
    latitude = StringField('Latitude', default='', render_kw={'type': 'hidden'})
    longitude = StringField('Longitude', default='', render_kw={'type': 'hidden'})