import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app import create_app, db
from app.models.test import Test, TestQuestion, TestRecord
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.user import User
from app.models.learning import LearningRecord
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def init_database(app, db_session):
    """初始化测试数据库"""
    try:
        # 创建测试用户
        user = User(
            username='testuser',
            phone='13800138002',  # 使用不同的手机号
            email='test@example.com'  # 添加必需的 email 字段
        )
        user.set_password('test123')
        db_session.add(user)
        db_session.flush()  # 提交用户以获取 ID
        
        # 创建测试单词书
        book = VocabularyBook(
            name='IELTS词汇',
            description='雅思考试常用词汇',
            level='advanced',
            user_id=user.id  # 添加 user_id
        )
        db_session.add(book)
        
        # 创建测试单词
        words = [
            Word(
                text='ubiquitous',
                phonetic='/juːˈbɪkwɪtəs/',
                definition='存在于所有地方的，普遍存在的',
                example='Mobile phones have become ubiquitous in modern society.'
            ),
            Word(
                text='ephemeral',
                phonetic='/ɪˈfem(ə)rəl/',
                definition='短暂的，瞬息的',
                example='Social media trends are often ephemeral.'
            ),
            Word(
                text='serendipity',
                phonetic='/ˌserənˈdɪpəti/',
                definition='意外发现美好事物的能力',
                example='Finding this book was pure serendipity.'
            ),
            Word(
                text='resilient',
                phonetic='/rɪˈzɪliənt/',
                definition='有适应力的，能快速恢复的',
                example='The human spirit is remarkably resilient.'
            ),
            Word(
                text='paradigm',
                phonetic='/ˈpærədaɪm/',
                definition='范例，模式',
                example='This discovery represents a paradigm shift in our understanding.'
            )
        ]
        for word in words:
            db_session.add(word)
        
        # 提交事务以获取 ID
        db_session.flush()
        
        # 创建单词和单词书的关联关系
        for i, word in enumerate(words, 1):
            word_relation = WordRelation(
                word_id=word.id,
                book_id=book.id,
                order=i
            )
            db_session.add(word_relation)
        
        # 提交事务
        db_session.commit()
        
        # 生成认证令牌
        with app.app_context():
            access_token = create_access_token(identity=user.id)
            auth_headers = {'Authorization': f'Bearer {access_token}'}
        
        # 返回测试数据
        return {'user': user, 'book': book, 'words': words, 'auth_headers': auth_headers}
    except IntegrityError as e:
        db_session.rollback()
        raise

