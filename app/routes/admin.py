from flask import Blueprint, redirect, render_template, url_for, request, send_file, jsonify
from flask_login import login_required, current_user
import csv
import io
from datetime import datetime

from app.database.models import Participant, db

admin_bp = Blueprint('admin_panel', __name__)

@admin_bp.route('/admin', methods=['GET'])
@login_required  # Только авторизованные пользователи могут зайти на админ-панель
def admin_panel():
    if not current_user.is_admin:  # Проверка, является ли пользователь администратором
        return redirect(url_for('index.html'))  # Перенаправление на главную страницу, если не администратор
    
    # Получаем страницу из запроса или устанавливаем значение по умолчанию
    page = request.args.get('page', 1, type=int)
    
    # Используем новый синтаксис для пагинации в SQLAlchemy
    participants = Participant.query.paginate(page=page, per_page=10, error_out=False)
    
    # Вычисляем диапазон страниц для пагинации
    start_page = max(1, participants.page - 2)
    end_page = min(participants.pages, participants.page + 2)

    return render_template('admin_panel.html', participants=participants, 
                          start_page=start_page, end_page=end_page)

@admin_bp.route('/admin/delete/<int:participant_id>', methods=['POST'])
@login_required
def delete_participant(participant_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    participant = Participant.query.get_or_404(participant_id)
    try:
        db.session.delete(participant)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/download/male-csv', methods=['GET'])
@login_required
def download_male_csv():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    # Получаем всех мужчин из базы данных
    male_participants = Participant.query.filter_by(gender='male').all()
    
    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Записываем заголовки
    writer.writerow(['Имя', 'Телефон', 'Город'])
    
    # Записываем данные
    for participant in male_participants:
        writer.writerow([participant.full_name, participant.phone, participant.city])
    
    # Подготавливаем файл для отправки
    output.seek(0)
    
    # Генерируем имя файла с текущей датой
    filename = f"male_participants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@admin_bp.route('/admin/download/female-csv', methods=['GET'])
@login_required
def download_female_csv():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    # Получаем всех женщин из базы данных
    female_participants = Participant.query.filter_by(gender='female').all()
    
    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Записываем заголовки
    writer.writerow(['Имя', 'Телефон', 'Город'])
    
    # Записываем данные
    for participant in female_participants:
        writer.writerow([participant.full_name, participant.phone, participant.city])
    
    # Подготавливаем файл для отправки
    output.seek(0)
    
    # Генерируем имя файла с текущей датой
    filename = f"female_participants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )
