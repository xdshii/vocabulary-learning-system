from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from app.extensions import db, migrate, jwt, init_extensions
from flask_cors import CORS
from app.config import config

def create_app(config_name='development'):
    """创建Flask应用"""
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 初始化扩展
    init_extensions(app)
    cors = CORS(app)

    # 注册蓝图
    from app.api import (
        auth_bp, vocabulary_bp, learning_bp,
        assessment_bp, test_bp
    )
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(vocabulary_bp, url_prefix='/api/v1/vocabulary')
    app.register_blueprint(learning_bp, url_prefix='/api/v1/learning')
    app.register_blueprint(assessment_bp, url_prefix='/api/v1/assessment')
    app.register_blueprint(test_bp, url_prefix='/api/v1/tests')

    return app 