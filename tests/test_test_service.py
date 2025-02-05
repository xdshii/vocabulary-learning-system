import pytest
from datetime import datetime
from app import db
from app.models.user import User
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.test import Test, TestQuestion
from app.models.learning import LearningRecord
from app.services.test_service import TestService

@pytest.fixture
def app():
    """创建测试应用"""
    from app import create_app
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def init_database(app):
    """初始化测试数据库"""
    # 创建用户
    user = User(
        username='test_user',
        email='test@example.com',
        phone='13800138000'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.flush()
    
    # 创建词书
    book = VocabularyBook(
        name='Test Book',
        level='intermediate',
        user_id=user.id,
        total_words=4
    )
    db.session.add(book)
    db.session.flush()
    
    # 创建单词
    words = [
        Word(text='apple', definition='苹果'),
        Word(text='banana', definition='香蕉'),
        Word(text='computer', definition='电脑'),
        Word(text='algorithm', definition='算法')
    ]
    for word in words:
        db.session.add(word)
    db.session.flush()
    
    # 创建单词和词书的关联
    word_relations = [
        WordRelation(word_id=word.id, book_id=book.id, order=i+1)
        for i, word in enumerate(words)
    ]
    for relation in word_relations:
        db.session.add(relation)
    db.session.flush()
    
    yield {'user': user, 'book': book, 'words': words}
    
    # 清理数据
    db.session.query(TestQuestion).delete()
    db.session.query(Test).delete()
    db.session.query(WordRelation).delete()
    db.session.query(Word).delete()
    db.session.query(VocabularyBook).delete()
    db.session.query(User).delete()
    db.session.commit()

def test_create_test(init_database, app):
    """测试创建测试"""
    with app.app_context():
        data = init_database
        
        # 创建选择题测试
        result = TestService.create_test(
            user_id=data['user'].id,
            book_id=data['book'].id,
            test_type='multiple_choice'
        )
        
        assert result['id'] is not None
        assert len(result['questions']) == 4
        for question in result['questions']:
            assert len(question['options']) == 4

def test_create_test_invalid_type(init_database, app):
    """测试创建无效类型的测试"""
    with app.app_context():
        data = init_database
        
        with pytest.raises(ValueError) as excinfo:
            TestService.create_test(
                user_id=data['user'].id,
                book_id=data['book'].id,
                test_type='invalid_type'
            )
        assert 'Invalid test type' in str(excinfo.value)

def test_submit_test(init_database, app):
    """测试提交测试答案"""
    with app.app_context():
        data = init_database
        
        # 创建测试
        test_result = TestService.create_test(
            user_id=data['user'].id,
            book_id=data['book'].id,
            test_type='multiple_choice'
        )
        
        # 提交答案
        answers = []
        for question in test_result['questions']:
            answers.append({
                'question_id': question['id'],
                'answer': question['correct_answer']
            })
        
        result = TestService.submit_test(
            test_id=test_result['id'],
            answers=answers
        )
        
        assert result['score'] == 100
        assert result['total_questions'] == 4
        assert result['correct_answers'] == 4

def test_submit_test_already_completed(init_database, app):
    """测试提交已完成的测试"""
    with app.app_context():
        data = init_database
        
        # 创建并完成测试
        test_result = TestService.create_test(
            user_id=data['user'].id,
            book_id=data['book'].id,
            test_type='multiple_choice'
        )
        
        answers = []
        for question in test_result['questions']:
            answers.append({
                'question_id': question['id'],
                'answer': question['correct_answer']
            })
        
        TestService.submit_test(
            test_id=test_result['id'],
            answers=answers
        )
        
        # 尝试再次提交
        with pytest.raises(ValueError) as excinfo:
            TestService.submit_test(
                test_id=test_result['id'],
                answers=answers
            )
        assert 'Test already completed' in str(excinfo.value)

def test_get_test_results(init_database, app):
    """测试获取测试结果"""
    with app.app_context():
        data = init_database
        
        # 创建并完成测试
        test_result = TestService.create_test(
            user_id=data['user'].id,
            book_id=data['book'].id,
            test_type='multiple_choice'
        )
        
        answers = []
        for question in test_result['questions']:
            answers.append({
                'question_id': question['id'],
                'answer': question['correct_answer']
            })
        
        TestService.submit_test(
            test_id=test_result['id'],
            answers=answers
        )
        
        # 获取测试结果
        results = TestService.get_test_results(data['user'].id)
        assert len(results) == 1
        assert results[0]['id'] == test_result['id']
        assert results[0]['score'] == 100

def test_get_test_details(init_database, app):
    """测试获取测试详情"""
    with app.app_context():
        data = init_database
        
        # 创建测试
        test_result = TestService.create_test(
            user_id=data['user'].id,
            book_id=data['book'].id,
            test_type='multiple_choice'
        )
        
        # 获取测试详情
        details = TestService.get_test_details(test_result['id'])
        assert details['test']['id'] == test_result['id']
        assert len(details['questions']) == 4

def test_get_learning_progress(init_database, app):
    """测试获取学习进度"""
    with app.app_context():
        data = init_database
        
        # 创建学习记录
        learning_record = LearningRecord(
            user_id=data['user'].id,
            book_id=data['book'].id,
            word_id=data['words'][0].id,
            status='mastered',
            review_count=5
        )
        db.session.add(learning_record)
        db.session.commit()
        
        # 获取学习进度
        progress = TestService.get_learning_progress(
            user_id=data['user'].id,
            book_id=data['book'].id
        )
        
        assert progress['total_words'] == 4
        assert progress['mastered_words'] == 1
        assert progress['learning_words'] == 0
        assert progress['new_words'] == 3
        assert progress['progress'] == 25.0 