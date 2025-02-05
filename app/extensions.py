from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask import jsonify

db = SQLAlchemy(
    session_options={
        'expire_on_commit': False,
        'autoflush': False
    }
)
migrate = Migrate()
jwt = JWTManager()

# 配置 JWT 错误处理
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    """处理无效的token"""
    return jsonify({
        'code': 401001,
        'message': '无效的令牌'
    }), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """处理过期的token"""
    return jsonify({
        'code': 401002,
        'message': '令牌已过期'
    }), 401

@jwt.unauthorized_loader
def unauthorized_callback(error_string):
    """处理未授权的请求"""
    return jsonify({
        'code': 401003,
        'message': '缺少认证头'
    }), 401

def init_extensions(app):
    """初始化Flask扩展"""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app) 