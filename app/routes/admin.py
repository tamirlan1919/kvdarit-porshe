from flask import Blueprint, redirect, render_template, url_for, request, send_file, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
import csv
import io
from datetime import datetime
from sqlalchemy import func

from app.database.models import Participant, db

admin_bp = Blueprint('admin_panel', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin', methods=['GET'])
@login_required
@admin_required
def admin_panel():
    # Получаем параметры фильтрации
    page = request.args.get('page', 1, type=int)
    district_filter = request.args.get('district', None)
    gender_filter = request.args.get('gender', None)
    
    # Базовый запрос
    query = Participant.query
    
    # Применяем фильтры
    if district_filter:
        query = query.filter(Participant.district == district_filter)
    if gender_filter:
        query = query.filter(Participant.gender == gender_filter)
    
    # Пагинация
    participants = query.paginate(page=page, per_page=10, error_out=False)
    
    # Получаем список всех районов для фильтра
    districts = [d[0] for d in db.session.query(Participant.district).distinct().all() if d[0] is not None]
    
    # Статистика по полу
    counts = dict(db.session.query(
        Participant.gender,
        func.count(Participant.id))
        .group_by(Participant.gender)
        .all())
    counts = {
        'male': counts.get('male', 0),
        'female': counts.get('female', 0)
    }
    
    # Статистика по районам
    district_counts = {d: c for d, c in db.session.query(
        Participant.district,
        func.count(Participant.id))
        .group_by(Participant.district)
        .all() if d is not None}

    start_page = max(1, participants.page - 2)
    end_page = min(participants.pages, participants.page + 2)

    return render_template('admin_panel.html', 
                         participants=participants,
                         districts=districts,
                         current_district=district_filter,
                         current_gender=gender_filter,
                         counts=counts,
                         district_counts=district_counts,
                         start_page=start_page, 
                         end_page=end_page)

@admin_bp.route('/admin/download/csv', methods=['GET'])
@login_required
@admin_required
def download_csv():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    # Получаем параметры фильтрации
    district_filter = request.args.get('district')
    gender_filter = request.args.get('gender')
    
    # Создаем запрос с фильтрами
    query = Participant.query
    if district_filter:
        query = query.filter(Participant.district == district_filter)
    if gender_filter:
        query = query.filter(Participant.gender == gender_filter)
    
    participants = query.all()
    
    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)
    # Только два столбца в заголовке
    writer.writerow(['Телефон', 'Имя и адрес'])
    
    for p in participants:
        # Формируем строку с именем и адресом
        name_and_address = f"{p.full_name}, {p.city}, {p.district if p.district else ''}"
        # Убираем лишние запятые и пробелы
        name_and_address = ', '.join(filter(None, [part.strip() for part in name_and_address.split(',')]))
        
        writer.writerow([
            p.phone,  # Номер телефона
            name_and_address  # Имя и адрес в одной колонке
        ])
    
    output.seek(0)
    filename = f"participants_{district_filter or 'all'}_{gender_filter or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )