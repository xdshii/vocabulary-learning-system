import pytest
from datetime import timedelta
from app.config import Config, TestingConfig

def test_default_config():
    """测试默认配置"""
    config = Config()
    
    assert config.SECRET_KEY == 'hard to guess string'
    assert config.SQLALCHEMY_DATABASE_URI == 'postgresql://postgres:postgres@localhost/vocabulary'
    assert config.SQLALCHEMY_TRACK_MODIFICATIONS is False
    assert config.JWT_SECRET_KEY == 'jwt-secret-string'
    assert config.JWT_ACCESS_TOKEN_EXPIRES == timedelta(hours=1)
    assert config.JWT_REFRESH_TOKEN_EXPIRES == timedelta(days=30)
    assert config.REDIS_URL == 'redis://localhost:6379/0'

def test_testing_config():
    """测试测试环境配置"""
    config = TestingConfig()
    
    # 继承自基类的配置
    assert config.SECRET_KEY == 'hard to guess string'
    assert config.SQLALCHEMY_DATABASE_URI == 'sqlite:///:memory:'
    assert config.SQLALCHEMY_TRACK_MODIFICATIONS is False
    assert config.JWT_SECRET_KEY == 'jwt-secret-string'
    assert config.JWT_ACCESS_TOKEN_EXPIRES == timedelta(hours=1)
    assert config.JWT_REFRESH_TOKEN_EXPIRES == timedelta(days=30)
    assert config.REDIS_URL == 'redis://localhost:6379/0'
    
    # 测试环境特有的配置
    assert config.TESTING is True
    assert config.WTF_CSRF_ENABLED is False
    assert config.PRESERVE_CONTEXT_ON_EXCEPTION is False 