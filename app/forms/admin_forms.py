from flask_wtf import FlaskForm
from wtforms import SelectField, StringField
from wtforms.validators import DataRequired, URL

# Копируйте ключи normalize_district_name() из main.py
DISTRICT_CHOICES = [
            ('Хасавюртовский район', 'Хасавюртовский район'),
            ('Кизлярский район', 'Кизлярский район'),
            ('Бабаюртовский район', 'Бабаюртовский район')
]

class CommunityLinkForm(FlaskForm):
    district = SelectField('Район', validators=[DataRequired()], choices=DISTRICT_CHOICES)
    link     = StringField('Ссылка на сообщество', validators=[DataRequired(), URL()])
