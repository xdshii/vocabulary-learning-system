from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity,
    get_jwt
)
from app.models.user import User
from app import db
from app.services.wechat_service import WeChatService
import random
import string
import re
import redis
from datetime import datetime, timedelta
from functools import wraps
from . import auth_bp

def token_required(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            current_user = db.session.get(User, current_user_id)
            if not current_user:
                return jsonify({
                    'code': 401002,
                    'message': '用户不存在'
                }), 401
            return f(current_user=current_user, *args, **kwargs)
        except Exception as e:
            return jsonify({
                'code': 401001,
                'message': '无效的令牌'
            }), 401
    return decorated

def get_redis_client():
    """获取 Redis 客户端"""
    if not hasattr(current_app, 'redis_client'):
        current_app.redis_client = redis.from_url(current_app.config['REDIS_URL'])
    return current_app.redis_client

@auth_bp.route('/send-code', methods=['POST'])
def send_verification_code():
    """发送验证码"""
    data = request.get_json()
    phone_number = data.get('phone')
    
    if not phone_number:
        return jsonify({'code': 400001, 'message': '手机号不能为空'}), 400
        
    # 生成验证码
    code = ''.join(random.choices(string.digits, k=6))
    
    # 存储验证码
    redis_client = get_redis_client()
    redis_client.setex(f'sms:code:{phone_number}', 300, code)
    
    # TODO: 调用短信服务发送验证码
    # 开发环境下直接返回验证码
    return jsonify({
        'code': 200,
        'message': '验证码已发送',
        'data': {'code': code}  # 仅在开发环境返回
    })

@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    """验证短信验证码"""
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')

    if not phone or not code:
        return jsonify({
            'code': 400002,
            'message': 'Missing phone number or verification code'
        }), 400

    # 从Redis获取验证码
    redis_client = get_redis_client()
    stored_code = redis_client.get(f'sms:code:{phone}')
    if not stored_code or stored_code.decode() != code:
        return jsonify({
            'code': 400002,
            'message': 'Invalid verification code'
        }), 400
    
    # 查找或创建用户
    user = User.query.filter_by(phone=phone).first()
    if not user:
        # 新用户，使用手机号作为用户名
        user = User(username=phone, phone=phone)
        db.session.add(user)
        db.session.commit()
    
    # 更新登录时间
    user.update_last_login()
    
    # 生成token
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'code': 400002,
        'message': 'Invalid verification code'
    }), 400

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新token"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({
        'code': 200,
        'data': {'access_token': access_token}
    })

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户信息"""
    try:
        current_user_id = get_jwt_identity()
        current_user = db.session.get(User, current_user_id)
        
        if not current_user:
            return jsonify({
                'code': 401002,
                'message': '用户不存在'
            }), 401

        return jsonify({
            'code': 200,
            'data': current_user.to_dict()
        })
    except Exception as e:
        return jsonify({
            'code': 400004,
            'message': str(e)
        }), 400

@auth_bp.route('/wechat-login', methods=['POST'])
def wechat_login():
    """微信登录"""
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'code': 400001, 'message': '缺少微信授权码'}), 400
    
    # 获取微信用户信息
    wechat_service = WeChatService()
    wechat_user = wechat_service.get_user_info(code)
    
    if not wechat_user:
        return jsonify({'code': 400002, 'message': '获取微信用户信息失败'}), 400
    
    # 查找或创建用户
    user = User.query.filter_by(wechat_id=wechat_user['openid']).first()
    if not user:
        # 新用户，使用微信昵称作为用户名
        username = wechat_user.get('nickname', 'wx_' + wechat_user['openid'][:8])
        user = User(
            username=username,
            wechat_id=wechat_user['openid'],
            avatar_url=wechat_user.get('headimgurl')
        )
        db.session.add(user)
        db.session.commit()
    
    # 更新登录时间
    user.update_last_login()
    
    # 生成token
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'code': 200,
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
    })

@auth_bp.route('/bind-phone', methods=['POST'])
@jwt_required()
def bind_phone():
    """绑定手机号"""
    try:
        current_user_id = get_jwt_identity()
        current_user = db.session.get(User, current_user_id)
        
        if not current_user:
            return jsonify({
                'code': 401002,
                'message': '用户不存在'
            }), 401

        data = request.get_json()
        phone = data.get('phone')
        code = data.get('code')
        
        if not phone or not code:
            return jsonify({'code': 400001, 'message': '手机号和验证码不能为空'}), 400
        
        # 验证验证码
        redis_client = get_redis_client()
        stored_code = redis_client.get(f'sms:code:{phone}')
        if not stored_code or stored_code.decode() != code:
            return jsonify({'code': 400002, 'message': '验证码错误或已过期'}), 400
        
        # 检查手机号是否已被其他用户绑定
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'code': 400003, 'message': '该手机号已被其他用户绑定'}), 400
        
        # 更新用户手机号
        current_user.phone = phone
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '手机号绑定成功',
            'data': current_user.to_dict()
        })
    except Exception as e:
        return jsonify({
            'code': 400004,
            'message': str(e)
        }), 400

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'password', 'email')):
        return jsonify({'code': 400001, 'message': '缺少必填字段'}), 400
    
    # 验证密码强度
    if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', data['password']):
        return jsonify({'code': 400002, 'message': '密码必须至少8位，包含字母和数字'}), 400
        
    # 验证邮箱格式
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
        return jsonify({'code': 400003, 'message': '邮箱格式不正确'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'code': 400004, 'message': '用户名已存在'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'code': 400005, 'message': '邮箱已存在'}), 400
    
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    token = create_access_token(identity=user.id)
    
    return jsonify({
        'code': 200,
        'data': {
            'access_token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }
    })

@auth_bp.route('/login', methods=['POST'])
def login():
    """密码登录"""
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'password')):
        return jsonify({'code': 400001, 'message': '缺少用户名或密码'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'code': 401001, 'message': '用户名或密码错误'}), 401
    
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'code': 200,
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
    })

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    new_password = data.get('new_password')
    
    if not all([phone, code, new_password]):
        return jsonify({'code': 400001, 'message': '所有字段都是必填的'}), 400
    
    # 验证密码强度
    if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', new_password):
        return jsonify({'code': 400002, 'message': '密码必须至少8位，包含字母和数字'}), 400
    
    # 验证验证码
    redis_client = get_redis_client()
    stored_code = redis_client.get(f'sms:code:{phone}')
    if not stored_code or stored_code.decode() != code:
        return jsonify({'code': 400003, 'message': '验证码错误或已过期'}), 400
    
    # 查找用户
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'code': 400004, 'message': '用户不存在'}), 400
    
    # 更新密码
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '密码重置成功'
    })
