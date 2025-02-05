import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from app import create_app, db
from app.models.user import User
from app.models.word import Word
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.learning import LearningRecord, LearningGoal
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app, init_database):
    """生成认证头部"""
    with app.app_context():
        access_token = create_access_token(identity=init_database['user'].id)
        return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture(scope='function')
def init_database(db_session):
    """初始化测试数据库"""
    try:
        # 创建测试用户
        user = User(
            username='testuser',
            phone='13800138003',  # 修改字段名
            email='test@example.com'  # 添加必需的 email 字段
        )
        user.set_password('test123')
        db_session.add(user)
        
        # 创建测试单词书
        book = VocabularyBook(
            name='IELTS词汇',
            description='雅思考试常用词汇',
            level='advanced',
            user_id=1  # 添加必需的 user_id 字段
        )
        db_session.add(book)
        db_session.flush()  # 获取 book.id
        
        # 创建测试单词
        word = Word(
            text='ubiquitous',  # 修改字段名
            phonetic='/juːˈbɪkwɪtəs/',  # 修改字段名
            definition='存在于所有地方的，普遍存在的',
            example='Mobile phones have become ubiquitous in modern society.'
        )
        db_session.add(word)
        db_session.flush()  # 获取 word.id
        
        # 创建单词和词汇书的关联关系
        word_relation = WordRelation(
            word_id=word.id,
            book_id=book.id,
            order=1
        )
        db_session.add(word_relation)
        db_session.commit()
        
        return {
            'user': user,
            'book': book,
            'word': word
        }
    except Exception as e:
        db_session.rollback()
        raise e

