import json
import pytest
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.word import Word
from app.models.vocabulary import VocabularyBook
from app import db
import jwt
import datetime
from app import create_app
from flask_jwt_extended import create_access_token

@pytest.fixture(scope='function')
def init_database(db_session):
    """初始化测试数据库"""
    try:
        # 创建测试用户
        user = User(
            username='testuser',
            phone='13800138001',  # 修改字段名
            email='test@example.com'  # 添加必需的 email 字段
        )
        user.set_password('test123')
        db_session.add(user)
        db_session.flush()  # 获取user.id
        
        # 创建测试单词书
        book = VocabularyBook(
            name='IELTS词汇',
            description='雅思考试常用词汇',
            level='advanced',
            user_id=user.id  # 设置user_id
        )
        db_session.add(book)
        
        # 创建测试单词
        word = Word(
            text='ubiquitous',  # 修改字段名
            phonetic='/juːˈbɪkwɪtəs/',
            definition='存在于所有地方的，普遍存在的',
            example='Mobile phones have become ubiquitous in modern society.'
        )
        db_session.add(word)
        
        # 提交事务
        db_session.commit()
        
        # 返回测试数据
        return {'user': user, 'book': book, 'word': word}
    except IntegrityError as e:
        db_session.rollback()
        raise

def test_register(client, redis_client):
    """测试用户注册"""
    try:
        # 先发送验证码
        phone = '13800138001'  # 修改变量名
        redis_client.setex(f'sms:code:{phone}', 300, '123456')

        # 注册请求
        response = client.post('/api/v1/auth/register', json={
            'phone': phone,  # 修改字段名
            'code': '123456',
            'username': 'test_register',
            'password': 'Test123456',
            'email': 'test_register@example.com'  # 添加 email 字段
        })

        assert response.status_code == 200
        assert response.json['code'] == 200
        assert 'access_token' in response.json['data']
        assert 'user' in response.json['data']
        
        # 验证用户是否创建成功
        user = User.query.filter_by(username='test_register').first()
        assert user is not None
        assert user.check_password('Test123456')
    except Exception as e:
        print(f"Error in test_register: {str(e)}")
        raise

