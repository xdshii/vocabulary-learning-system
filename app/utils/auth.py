from functools import wraps
from flask import request, jsonify, current_app
from app.models.user import User
import jwt

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'code': 401, 'message': '请先登录'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            # 验证token
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['sub']
            user = User.query.get(user_id)
            if not user:
                return jsonify({'code': 401, 'message': '请先登录'}), 401
            return f(*args, **kwargs)
        except:
            return jsonify({'code': 401, 'message': '请先登录'}), 401
            
    return decorated 