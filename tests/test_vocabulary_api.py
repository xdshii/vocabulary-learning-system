import pytest
from datetime import datetime, timedelta
from app import db, create_app
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.user import User
from app.models.learning import LearningRecord
from flask_jwt_extended import create_access_token
import json

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
        WordRelation.query.delete()
        Word.query.delete()
        VocabularyBook.query.delete()
        LearningRecord.query.delete()
        db.session.commit()

def test_create_book(client, auth_headers):
    """测试创建词汇书"""
    response = client.post('/api/v1/vocabulary/books',
        json={
            'name': 'Test Book',
            'description': 'This is a test book',
            'level': 'intermediate',
            'tags': ['test', 'vocabulary']
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'code' in data
    assert 'data' in data
    assert 'id' in data['data']
    assert data['data']['name'] == 'Test Book'
    assert data['data']['description'] == 'This is a test book'
    assert data['data']['level'] == 'intermediate'
    assert data['data']['tags'] == ['test', 'vocabulary']

def test_create_book_missing_name(client, auth_headers):
    """测试创建词汇书时缺少名称"""
    response = client.post('/api/v1/vocabulary/books',
        json={
            'description': 'This is a test book'
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['code'] == 400001
    assert 'message' in data

def test_get_books(client, auth_headers, test_user):
    """测试获取词汇书列表"""
    # 创建测试词汇书
    books = [
        VocabularyBook(
            name='Test Book 1',
            description='This is test book 1',
            level='beginner',
            user_id=test_user.id
        ),
        VocabularyBook(
            name='Test Book 2',
            description='This is test book 2',
            level='intermediate',
            user_id=test_user.id
        )
    ]
    with client.application.app_context():
        for book in books:
            db.session.add(book)
        db.session.commit()
    
    response = client.get('/api/v1/vocabulary/books',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 200
    assert 'data' in data
    assert 'items' in data['data']
    assert 'total' in data['data']
    assert data['data']['total'] == 2
    assert len(data['data']['items']) == 2
    assert data['data']['items'][0]['name'] == 'Test Book 1'
    assert data['data']['items'][1]['name'] == 'Test Book 2'

def test_get_books_empty(client, auth_headers):
    """测试获取空的词汇书列表"""
    response = client.get('/api/v1/vocabulary/books',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 200
    assert 'data' in data
    assert 'items' in data['data']
    assert 'total' in data['data']
    assert data['data']['total'] == 0
    assert len(data['data']['items']) == 0

def test_get_book_by_id(client, auth_headers, test_user):
    """测试通过ID获取词汇书"""
    # 创建测试词汇书
    book = VocabularyBook(
        name='Test Book',
        description='This is a test book',
        level='intermediate',
        user_id=test_user.id
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.commit()
        
        response = client.get(f'/api/v1/vocabulary/books/{book.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'data' in data
        assert data['data']['id'] == book.id
        assert data['data']['name'] == 'Test Book'
        assert data['data']['description'] == 'This is a test book'
        assert data['data']['level'] == 'intermediate'

def test_get_book_not_found(client, auth_headers):
    """测试获取不存在的词汇书"""
    response = client.get('/api/v1/vocabulary/books/999',
        headers=auth_headers
    )
    
    assert response.status_code == 404
    data = response.get_json()
    assert data['code'] == 404
    assert 'message' in data

def test_update_book(client, auth_headers, test_user):
    """测试更新词汇书"""
    # 创建测试词汇书
    book = VocabularyBook(
        name='Test Book',
        description='This is a test book',
        level='intermediate',
        user_id=test_user.id
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.commit()
        
        response = client.put(f'/api/v1/vocabulary/books/{book.id}',
            json={
                'name': 'Updated Book',
                'description': 'This is an updated book',
                'level': 'advanced'
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'data' in data
        assert data['data']['id'] == book.id
        assert data['data']['name'] == 'Updated Book'
        assert data['data']['description'] == 'This is an updated book'
        assert data['data']['level'] == 'advanced'

def test_delete_book(client, auth_headers, test_user):
    """测试删除词汇书"""
    # 创建测试词汇书
    book = VocabularyBook(
        name='Test Book',
        description='This is a test book',
        level='intermediate',
        user_id=test_user.id
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.commit()
        
        response = client.delete(f'/api/v1/vocabulary/books/{book.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        
        # 验证词汇书已被删除
        book = VocabularyBook.query.get(book.id)
        assert book is None

def test_add_words_to_book(client, auth_headers, test_user):
    """测试向词汇书添加单词"""
    # 创建测试词汇书和单词
    book = VocabularyBook(
        name='Test Book',
        description='This is a test book',
        level='intermediate',
        user_id=test_user.id
    )
    words = [
        Word(text='apple', definition='苹果'),
        Word(text='banana', definition='香蕉'),
        Word(text='orange', definition='橙子')
    ]
    with client.application.app_context():
        db.session.add(book)
        for word in words:
            db.session.add(word)
        db.session.commit()
        
        response = client.post(f'/api/v1/vocabulary/books/{book.id}/words',
            json={
                'word_ids': [word.id for word in words]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        
        # 验证单词已添加到词汇书
        book = VocabularyBook.query.get(book.id)
        assert len(book.words) == 3
        assert book.words[0].text == 'apple'
        assert book.words[1].text == 'banana'
        assert book.words[2].text == 'orange'

def test_get_book_words(client, auth_headers, test_user):
    """测试获取词汇书中的单词"""
    # 创建测试词汇书和单词
    book = VocabularyBook(
        name='Test Book',
        description='This is a test book',
        level='intermediate',
        user_id=test_user.id
    )
    words = [
        Word(text='apple', definition='苹果'),
        Word(text='banana', definition='香蕉'),
        Word(text='orange', definition='橙子')
    ]
    with client.application.app_context():
        db.session.add(book)
        for word in words:
            db.session.add(word)
        db.session.commit()
        
        # 添加单词到词汇书
        for i, word in enumerate(words):
            relation = WordRelation(
                book_id=book.id,
                word_id=word.id,
                order=i+1
            )
            db.session.add(relation)
        db.session.commit()
        
        response = client.get(f'/api/v1/vocabulary/books/{book.id}/words',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'data' in data
        assert 'items' in data['data']
        assert 'total' in data['data']
        assert data['data']['total'] == 3
        assert len(data['data']['items']) == 3
        assert data['data']['items'][0]['text'] == 'apple'
        assert data['data']['items'][1]['text'] == 'banana'
        assert data['data']['items'][2]['text'] == 'orange'

def test_add_single_word(client, auth_headers, test_user):
    """测试向词汇书添加单个单词"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.commit()
        
        response = client.post(f'/api/v1/vocabulary/books/{book.id}/words',
            json={
                'text': 'apple',
                'phonetic': 'ˈæpl',
                'definition': '苹果',
                'example': 'I eat an apple every day.'
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'data' in data
        assert data['data']['text'] == 'apple'

def test_add_word_missing_fields(client, auth_headers, test_user):
    """测试添加单词时缺少必填字段"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.commit()
        
        response = client.post(f'/api/v1/vocabulary/books/{book.id}/words',
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 400001
        assert 'message' in data

def test_get_word_detail(client, auth_headers, test_user):
    """测试获取单词详情"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    word = Word(
        text='apple',
        phonetic='ˈæpl',
        definition='苹果',
        example='I eat an apple every day.'
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.add(word)
        db.session.commit()
        
        relation = WordRelation(
            book_id=book.id,
            word_id=word.id,
            order=1
        )
        db.session.add(relation)
        db.session.commit()
        
        response = client.get(f'/api/v1/vocabulary/books/{book.id}/words/{word.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'data' in data
        assert data['data']['text'] == 'apple'
        assert data['data']['phonetic'] == 'ˈæpl'
        assert data['data']['definition'] == '苹果'

def test_get_word_not_found(client, auth_headers, test_user):
    """测试获取不存在的单词"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.commit()
        
        response = client.get(f'/api/v1/vocabulary/books/{book.id}/words/999',
            headers=auth_headers
        )
        
        assert response.status_code == 404

def test_update_word_detail(client, auth_headers, test_user):
    """测试更新单词详情"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    word = Word(
        text='apple',
        phonetic='ˈæpl',
        definition='苹果',
        example='I eat an apple every day.'
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.add(word)
        db.session.commit()
        
        relation = WordRelation(
            book_id=book.id,
            word_id=word.id,
            order=1
        )
        db.session.add(relation)
        db.session.commit()
        
        response = client.put(f'/api/v1/vocabulary/books/{book.id}/words/{word.id}',
            json={
                'phonetic': 'ˈæpəl',
                'definition': '苹果(水果)',
                'example': 'An apple a day keeps the doctor away.'
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'data' in data
        assert data['data']['phonetic'] == 'ˈæpəl'
        assert data['data']['definition'] == '苹果(水果)'
        assert data['data']['example'] == 'An apple a day keeps the doctor away.'

def test_unauthorized_access(client, auth_headers, test_user):
    """测试未授权访问"""
    # 创建另一个用户的词汇书
    other_user = User(
        username='other_user',
        email='other@example.com',
        phone='13900139000'
    )
    book = VocabularyBook(
        name='Other Book',
        user_id=None  # 稍后设置
    )
    with client.application.app_context():
        other_user.set_password('password123')
        db.session.add(other_user)
        db.session.commit()
        book.user_id = other_user.id
        db.session.add(book)
        db.session.commit()
        
        # 尝试访问其他用户的词汇书
        response = client.get(f'/api/v1/vocabulary/books/{book.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['code'] == 403001
        assert 'message' in data

def test_get_words_pagination(client, auth_headers, test_user):
    """测试获取单词列表的分页功能"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    # 创建25个测试单词
    words = [
        Word(text=f'word{i}', definition=f'定义{i}')
        for i in range(25)
    ]
    with client.application.app_context():
        db.session.add(book)
        for word in words:
            db.session.add(word)
        db.session.commit()
        
        # 添加单词到词汇书
        for i, word in enumerate(words):
            relation = WordRelation(
                book_id=book.id,
                word_id=word.id,
                order=i+1
            )
            db.session.add(relation)
        db.session.commit()
        
        # 测试第一页（默认每页20条）
        response = client.get(f'/api/v1/vocabulary/books/{book.id}/words',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert data['data']['total'] == 25
        assert len(data['data']['items']) == 20
        assert data['data']['page'] == 1
        assert data['data']['pages'] == 2
        
        # 测试第二页
        response = client.get(f'/api/v1/vocabulary/books/{book.id}/words?page=2',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert len(data['data']['items']) == 5
        assert data['data']['page'] == 2

def test_delete_word(client, auth_headers, test_user):
    """测试从词汇书中删除单词"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    word = Word(
        text='apple',
        definition='苹果'
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.add(word)
        db.session.commit()
        
        relation = WordRelation(
            book_id=book.id,
            word_id=word.id,
            order=1
        )
        db.session.add(relation)
        db.session.commit()
        
        response = client.delete(f'/api/v1/vocabulary/books/{book.id}/words/{word.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'message' in data
        
        # 验证单词关系已被删除
        relation = WordRelation.query.filter_by(
            book_id=book.id,
            word_id=word.id
        ).first()
        assert relation is None

def test_add_words_invalid_ids(client, auth_headers, test_user):
    """测试批量添加不存在的单词ID"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.commit()
        
        response = client.post(f'/api/v1/vocabulary/books/{book.id}/words',
            json={
                'word_ids': [999, 1000, 1001]  # 不存在的ID
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 400001
        assert 'message' in data

def test_update_word_not_found(client, auth_headers, test_user):
    """测试更新不存在的单词"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.commit()
        
        response = client.put(f'/api/v1/vocabulary/books/{book.id}/words/999',
            json={
                'definition': '新定义'
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404

def test_unauthorized_word_access(client, auth_headers, test_user):
    """测试未授权访问单词操作"""
    # 创建另一个用户的词汇书和单词
    other_user = User(
        username='other_user2',
        email='other2@example.com',
        phone='13900139001'
    )
    book = VocabularyBook(
        name='Other Book',
        user_id=None
    )
    word = Word(text='test', definition='测试')
    
    with client.application.app_context():
        other_user.set_password('password123')
        db.session.add(other_user)
        db.session.commit()
        book.user_id = other_user.id
        db.session.add(book)
        db.session.add(word)
        db.session.commit()
        
        relation = WordRelation(
            book_id=book.id,
            word_id=word.id,
            order=1
        )
        db.session.add(relation)
        db.session.commit()
        
        # 测试未授权获取单词
        response = client.get(f'/api/v1/vocabulary/books/{book.id}/words/{word.id}',
            headers=auth_headers
        )
        assert response.status_code == 403
        
        # 测试未授权更新单词
        response = client.put(f'/api/v1/vocabulary/books/{book.id}/words/{word.id}',
            json={'definition': '新定义'},
            headers=auth_headers
        )
        assert response.status_code == 403
        
        # 测试未授权删除单词
        response = client.delete(f'/api/v1/vocabulary/books/{book.id}/words/{word.id}',
            headers=auth_headers
        )
        assert response.status_code == 403

def test_search_words(client, auth_headers, test_user):
    """测试搜索单词"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    words = [
        Word(text='apple', definition='苹果'),
        Word(text='application', definition='应用'),
        Word(text='banana', definition='香蕉')
    ]
    with client.application.app_context():
        db.session.add(book)
        for word in words:
            db.session.add(word)
        db.session.commit()
        
        for i, word in enumerate(words):
            relation = WordRelation(
                book_id=book.id,
                word_id=word.id,
                order=i+1
            )
            db.session.add(relation)
        db.session.commit()
        
        # 测试搜索单词
        response = client.get(
            f'/api/v1/vocabulary/books/{book.id}/words?keyword=app',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert len(data['data']['items']) == 2
        assert data['data']['total'] == 2
        assert any(item['text'] == 'apple' for item in data['data']['items'])
        assert any(item['text'] == 'application' for item in data['data']['items'])

def test_reorder_words(client, auth_headers, test_user):
    """测试重新排序单词"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    words = [
        Word(text='apple', definition='苹果'),
        Word(text='banana', definition='香蕉'),
        Word(text='orange', definition='橙子')
    ]
    with client.application.app_context():
        db.session.add(book)
        for word in words:
            db.session.add(word)
        db.session.commit()
        
        for i, word in enumerate(words):
            relation = WordRelation(
                book_id=book.id,
                word_id=word.id,
                order=i+1
            )
            db.session.add(relation)
        db.session.commit()
        
        # 测试重新排序
        response = client.put(
            f'/api/v1/vocabulary/books/{book.id}/words/reorder',
            json={
                'word_ids': [words[2].id, words[0].id, words[1].id]  # 新的顺序
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        
        # 验证新的顺序
        response = client.get(f'/api/v1/vocabulary/books/{book.id}/words',
            headers=auth_headers
        )
        data = response.get_json()
        assert data['data']['items'][0]['text'] == 'orange'
        assert data['data']['items'][1]['text'] == 'apple'
        assert data['data']['items'][2]['text'] == 'banana'

def test_batch_delete_words(client, auth_headers, test_user):
    """测试批量删除单词"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    words = [
        Word(text='apple', definition='苹果'),
        Word(text='banana', definition='香蕉'),
        Word(text='orange', definition='橙子')
    ]
    with client.application.app_context():
        db.session.add(book)
        for word in words:
            db.session.add(word)
        db.session.commit()
        
        for i, word in enumerate(words):
            relation = WordRelation(
                book_id=book.id,
                word_id=word.id,
                order=i+1
            )
            db.session.add(relation)
        db.session.commit()
        
        # 测试批量删除
        response = client.delete(
            f'/api/v1/vocabulary/books/{book.id}/words',
            json={
                'word_ids': [words[0].id, words[2].id]  # 删除apple和orange
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        
        # 验证删除结果
        response = client.get(f'/api/v1/vocabulary/books/{book.id}/words',
            headers=auth_headers
        )
        data = response.get_json()
        assert data['data']['total'] == 1
        assert data['data']['items'][0]['text'] == 'banana'

def test_update_book_tags(client, auth_headers, test_user):
    """测试更新词汇书标签"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id,
        tags=['old_tag']
    )
    with client.application.app_context():
        db.session.add(book)
        db.session.commit()
        
        response = client.put(
            f'/api/v1/vocabulary/books/{book.id}',
            json={
                'tags': ['new_tag1', 'new_tag2']
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert set(data['data']['tags']) == {'new_tag1', 'new_tag2'}

def test_get_book_statistics(client, auth_headers, test_user):
    """测试获取词汇书统计信息"""
    book = VocabularyBook(
        name='Test Book',
        user_id=test_user.id
    )
    words = [
        Word(
            text=f'word{i}',
            definition=f'definition{i}'
        ) for i in range(5)
    ]
    with client.application.app_context():
        db.session.add(book)
        for word in words:
            db.session.add(word)
        db.session.commit()
        
        for word in words:
            relation = WordRelation(
                book_id=book.id,
                word_id=word.id
            )
            db.session.add(relation)
        db.session.commit()
        
        response = client.get(
            f'/api/v1/vocabulary/books/{book.id}/statistics',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'data' in data
        assert data['data']['total_words'] == 5

def test_get_learning_progress(client, auth_headers, test_user):
    """测试获取词汇书学习进度"""
    # 创建测试词汇书和单词
    book = VocabularyBook(
        name='Test Book',
        description='This is a test book',
        level='intermediate',
        user_id=test_user.id
    )
    word1 = Word(text='test1', definition='测试1')
    word2 = Word(text='test2', definition='测试2')
    word3 = Word(text='test3', definition='测试3')
    db.session.add_all([book, word1, word2, word3])
    db.session.commit()

    # 添加单词到词汇书
    word_relations = [
        WordRelation(book_id=book.id, word_id=word1.id, order=1),
        WordRelation(book_id=book.id, word_id=word2.id, order=2),
        WordRelation(book_id=book.id, word_id=word3.id, order=3)
    ]
    db.session.add_all(word_relations)
    db.session.commit()

    # 添加学习记录
    records = [
        LearningRecord(
            user_id=test_user.id,
            book_id=book.id,
            word_id=word1.id,
            status='learning',
            study_time=300
        ),
        LearningRecord(
            user_id=test_user.id,
            book_id=book.id,
            word_id=word2.id,
            status='mastered',
            study_time=600
        )
    ]
    db.session.add_all(records)
    db.session.commit()

    response = client.get(f'/api/v1/vocabulary/books/{book.id}/progress',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()['data']
    assert data['total_words'] == 3
    assert data['learning_words'] == 1
    assert data['mastered_words'] == 1
    assert data['new_words'] == 1
    assert data['total_study_time'] == 900
    assert data['today_learned_count'] == 2
    assert data['consecutive_days'] == 1

def test_get_learning_progress_empty(client, auth_headers, test_user):
    """测试获取空词汇书的学习进度"""
    book = VocabularyBook(
        name='Empty Book',
        description='This is an empty book',
        level='beginner',
        user_id=test_user.id
    )
    db.session.add(book)
    db.session.commit()
    
    response = client.get(f'/api/v1/vocabulary/books/{book.id}/progress',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()['data']
    assert data['total_words'] == 0
    assert data['learning_words'] == 0
    assert data['mastered_words'] == 0
    assert data['new_words'] == 0
    assert data['total_study_time'] == 0
    assert data['today_learned_count'] == 0
    assert data['consecutive_days'] == 0

def test_get_learning_progress_consecutive_days(client, auth_headers, test_user):
    """测试连续学习天数统计"""
    book = VocabularyBook(
        name='Test Book',
        description='This is a test book',
        level='intermediate',
        user_id=test_user.id
    )
    word = Word(text='test', definition='测试')
    db.session.add_all([book, word])
    db.session.commit()

    # 添加单词到词汇书
    word_relation = WordRelation(book_id=book.id, word_id=word.id, order=1)
    db.session.add(word_relation)
    db.session.commit()

    # 创建连续3天的学习记录
    for i in range(3):
        record = LearningRecord(
            user_id=test_user.id,
            book_id=book.id,
            word_id=word.id,
            status='learning',
            study_time=300
        )
        db.session.add(record)
        db.session.flush()  # 获取 id
        # 手动设置创建时间
        record.created_at = datetime.utcnow() - timedelta(days=i)
        record.updated_at = record.created_at
    db.session.commit()

    response = client.get(f'/api/v1/vocabulary/books/{book.id}/progress',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()['data']
    assert data['consecutive_days'] == 3

def test_get_learning_progress_today(client, auth_headers, test_user):
    """测试今日学习统计"""
    book = VocabularyBook(
        name='Test Book',
        description='This is a test book',
        level='intermediate',
        user_id=test_user.id
    )
    word = Word(text='test', definition='测试')
    db.session.add_all([book, word])
    db.session.commit()

    # 添加单词到词汇书
    word_relation = WordRelation(book_id=book.id, word_id=word.id, order=1)
    db.session.add(word_relation)
    db.session.commit()

    # 创建今日和昨日的学习记录
    today_record = LearningRecord(
        user_id=test_user.id,
        book_id=book.id,
        word_id=word.id,
        status='learning',
        study_time=300
    )
    db.session.add(today_record)
    db.session.flush()
    # 手动设置创建时间为今天
    today_record.created_at = datetime.utcnow()
    today_record.updated_at = today_record.created_at

    yesterday_record = LearningRecord(
        user_id=test_user.id,
        book_id=book.id,
        word_id=word.id,
        status='learning',
        study_time=300
    )
    db.session.add(yesterday_record)
    db.session.flush()
    # 手动设置创建时间为昨天
    yesterday_record.created_at = datetime.utcnow() - timedelta(days=1)
    yesterday_record.updated_at = yesterday_record.created_at
    
    db.session.commit()

    response = client.get(f'/api/v1/vocabulary/books/{book.id}/progress',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()['data']
    assert data['today_learned_count'] == 1

def test_get_learning_progress_unauthorized(client, auth_headers, test_user):
    """测试未授权访问词汇书学习进度"""
    # 创建另一个用户的词汇书
    other_user = User(
        username='other_user',
        email='other@example.com',
        phone='13900139000'
    )
    other_user.set_password('password123')
    db.session.add(other_user)
    db.session.commit()

    book = VocabularyBook(
        name='Other Book',
        description='This is another user\'s book',
        level='intermediate',
        user_id=other_user.id
    )
    db.session.add(book)
    db.session.commit()

    response = client.get(f'/api/v1/vocabulary/books/{book.id}/progress',
        headers=auth_headers
    )
    
    assert response.status_code == 403
    data = response.get_json()
    assert data['code'] == 403001
    assert '无权访问此词汇书' in data['message'] 