def test_create_learning_goal(client, auth_headers, init_database):
    """测试创建学习目标"""
    book = init_database['book']
    
    response = client.post('/api/v1/learning/goals',
        json={
            'book_id': book.id,
            'daily_words': 20,
            'target_date': (datetime.utcnow() + timedelta(days=30)).date().isoformat()
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json['code'] == 200
    assert 'id' in response.json['data']
    
    # 验证学习目标是否创建成功
    goal = db.session.get(LearningGoal, response.json['data']['id'])
    assert goal is not None
    assert goal.daily_word_count == 20
    assert goal.book_id == book.id
    assert goal.user_id == init_database['user'].id
    assert goal.status == 'active'  # 验证状态是否为激活状态

def test_get_review_plan(client, auth_headers, init_database):
    """测试获取复习计划"""
    # 创建一些需要复习的记录
    user = init_database['user']
    word = init_database['word']
    
    learning_record = LearningRecord(
        user_id=user.id,
        word_id=word.id,
        book_id=init_database['book'].id,
        status='learning',
        review_count=2,
        next_review_time=datetime.utcnow() - timedelta(hours=1)  # 设置为过去时间，确保需要复习
    )
    db.session.add(learning_record)
    db.session.commit()
    
    response = client.get('/api/v1/learning/review/plan',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json['code'] == 200
    assert 'data' in response.json
    assert 'words' in response.json['data']
    assert len(response.json['data']['words']) >= 1
    assert 'total' in response.json['data']
    assert response.json['data']['total'] >= 1

def test_complete_review(client, auth_headers, init_database):
    """测试完成复习"""
    # 创建一个复习计划
    user = init_database['user']
    word = init_database['word']
    
    learning_record = LearningRecord(
        user_id=user.id,
        word_id=word.id,
        book_id=init_database['book'].id,
        status='learning',
        review_count=3,
        next_review_time=datetime.utcnow() - timedelta(hours=1)
    )
    db.session.add(learning_record)
    db.session.commit()
    
    response = client.post(f'/api/v1/learning/review/complete/{learning_record.id}',
        headers=auth_headers,
        json={
            'result': 'remembered'  # 添加复习结果
        }
    )
    
    assert response.status_code == 200
    assert response.json['code'] == 200
    
    # 验证学习记录是否正确更新
    learning_record = db.session.get(LearningRecord, learning_record.id)
    assert learning_record.review_count == 4
    assert learning_record.status == 'learning'  # 确认状态保持不变
    assert learning_record.next_review_time > datetime.utcnow()  # 确认下次复习时间已更新

def test_add_word(client, auth_headers, init_database):
    """测试添加单词"""
    book = init_database['book']
    response = client.post(
        f'/api/v1/vocabulary/books/{book.id}/words',
        headers=auth_headers,
        json={
            'text': 'ephemeral',  # 修改字段名
            'phonetic': 'ɪˈfem(ə)rəl',  # 修改字段名
            'definition': '短暂的，瞬息的',
            'example': 'ephemeral pleasures'
        }
    )
    assert response.status_code == 200
    assert response.json['data']['text'] == 'ephemeral'  # 修改字段名

def test_get_words(client, auth_headers, init_database):
    """测试获取单词列表"""
    book = init_database['book']
    response = client.get(
        f'/api/v1/vocabulary/books/{book.id}/words',
        headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json['data']['items']) >= 1

def test_update_word(client, auth_headers, init_database):
    """测试更新单词"""
    book = init_database['book']
    word = init_database['word']
    response = client.put(
        f'/api/v1/vocabulary/books/{book.id}/words/{word.id}',
        headers=auth_headers,
        json={
            'phonetic': 'updated-phonetic',  # 修改字段名
            'definition': 'updated definition',
            'example': 'updated example'
        }
    )
    assert response.status_code == 200
    assert response.json['data']['phonetic'] == 'updated-phonetic'  # 修改字段名

def test_delete_word(client, auth_headers, init_database):
    """测试删除单词"""
    book = init_database['book']
    word = init_database['word']
    response = client.delete(
        f'/api/v1/vocabulary/books/{book.id}/words/{word.id}',
        headers=auth_headers
    )
    assert response.status_code == 200

    # 验证是否真的被删除
    response = client.get(
        f'/api/v1/vocabulary/books/{book.id}/words/{word.id}',
        headers=auth_headers
    )
    assert response.status_code == 404

def test_create_vocabulary_book(client, auth_headers):
    """测试创建词汇书"""
    response = client.post(
        '/api/v1/vocabulary/books',
        headers=auth_headers,
        json={
            'name': 'IELTS词汇',
            'description': 'IELTS考试必备词汇',
            'level': 'advanced',
            'tags': ['IELTS', '考试']
        }
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['code'] == 200
    assert 'id' in data['data']

def test_get_vocabulary_books(client, auth_headers, init_database):
    """测试获取词汇书列表"""
    response = client.get(
        '/api/v1/vocabulary/books',
        headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json['data']['items']) >= 1
    assert response.json['data']['items'][0]['name'] == 'IELTS词汇'

def test_get_vocabulary_book_detail(client, auth_headers, init_database):
    """测试获取词汇书详情"""
    book = init_database['book']
    response = client.get(
        f'/api/v1/vocabulary/books/{book.id}',
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json['data']['name'] == 'IELTS词汇'
    assert response.json['data']['description'] == '雅思考试常用词汇'

def test_update_vocabulary_book(client, auth_headers, init_database):
    """测试更新词汇书"""
    book = init_database['book']
    response = client.put(
        f'/api/v1/vocabulary/books/{book.id}',
        headers=auth_headers,
        json={
            'name': 'Updated Book',
            'description': 'Updated Description'
        }
    )
    assert response.status_code == 200
    assert response.json['data']['name'] == 'Updated Book'
    assert response.json['data']['description'] == 'Updated Description'

def test_delete_vocabulary_book(client, auth_headers, init_database):
    """测试删除词汇书"""
    book = init_database['book']
    response = client.delete(
        f'/api/v1/vocabulary/books/{book.id}',
        headers=auth_headers
    )
    assert response.status_code == 200

    # 验证是否真的被删除
    response = client.get(
        f'/api/v1/vocabulary/books/{book.id}',
        headers=auth_headers
    )
    assert response.status_code == 404 