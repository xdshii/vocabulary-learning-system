import pytest
import json
from datetime import datetime, timedelta
from app.models.learning import LearningRecord, LearningGoal
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.user import User
from app import db, create_app
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()  # 创建所有表
        yield app
        db.session.remove()
        db.drop_all()  # 删除所有表

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user(app):
    """创建测试用户"""
    with app.app_context():
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        user = User(
            username=f'test_user_{timestamp}',
            email=f'test_{timestamp}@example.com',
            phone='13800138000'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def auth_headers(app, test_user):
    """生成认证头"""
    with app.app_context():
        access_token = create_access_token(identity=test_user.id)
        return {
            'Authorization': f'Bearer {access_token}'
        }

@pytest.fixture(autouse=True)
def cleanup_database(app):
    """在每个测试前清理数据库"""
    with app.app_context():
        # 删除所有记录
        LearningRecord.query.delete()
        LearningGoal.query.delete()
        WordRelation.query.delete()
        Word.query.delete()
        VocabularyBook.query.delete()
        db.session.commit()
        yield
        # 测试结束后再次清理
        LearningRecord.query.delete()
        LearningGoal.query.delete()
        WordRelation.query.delete()
        Word.query.delete()
        VocabularyBook.query.delete()
        db.session.commit()

@pytest.fixture
def setup_learning_data(client, auth_headers):
    """创建学习相关的测试数据"""
    # 创建词汇书
    response = client.post('/api/v1/vocabulary/books', 
        json={
            'name': 'Test Learning Book',
            'description': 'Test Description',
            'level': 'intermediate'
        },
        headers=auth_headers
    )
    data = json.loads(response.data)
    book_id = data['data']['id']
    
    # 添加单词
    words_data = [
        {
            'text': f'test{i}',
            'definition': f'测试{i}',
            'phonetic': f'test{i}',
            'example': f'This is test{i}.'
        }
        for i in range(1, 4)
    ]
    
    words = []
    for word_data in words_data:
        response = client.post(f'/api/v1/vocabulary/books/{book_id}/words',
            json=word_data,
            headers=auth_headers
        )
        data = json.loads(response.data)
        word = {
            'id': data['data']['id'],
            'text': data['data']['text'],
            'definition': data['data']['definition'],
            'phonetic': data['data']['phonetic'],
            'example': data['data']['example']
        }
        words.append(word)
    
    return {
        'book_id': book_id,
        'words': words
    }

def test_create_learning_plan(client, auth_headers, setup_learning_data):
    """测试创建学习计划"""
    book_id = setup_learning_data['book_id']
    start_date = datetime.now().date().isoformat()

    # 创建计划
    response = client.post('/api/v1/learning/plans',
        json={
            'book_id': book_id,
            'daily_words': 10,
            'start_date': start_date
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['code'] == 200
    assert 'data' in data
    plan_data = data['data']
    assert plan_data['book_id'] == book_id
    assert plan_data['daily_words'] == 10
    assert plan_data['start_date'] == start_date

def test_get_learning_plan(client, auth_headers, setup_learning_data):
    """测试获取学习计划"""
    book_id = setup_learning_data['book_id']
    start_date = datetime.now().date().isoformat()

    # 创建计划
    response = client.post('/api/v1/learning/plans',
        json={
            'book_id': book_id,
            'daily_words': 10,
            'start_date': start_date
        },
        headers=auth_headers
    )
    create_data = json.loads(response.data)
    plan_id = create_data['data']['id']

    # 获取计划
    response = client.get('/api/v1/learning/plans', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['code'] == 200
    assert 'data' in data
    assert 'plans' in data['data']
    assert len(data['data']['plans']) > 0
    assert data['data']['plans'][0]['start_date'] == start_date

def test_update_learning_plan(client, auth_headers, setup_learning_data):
    """测试更新学习计划"""
    book_id = setup_learning_data['book_id']
    start_date = datetime.now().date().isoformat()

    # 创建计划
    response = client.post('/api/v1/learning/plans',
        json={
            'book_id': book_id,
            'daily_words': 10,
            'start_date': start_date
        },
        headers=auth_headers
    )
    create_data = json.loads(response.data)
    plan_id = create_data['data']['id']

    # 更新计划
    response = client.put(f'/api/v1/learning/plans/{plan_id}',
        json={
            'daily_words': 20
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['code'] == 200
    assert 'data' in data
    plan_data = data['data']
    assert plan_data['daily_words'] == 20
    assert plan_data['start_date'] == start_date

def test_create_learning_record(client, auth_headers, setup_learning_data):
    """测试创建学习记录"""
    book_id = setup_learning_data['book_id']
    word_id = setup_learning_data['words'][0]['id']

    response = client.post('/api/v1/learning/records',
        json={
            'book_id': book_id,
            'word_id': word_id,
            'status': 'learning'
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['code'] == 200
    assert 'data' in data
    record_data = data['data']
    assert record_data['word_id'] == word_id
    assert record_data['status'] == 'learning'

def test_update_learning_record(client, auth_headers, setup_learning_data):
    """测试更新学习记录"""
    book_id = setup_learning_data['book_id']
    word_id = setup_learning_data['words'][0]['id']

    # 创建记录
    response = client.post('/api/v1/learning/records',
        json={
            'book_id': book_id,
            'word_id': word_id,
            'status': 'learning'
        },
        headers=auth_headers
    )
    create_data = json.loads(response.data)
    record_id = create_data['data']['id']

    # 更新记录
    response = client.put(f'/api/v1/learning/records/{record_id}',
        json={
            'status': 'mastered'
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['code'] == 200
    assert 'data' in data
    record_data = data['data']
    assert record_data['status'] == 'mastered'

def test_get_learning_statistics(client, auth_headers, setup_learning_data):
    """测试获取学习统计"""
    book_id = setup_learning_data['book_id']
    word_id = setup_learning_data['words'][0]['id']

    # 创建学习记录
    response = client.post('/api/v1/learning/records',
        json={
            'book_id': book_id,
            'word_id': word_id,
            'status': 'learning'
        },
        headers=auth_headers
    )
    create_data = json.loads(response.data)
    record_id = create_data['data']['id']

    # 获取统计信息
    response = client.get('/api/v1/learning/statistics',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['code'] == 200
    assert 'data' in data
    stats = data['data']
    assert 'total' in stats
    assert 'learning' in stats
    assert 'mastered' in stats
    assert 'new_words' in stats
    assert 'avg_review_count' in stats

def test_get_review_list(client, auth_headers, setup_learning_data):
    """测试获取复习列表"""
    book_id = setup_learning_data['book_id']
    word_id = setup_learning_data['words'][0]['id']

    # 创建需要复习的记录
    response = client.post('/api/v1/learning/records',
        json={
            'book_id': book_id,
            'word_id': word_id,
            'status': 'learning'
        },
        headers=auth_headers
    )
    create_data = json.loads(response.data)
    record_id = create_data['data']['id']

    # 获取复习列表
    response = client.get('/api/v1/learning/review/list',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['code'] == 200
    assert 'data' in data
    review_list = data['data']
    assert isinstance(review_list, list)  # 检查是否为列表
    if len(review_list) > 0:  # 如果有数据,检查第一个记录的格式
        first_record = review_list[0]
        assert 'id' in first_record
        assert 'word_id' in first_record
        assert 'status' in first_record

def test_submit_review_result(client, auth_headers, setup_learning_data):
    """测试提交复习结果"""
    book_id = setup_learning_data['book_id']
    word_id = setup_learning_data['words'][0]['id']

    # 创建学习记录
    response = client.post('/api/v1/learning/records',
        json={
            'book_id': book_id,
            'word_id': word_id,
            'status': 'learning'
        },
        headers=auth_headers
    )
    create_data = json.loads(response.data)
    record_id = create_data['data']['id']

    # 提交复习结果
    response = client.post('/api/v1/learning/review/submit',
        json={
            'record_id': record_id,
            'result': 'correct'
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['code'] == 200
    assert 'data' in data
    result_data = data['data']
    assert result_data['status'] in ['learning', 'mastered'] 