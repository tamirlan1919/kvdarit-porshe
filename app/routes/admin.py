from flask import Blueprint, redirect, render_template, url_for, request, send_file, jsonify, flash
from flask_login import login_required, current_user
from functools import wraps
import csv
import io
from datetime import datetime
from sqlalchemy import func
from app.database.models import Participant, CommunityLink, db
from app.forms.admin_forms import CommunityLinkForm  # Импортируем форму
from app.database.models import Participant, CommunityLink, db
from app.forms.admin_forms import CommunityLinkForm


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
    page = request.args.get('page', 1, type=int)
    district_filter = request.args.get('district', None)
    gender_filter = request.args.get('gender', None)
    
    query = Participant.query
    if district_filter:
        query = query.filter(Participant.district == district_filter)
    if gender_filter:
        query = query.filter(Participant.gender == gender_filter)
    
    participants = query.paginate(page=page, per_page=10, error_out=False)
    districts = [d[0] for d in db.session.query(Participant.district).distinct().all() if d[0] is not None]
    counts = dict(db.session.query(
        Participant.gender,
        func.count(Participant.id))
        .group_by(Participant.gender)
        .all())
    counts = {
        'male': counts.get('male', 0),
        'female': counts.get('female', 0)
    }
    district_counts = {d: c for d, c in db.session.query(
        Participant.district,
        func.count(Participant.id))
        .group_by(Participant.district)
        .all() if d is not None}
    
    community_links = CommunityLink.query.all()

    start_page = max(1, participants.page - 2)
    end_page = min(participants.pages, participants.page + 2)

    return render_template('admin_panel.html', 
                         participants=participants,
                         districts=districts,
                         current_district=district_filter,
                         current_gender=gender_filter,
                         counts=counts,
                         district_counts=district_counts,
                         community_links=community_links,
                         start_page=start_page, 
                         end_page=end_page)

@admin_bp.route('/admin/community_links/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_community_link():
    form = CommunityLinkForm()
    if form.validate_on_submit():  # Проверка формы
        district = form.district.data
        link = form.link.data
        # Проверяем, существует ли уже ссылка для района
        if CommunityLink.query.filter_by(district=district).first():
            flash(f'Ссылка для района "{district}" уже существует!', 'error')
        else:
            new_link = CommunityLink(district=district, link=link)
            db.session.add(new_link)
            db.session.commit()
            flash('Ссылка успешно добавлена!', 'success')
        return redirect(url_for('admin_panel.admin_panel'))
    return render_template('add_community_link.html', form=form)

@admin_bp.route('/admin/community_links/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_community_link(id):
    link = CommunityLink.query.get_or_404(id)
    form = CommunityLinkForm(obj=link)
    if form.validate_on_submit():
        # проверка на дубликат уже есть
        link.district = form.district.data
        link.link     = form.link.data
        db.session.commit()
        flash('Ссылка успешно обновлена!', 'success')
        return redirect(url_for('admin_panel.admin_panel'))
    return render_template('edit_community_link.html', form=form, link=link)

@admin_bp.route('/admin/community_links/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_community_link(id):
    link = CommunityLink.query.get_or_404(id)
    db.session.delete(link)
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/admin/download/csv', methods=['GET'])
@login_required
@admin_required
def download_csv():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    district_filter = request.args.get('district')
    gender_filter = request.args.get('gender')
    
    query = Participant.query
    if district_filter:
        query = query.filter(Participant.district == district_filter)
    if gender_filter:
        query = query.filter(Participant.gender == gender_filter)
    
    participants = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Телефон', 'Имя и адрес'])
    
    for p in participants:
        name_and_address = f"{p.full_name}, {p.city}, {p.district if p.district else ''}"
        name_and_address = ', '.join(filter(None, [part.strip() for part in name_and_address.split(',')]))
        writer.writerow([p.phone, name_and_address])
    
    output.seek(0)
    filename = f"participants_{district_filter or 'all'}_{gender_filter or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@admin_bp.route('/admin/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_participant(id):
    participant = Participant.query.get_or_404(id)
    db.session.delete(participant)
    db.session.commit()
    return jsonify({'success': True})