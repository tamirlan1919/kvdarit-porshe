from flask import Blueprint, request, jsonify
from app.database.models import Participant
from flask_wtf.csrf import generate_csrf

app = Blueprint('find_user', __name__)

@app.route('/find_user', methods=['POST'])
def find_user():
    # Получаем данные из запроса
    data = request.get_json()
    
    # Проверяем, что данные получены
    if not data:
        return jsonify({
            'success': False,
            'message': 'Неверный формат данных'
        }), 400
        
    phone = data.get('phone')
    
    # Проверяем, что телефон указан
    if not phone:
        return jsonify({
            'success': False,
            'message': 'Номер телефона не указан'
        }), 400

    # Ищем пользователя по номеру телефона
    user = Participant.query.filter(Participant.phone == phone).first()

    if user:
        return jsonify({
            'success': True,
            'participant_id': user.id
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Пользователь с таким номером не найден!'
        })