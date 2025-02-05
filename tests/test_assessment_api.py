import pytest
from unittest.mock import patch, MagicMock
from flask_jwt_extended import create_access_token
from app.models.assessment import UserLevelAssessment
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app import db, create_app

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        # 创建所有数据库表
        db.create_all()
        
        # 创建必要的测试数据
        book = VocabularyBook(name='Test Book', user_id=1)
        db.session.add(book)
        
        # 创建一些单词
        words = [
            Word(text='test', definition='测试'),
            Word(text='hello', definition='你好'),
            Word(text='world', definition='世界'),
            Word(text='python', definition='蟒蛇')
        ]
        for word in words:
            db.session.add(word)
        
        db.session.commit()
        
        # 创建单词和词书的关联
        for i, word in enumerate(words):
            relation = WordRelation(
                word_id=word.id,
                book_id=book.id,
                order=i+1
            )
            db.session.add(relation)
        
        db.session.commit()
        
        yield app
        
        # 清理数据库
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """创建测试用户"""
    with app.app_context():
        from app.models.user import User
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
    """创建认证头"""
    with app.app_context():
        access_token = create_access_token(identity=test_user.id)
        return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def setup_test_data(app, test_user):
    """创建测试数据"""
    with app.app_context():
        # 创建词书
        book = VocabularyBook(
            name='Test Book',
            user_id=test_user.id,
            description='Test Description',
            level='beginner'
        )
        db.session.add(book)
        db.session.commit()
        
        # 创建单词
        words = [
            Word(text='hello', definition='你好'),
            Word(text='python', definition='蟒蛇'),
            Word(text='world', definition='世界'),
            Word(text='test', definition='测试'),
            Word(text='apple', definition='苹果'),
            Word(text='book', definition='书本'),
            Word(text='computer', definition='电脑'),
            Word(text='phone', definition='手机'),
            Word(text='table', definition='桌子'),
            Word(text='chair', definition='椅子'),
            Word(text='window', definition='窗户'),
            Word(text='door', definition='门')
        ]
        for word in words:
            db.session.add(word)
        db.session.commit()

        # 创建单词和词书的关联
        for word in words:
            relation = WordRelation(word_id=word.id, book_id=book.id)
            db.session.add(relation)
        db.session.commit()

        return {
            'user': test_user,
            'book': book,
            'words': words
        }

def test_start_assessment(client, auth_headers, app, setup_test_data):
    """测试开始评估"""
    with app.app_context():
        # 使用setup_test_data中的数据
        book = setup_test_data['book']
        
        # 发送开始评估请求
        response = client.post(
            '/api/v1/assessment/start',
            json={'book_id': book.id},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # 验证返回的数据
        assert data['code'] == 200
        assert 'assessment_id' in data['data']
        assert 'questions' in data['data']
        assert len(data['data']['questions']) > 0
        
        # 验证问题格式
        for question in data['data']['questions']:
            assert 'id' in question
            assert 'word' in question
            assert 'options' in question
            assert len(question['options']) == 4  # 应该有4个选项
            
        # 验证评估记录是否创建
        assessment = UserLevelAssessment.query.get(data['data']['assessment_id'])
        assert assessment is not None
        assert assessment.user_id == setup_test_data['user'].id
        assert assessment.book_id == book.id
        assert assessment.status == 'in_progress'

def test_start_assessment_missing_book_id(client, auth_headers):
    """测试开始评估时缺少book_id参数"""
    response = client.post('/api/v1/assessment/start',
        json={'question_count': 10},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['code'] == 400
    assert 'message' in data

def test_submit_assessment(client, auth_headers, app, setup_test_data):
    """测试提交评估答案"""
    with app.app_context():
        # 先创建一个评估
        book = setup_test_data['book']
        start_response = client.post('/api/v1/assessment/start',
            json={
                'book_id': book.id,
                'question_count': 2
            },
            headers=auth_headers
        )
        
        assert start_response.status_code == 200
        start_data = start_response.get_json()
        
        # 提交答案
        assessment_id = start_data['data']['assessment_id']
        questions = start_data['data']['questions']
        answers = [
            {'question_id': q['id'], 'answer': q['options'][0]}
            for q in questions
        ]
        
        response = client.post('/api/v1/assessment/submit',
            json={
                'assessment_id': assessment_id,
                'answers': answers
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'score' in data['data']
        assert 'correct_count' in data['data']
        assert 'total_count' in data['data']

def test_submit_assessment_missing_answers(client, auth_headers, app, setup_test_data):
    """测试提交评估时缺少答案"""
    with app.app_context():
        book = setup_test_data['book']
        start_response = client.post('/api/v1/assessment/start',
            json={
                'book_id': book.id,
                'question_count': 2
            },
            headers=auth_headers
        )
        
        assert start_response.status_code == 200
        start_data = start_response.get_json()
        assessment_id = start_data['data']['assessment_id']
        
        # 提交空答案
        response = client.post('/api/v1/assessment/submit',
            json={
                'assessment_id': assessment_id,
                'answers': []
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 400

def test_get_assessment_history(client, auth_headers, app, setup_test_data):
    """测试获取评估历史"""
    with app.app_context():
        book = setup_test_data['book']
        
        # 先创建一些评估记录
        client.post('/api/v1/assessment/start',
            json={
                'book_id': book.id,
                'question_count': 2
            },
            headers=auth_headers
        )
        
        response = client.get('/api/v1/assessment/history',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'assessments' in data['data']
        assert isinstance(data['data']['assessments'], list)

def test_get_assessment_analysis(client, auth_headers, app, setup_test_data):
    """测试获取评估分析"""
    with app.app_context():
        book = setup_test_data['book']
        
        # 先创建并完成一个评估
        start_response = client.post('/api/v1/assessment/start',
            json={
                'book_id': book.id,
                'question_count': 2
            },
            headers=auth_headers
        )
        
        start_data = start_response.get_json()
        assessment_id = start_data['data']['assessment_id']
        
        # 获取分析
        response = client.get(f'/api/v1/assessment/analysis/{assessment_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'analysis' in data['data'] 