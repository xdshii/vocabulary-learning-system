import pytest
import sys
import os
import jwt
import datetime
import redis
from flask_jwt_extended import create_access_token

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import *

# 导入所有模型以确保它们在创建表之前被注册
from app.models.user import User
from app.models.word import Word
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.learning import LearningGoal, ReviewPlan
from app.models.learning_plan import LearningPlan
from app.models.learning_record import LearningRecord
from app.models.assessment import UserLevelAssessment, AssessmentQuestion
from app.models.test import Test, TestQuestion, TestRecord, TestAnswer

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    
    # 创建所有表
    with app.app_context():
        db.create_all()
        
    return app

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """创建测试用户"""
    with app.app_context():
        user = User(
            username='test_user',
            email='test@example.com',
            phone='13800138000'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def auth_headers(app, test_user):
    """创建带有有效JWT token的认证头"""
    with app.app_context():
        access_token = create_access_token(identity=test_user.id)
        return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture(autouse=True)
def cleanup_database(app):
    """在每个测试前清理数据库"""
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        
    yield
    
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def redis_client(app):
    """创建Redis客户端"""
    redis_client = redis.from_url(app.config['REDIS_URL'])
    redis_client.flushdb()  # 清空测试数据库
    return redis_client

@pytest.fixture(scope='function')
def init_database(app, test_user):
    """初始化测试数据"""
    with app.app_context():
        # 创建测试词书
        book = VocabularyBook(
            name='Test Book',
            description='Test Description',
            level='intermediate',
            user_id=test_user.id
        )
        db.session.add(book)
        
        # 创建测试单词
        words = []
        for i in range(10):
            word = Word(
                text=f'test_word_{i}',
                phonetic=f'test_phonetic_{i}',
                definition=f'test_definition_{i}',
                example=f'test_example_{i}'
            )
            db.session.add(word)
            words.append(word)
        
        db.session.commit()
        
        return {'user': test_user, 'book': book, 'words': words}

@pytest.fixture(scope='function')
def setup_test_data(app, init_database):
    """设置测试数据"""
    with app.app_context():
        return init_database

@pytest.fixture(scope='function')
def db_setup(app):
    """创建数据库会话"""
    with app.app_context():
        db.drop_all()  # 先删除所有表
        db.create_all()  # 创建所有表
        db.session.begin_nested()  # 创建保存点
        yield db
        db.session.rollback()  # 回滚到保存点
        db.session.remove()

@pytest.fixture(scope='function')
def db_session(db_setup):
    """提供数据库会话"""
    return db_setup.session

@pytest.fixture(scope='function')
def auth_token(init_database, app):
    """生成认证令牌"""
    user = init_database['user']
    with app.app_context():
        token = create_access_token(identity=user.id)
    return token

@pytest.fixture(scope='function')
def test_book(db_setup, test_user):
    """创建测试单词书"""
    book = VocabularyBook(
        name='Test Book',
        description='Test Description',
        level='intermediate',
        creator_id=test_user.id
    )
    db_setup.session.add(book)
    db_setup.session.commit()
    return book

@pytest.fixture(scope='function')
def test_word(db_setup, test_book):
    """创建测试单词"""
    word = Word(
        text='test',
        phonetic='test',
        definition='test meaning',
        example='test example'
    )
    db_setup.session.add(word)
    db_setup.session.commit()
    return word

@pytest.fixture(scope='function')
def runner(app):
    """测试命令行"""
    return app.test_cli_runner() 