def test_password_login(client, init_database):
    """测试密码登录"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',  # 修改为正确的用户名
        'password': 'test123'
    })
    
    assert response.status_code == 200
    assert response.json['code'] == 200
    assert 'access_token' in response.json['data']

def test_send_code(client, redis_client):
    """测试发送验证码"""
    response = client.post('/api/v1/auth/send-code', json={
        'phone': '13800138002'  # 修改字段名
    })
    
    assert response.status_code == 200
    assert response.json['code'] == 200
    
    # 验证验证码是否存储在Redis中
    code = redis_client.get(f'sms:code:13800138002')
    assert code is not None

def test_verify_code(client, redis_client):
    """测试验证码验证"""
    phone = '13800138003'  # 修改变量名
    redis_client.setex(f'sms:code:{phone}', 300, '123456')
    
    response = client.post('/api/v1/auth/verify-code', json={
        'phone': phone,  # 修改字段名
        'code': '123456'
    })
    
    assert response.status_code == 400
    assert response.json['code'] == 400002
    assert 'message' in response.json

@patch('app.services.wechat_service.WeChatService.get_access_token')
@patch('app.services.wechat_service.WeChatService.get_user_info')
def test_wechat_login(mock_get_user_info, mock_get_access_token, client):
    """测试微信登录"""
    # 模拟微信API返回
    mock_get_access_token.return_value = {
        'access_token': 'test_token',
        'openid': 'test_openid'
    }
    mock_get_user_info.return_value = {
        'openid': 'test_openid',
        'nickname': 'test_nickname',
        'email': 'wechat_user@example.com'  # 添加 email 字段
    }
    
    response = client.post('/api/v1/auth/wechat-login', json={
        'code': 'test_code'
    })
    
    assert response.status_code == 200
    assert response.json['code'] == 200
    assert 'access_token' in response.json['data']

def test_bind_phone(client, auth_headers, redis_client):
    """测试绑定手机号"""
    phone = '13800138004'  # 修改变量名
    redis_client.setex(f'sms:code:{phone}', 300, '123456')
    
    response = client.post('/api/v1/auth/bind-phone', 
        json={
            'phone': phone,  # 修改字段名
            'code': '123456'
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json['code'] == 200

def test_reset_password(client, init_database, redis_client):
    """测试重置密码"""
    phone = '13800138005'  # 修改变量名
    redis_client.setex(f'sms:code:{phone}', 300, '123456')
    
    # 先创建用户
    user = User.query.filter_by(id=1).first()
    user.phone = phone  # 修改字段名
    db.session.commit()
    
    response = client.post('/api/v1/auth/reset-password', json={
        'phone': phone,  # 修改字段名
        'code': '123456',
        'new_password': 'NewTest123'
    })
    
    assert response.status_code == 200
    assert response.json['code'] == 200
    
    # 验证新密码是否生效
    user = User.query.filter_by(phone=phone).first()  # 修改字段名
    assert user.check_password('NewTest123')

def test_refresh_token(client, init_database):
    """测试刷新令牌"""
    # 先登录获取refresh_token
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'test123'
    })
    
    refresh_token = response.json['data']['refresh_token']
    
    # 使用refresh_token刷新access_token
    response = client.post('/api/v1/auth/refresh',
        headers={'Authorization': f'Bearer {refresh_token}'}
    )
    
    assert response.status_code == 200
    assert response.json['code'] == 200
    assert 'access_token' in response.json['data']

def test_get_profile(client, auth_headers):
    """测试获取用户信息"""
    response = client.get('/api/v1/auth/profile',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json['code'] == 200
    assert 'username' in response.json['data']

def test_invalid_token(client):
    """测试无效的令牌"""
    # 使用无效的token
    headers = {'Authorization': 'Bearer invalid_token'}
    response = client.get('/api/v1/auth/profile', headers=headers)
    
    assert response.status_code == 401
    assert response.json['code'] == 401001

def test_user_not_exist(client):
    """测试用户不存在的情况"""
    # 使用不存在的用户ID生成token
    with client.application.app_context():
        token = create_access_token(identity=999)
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/api/v1/auth/profile', headers=headers)
    
    assert response.status_code == 401
    assert response.json['code'] == 401002

def test_invalid_verification_code(client, redis_client):
    """测试验证码错误的情况"""
    phone = '13800138006'
    redis_client.setex(f'sms:code:{phone}', 300, '123456')
    
    response = client.post('/api/v1/auth/verify-code', json={
        'phone': phone,
        'code': '654321'  # 错误的验证码
    })
    
    assert response.status_code == 400
    assert response.json['code'] == 400002

def test_invalid_password_format(client):
    """测试密码格式错误的情况"""
    response = client.post('/api/v1/auth/register', json={
        'username': 'test_user',
        'password': '123',  # 密码太短且没有字母
        'email': 'test@example.com'
    })
    
    assert response.status_code == 400
    assert response.json['code'] == 400002

def test_invalid_email_format(client):
    """测试邮箱格式错误的情况"""
    response = client.post('/api/v1/auth/register', json={
        'username': 'test_user',
        'password': 'Test123456',
        'email': 'invalid_email'  # 无效的邮箱格式
    })
    
    assert response.status_code == 400
    assert response.json['code'] == 400003

def test_duplicate_username(client, init_database):
    """测试重复用户名注册"""
    response = client.post('/api/v1/auth/register', json={
        'username': 'testuser',  # 已存在的用户名
        'password': 'Test123456',
        'email': 'another@example.com'
    })
    
    assert response.status_code == 400
    assert response.json['code'] == 400004

def test_duplicate_email(client, init_database):
    """测试重复邮箱注册"""
    response = client.post('/api/v1/auth/register', json={
        'username': 'another_user',
        'password': 'Test123456',
        'email': 'test@example.com'  # 已存在的邮箱
    })
    
    assert response.status_code == 400
    assert response.json['code'] == 400005

def test_bind_phone_invalid_code(client, auth_headers, redis_client):
    """测试绑定手机号时验证码错误"""
    phone = '13800138007'
    redis_client.setex(f'sms:code:{phone}', 300, '123456')
    
    response = client.post('/api/v1/auth/bind-phone',
        json={
            'phone': phone,
            'code': '654321'  # 错误的验证码
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert response.json['code'] == 400002

def test_bind_phone_duplicate(client, init_database, redis_client):
    """测试绑定已被其他用户绑定的手机号"""
    # 创建另一个用户
    user2 = User(
        username='testuser2',
        email='test2@example.com'
    )
    user2.set_password('test123')
    db.session.add(user2)
    db.session.commit()
    
    # 为新用户生成token
    with client.application.app_context():
        token = create_access_token(identity=user2.id)
    headers = {'Authorization': f'Bearer {token}'}
    
    # 尝试绑定第一个用户的手机号
    phone = '13800138001'  # 使用已存在用户的手机号
    redis_client.setex(f'sms:code:{phone}', 300, '123456')
    
    response = client.post('/api/v1/auth/bind-phone',
        json={
            'phone': phone,
            'code': '123456'
        },
        headers=headers
    )
    
    assert response.status_code == 400
    assert response.json['code'] == 400003

def test_reset_password_invalid_code(client, init_database, redis_client):
    """测试重置密码时验证码错误"""
    phone = '13800138001'
    redis_client.setex(f'sms:code:{phone}', 300, '123456')
    
    response = client.post('/api/v1/auth/reset-password', json={
        'phone': phone,
        'code': '654321',  # 错误的验证码
        'new_password': 'NewTest123'
    })
    
    assert response.status_code == 400
    assert response.json['code'] == 400003

def test_reset_password_invalid_format(client, init_database, redis_client):
    """测试重置密码时新密码格式错误"""
    phone = '13800138001'
    redis_client.setex(f'sms:code:{phone}', 300, '123456')
    
    response = client.post('/api/v1/auth/reset-password', json={
        'phone': phone,
        'code': '123456',
        'new_password': '123'  # 密码格式错误
    })
    
    assert response.status_code == 400
    assert response.json['code'] == 400002 