import pytest
from flask import Flask, jsonify
from app.utils.auth import login_required
from flask_jwt_extended import create_access_token, JWTManager
from datetime import timedelta
from app.extensions import db
from app.models.user import User

@pytest.fixture
def app():
    """创建测试应用"""
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    JWTManager(app)  # 初始化JWTManager
    db.init_app(app)  # 初始化SQLAlchemy
    
    # 创建测试路由
    @app.route('/test-auth')
    @login_required
    def test_auth():
        return jsonify(code=200, message='success')
    
    return app

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture(autouse=True)
def setup_database(app):
    """设置和清理数据库"""
    with app.app_context():
        db.create_all()  # 创建所有表
        
        # 创建测试用户
        user = User(username='test_user', email='test@example.com')
        user.set_password('test123')
        db.session.add(user)
        db.session.commit()
        
    yield
    
    with app.app_context():
        db.session.remove()
        db.drop_all()

def test_login_required_without_token(client):
    """测试未提供token的情况"""
    response = client.get('/test-auth')
    assert response.status_code == 401
    assert response.json['code'] == 401
    assert response.json['message'] == '请先登录'

def test_login_required_with_invalid_token(client):
    """测试提供无效token的情况"""
    headers = {'Authorization': 'Bearer invalid-token'}
    response = client.get('/test-auth', headers=headers)
    assert response.status_code == 401
    assert response.json['code'] == 401
    assert response.json['message'] == '请先登录'

def test_login_required_with_valid_token(client, app):
    """测试提供有效token的情况"""
    with app.app_context():
        token = create_access_token(identity=1)
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/test-auth', headers=headers)
    assert response.status_code == 200
    assert response.json['code'] == 200
    assert response.json['message'] == 'success'

def test_login_required_with_expired_token(client, app):
    """测试提供过期token的情况"""
    with app.app_context():
        token = create_access_token(identity=1, expires_delta=timedelta(seconds=-1))  # 创建已过期的token
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/test-auth', headers=headers)
    assert response.status_code == 401
    assert response.json['message'] == '请先登录' 