@pytest.fixture
def auth_headers(client, init_database):
    """获取认证头"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'test123'
    })
    if not response.json:
        raise Exception(f"登录失败: {response.status_code} - {response.data}")
    
    # 从嵌套的 data 字段中获取 access_token
    data = response.json.get('data', {})
    token = data.get('access_token')
    if not token:
        raise Exception(f"登录响应中没有access_token: {response.json}")
    return {'Authorization': f'Bearer {token}'}

def test_create_test(client, init_database, auth_headers):
    """测试创建测试"""
    response = client.post('/api/v1/tests', json={
        'name': '词汇测试1',
        'description': '测试描述',
        'book_id': 1,
        'duration': 30,
        'total_questions': 10,
        'pass_score': 60
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json.get('data', {})
    assert data.get('name') == '词汇测试1'

def test_submit_test(client, init_database, auth_headers):
    """测试提交测试答案"""
    # 先创建一个测试
    test_data = {
        'name': '词汇测试2',
        'description': '测试描述',
        'book_id': 1,
        'duration': 30,
        'total_questions': 10,
        'pass_score': 60
    }
    response = client.post('/api/v1/tests', json=test_data, headers=auth_headers)
    print(f"\n创建测试响应: {response.status_code} - {response.data}")
    data = response.json.get('data', {})
    test_id = data.get('id')
    assert test_id is not None, f"创建测试失败: {response.json}"
    
    # 开始测试
    response = client.post(f'/api/v1/tests/{test_id}/start', headers=auth_headers)
    print(f"开始测试响应: {response.status_code} - {response.data}")
    assert response.status_code == 200, "开始测试失败"
    
    # 提交测试答案
    answers = [{'question_id': 1, 'answer': 'A'}, {'question_id': 2, 'answer': 'B'}]
    response = client.post(f'/api/v1/tests/{test_id}/submit', json={'answers': answers}, headers=auth_headers)
    print(f"提交测试答案响应: {response.status_code} - {response.data}")
    assert response.status_code == 200
    data = response.json.get('data', {})
    assert 'score' in data

def test_get_test_results(client, init_database):
    """测试获取测试结果"""
    auth_headers = init_database['auth_headers']
    # 先创建一个测试
    test_data = {
        'name': '词汇测试3',
        'description': '测试描述',
        'book_id': 1,
        'duration': 30,
        'total_questions': 10,
        'pass_score': 60
    }
    response = client.post('/api/v1/tests', json=test_data, headers=auth_headers)
    data = response.json.get('data', {})
    test_id = data.get('id')
    assert test_id is not None, "创建测试失败"
    
    # 开始测试
    response = client.post(f'/api/v1/tests/{test_id}/start', headers=auth_headers)
    assert response.status_code == 200, "开始测试失败"
    
    # 提交测试答案
    answers = [{'question_id': 1, 'answer': 'A'}, {'question_id': 2, 'answer': 'B'}]
    response = client.post(f'/api/v1/tests/{test_id}/submit', json={'answers': answers}, headers=auth_headers)
    assert response.status_code == 200, "提交测试答案失败"
    
    # 获取测试结果
    response = client.get(f'/api/v1/tests/{test_id}/results', headers=auth_headers)
    assert response.status_code == 200

def test_unauthorized_access(client, init_database):
    """测试未授权访问"""
    response = client.get('/api/v1/tests/1')
    assert response.status_code == 401

def test_invalid_test_data(client, init_database):
    """测试无效的测试数据"""
    auth_headers = init_database['auth_headers']
    response = client.post('/api/v1/tests', json={
        'name': '',  # 无效的名称
        'book_id': 1,
        'duration': -1  # 无效的时长
    }, headers=auth_headers)
    assert response.status_code == 400

def test_generate_test(client, init_database):
    """测试生成测试"""
    auth_headers = init_database['auth_headers']
    response = client.post('/api/v1/tests/generate', json={
        'book_id': 1,
        'question_count': 5,
        'test_type': 'multiple_choice'
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json.get('data', {})
    assert 'id' in data
    assert 'questions' in data
    assert len(data['questions']) == 5

def test_get_tests(client, init_database):
    """测试获取测试列表"""
    auth_headers = init_database['auth_headers']
    response = client.get('/api/v1/tests', headers=auth_headers)
    assert response.status_code == 200
    data = response.json.get('data', {})
    assert 'items' in data

def test_test_lifecycle(client, init_database):
    """测试完整的测试生命周期（创建、更新、获取详情、删除）"""
    auth_headers = init_database['auth_headers']
    # 创建测试
    response = client.post('/api/v1/tests', json={
        'name': '生命周期测试',
        'description': '测试描述',
        'book_id': 1,
        'duration': 30,
        'total_questions': 10,
        'pass_score': 60
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json.get('data', {})
    test_id = data.get('id')
    assert test_id is not None
    
    # 更新测试
    response = client.put(f'/api/v1/tests/{test_id}', json={
        'name': '更新后的测试',
        'duration': 45
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json.get('data', {})
    assert data.get('name') == '更新后的测试'
    assert data.get('duration') == 45
    
    # 获取测试详情
    response = client.get(f'/api/v1/tests/{test_id}', headers=auth_headers)
    assert response.status_code == 200
    data = response.json.get('data', {})
    assert data.get('name') == '更新后的测试'
    
    # 删除测试
    response = client.delete(f'/api/v1/tests/{test_id}', headers=auth_headers)
    assert response.status_code == 200
    
    # 确认已删除
    response = client.get(f'/api/v1/tests/{test_id}', headers=auth_headers)
    assert response.status_code == 404

def test_question_management(client, init_database):
    """测试题目管理"""
    auth_headers = init_database['auth_headers']
    # 创建测试
    response = client.post('/api/v1/tests', json={
        'name': '题目管理测试',
        'description': '测试描述',
        'book_id': 1,
        'duration': 30,
        'total_questions': 10,
        'pass_score': 60
    }, headers=auth_headers)
    test_id = response.json.get('data', {}).get('id')
    
    # 添加题目
    question_data = {
        'word_id': 1,
        'question_type': 'multiple_choice',
        'question': 'What is the meaning of "test"?',
        'options': ['A', 'B', 'C', 'D'],
        'correct_answer': 'A'
    }
    response = client.post(f'/api/v1/tests/{test_id}/questions', json=question_data, headers=auth_headers)
    assert response.status_code == 200
    question_id = response.json.get('data', {}).get('id')
    
    # 获取题目列表
    response = client.get(f'/api/v1/tests/{test_id}/questions', headers=auth_headers)
    assert response.status_code == 200
    data = response.json.get('data', {})
    assert 'items' in data
    assert len(data['items']) > 0

def test_test_history_and_statistics(client, init_database):
    """测试历史记录和统计功能"""
    auth_headers = init_database['auth_headers']
    # 创建并完成一些测试
    for i in range(3):
        # 创建测试
        response = client.post('/api/v1/tests', json={
            'name': f'统计测试{i+1}',
            'description': '测试描述',
            'book_id': 1,
            'duration': 30,
            'total_questions': 10,
            'pass_score': 60
        }, headers=auth_headers)
        test_id = response.json.get('data', {}).get('id')
        
        # 开始测试
        response = client.post(f'/api/v1/tests/{test_id}/start', headers=auth_headers)
        assert response.status_code == 200
        
        # 提交答案
        answers = [{'question_id': 1, 'answer': 'A'}, {'question_id': 2, 'answer': 'B'}]
        response = client.post(f'/api/v1/tests/{test_id}/submit', json={'answers': answers}, headers=auth_headers)
        assert response.status_code == 200
    
    # 获取历史记录
    response = client.get('/api/v1/tests/history', headers=auth_headers)
    assert response.status_code == 200
    data = response.json.get('data', {})
    assert 'items' in data
    assert len(data['items']) == 3

def test_error_cases(client, init_database):
    """测试各种错误情况"""
    auth_headers = init_database['auth_headers']
    # 访问不存在的测试
    response = client.get('/api/v1/tests/999', headers=auth_headers)
    assert response.status_code == 404
    
    # 访问其他用户的测试（需要先创建另一个用户的测试）
    other_user = User(
        username='otheruser',
        phone='13800138003',
        email='other@example.com'
    )
    other_user.set_password('test123')
    db.session.add(other_user)
    db.session.commit()
    
    test = Test(
        user_id=other_user.id,
        book_id=1,
        name='其他用户的测试',
        duration=30,
        total_questions=10,
        pass_score=60
    )
    db.session.add(test)
    db.session.commit()
    
    response = client.get(f'/api/v1/tests/{test.id}', headers=auth_headers)
    assert response.status_code == 403
    
    # 提交无效的答案格式
    response = client.post('/api/v1/tests/1/submit', json={
        'invalid': 'data'
    }, headers=auth_headers)
    assert response.status_code == 400
    
    # 重复提交测试答案
    test_id = test.id
    response = client.post(f'/api/v1/tests/{test_id}/submit', json={
        'answers': [{'question_id': 1, 'answer': 'A'}]
    }, headers=auth_headers)
    assert response.status_code in [400, 403]  # 可能是未授权或测试未开始 