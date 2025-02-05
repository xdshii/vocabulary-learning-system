import pytest
from datetime import datetime, timedelta
from app import db, create_app
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.learning import LearningRecord
from app.models.assessment import UserLevelAssessment, AssessmentQuestion
from app.models.test import Test, TestRecord, TestQuestion, TestAnswer
from app.models.user import User
from app.services.analysis_service import AnalysisService

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        db.create_all()  # 创建所有表
        yield app
        db.session.remove()
        db.drop_all()  # 删除所有表

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

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
        user_id=user.id
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
    
    # 创建评估记录
    assessment = UserLevelAssessment(
        user_id=user.id,
        book_id=book.id,
        level='intermediate',
        score=75
    )
    db.session.add(assessment)
    db.session.flush()
    
    # 创建评估题目
    questions = [
        AssessmentQuestion(
            assessment_id=assessment.id,
            word_id=words[0].id,
            question_type='multiple_choice',
            difficulty='easy',
            content='What is apple?',
            options=['苹果', '香蕉', '电脑', '算法'],
            correct_answer='苹果',
            user_answer='苹果',
            is_correct=True
        ),
        AssessmentQuestion(
            assessment_id=assessment.id,
            word_id=words[1].id,
            question_type='multiple_choice',
            difficulty='easy',
            content='What is banana?',
            options=['苹果', '香蕉', '电脑', '算法'],
            correct_answer='香蕉',
            user_answer='香蕉',
            is_correct=True
        ),
        AssessmentQuestion(
            assessment_id=assessment.id,
            word_id=words[2].id,
            question_type='multiple_choice',
            difficulty='medium',
            content='What is computer?',
            options=['苹果', '香蕉', '电脑', '算法'],
            correct_answer='电脑',
            user_answer='香蕉',
            is_correct=False
        ),
        AssessmentQuestion(
            assessment_id=assessment.id,
            word_id=words[3].id,
            question_type='multiple_choice',
            difficulty='hard',
            content='What is algorithm?',
            options=['苹果', '香蕉', '电脑', '算法'],
            correct_answer='算法',
            user_answer='电脑',
            is_correct=False
        )
    ]
    db.session.bulk_save_objects(questions)
    db.session.flush()
    
    yield user
    
    # 清理数据
    db.session.query(AssessmentQuestion).delete()
    db.session.query(UserLevelAssessment).delete()
    db.session.query(Word).delete()
    db.session.query(VocabularyBook).delete()
    db.session.query(User).delete()
    db.session.commit()

@pytest.fixture(autouse=True)
def cleanup_database(app):
    """在每个测试前清理数据库"""
    with app.app_context():
        # 删除所有记录
        AssessmentQuestion.query.delete()
        UserLevelAssessment.query.delete()
        Word.query.delete()
        db.session.commit()

def test_analyze_assessment(app):
    """测试分析评估结果"""
    with app.app_context():
        # 创建测试单词
        words = [
            Word(text='test1', definition='测试1'),
            Word(text='test2', definition='测试2'),
            Word(text='test3', definition='测试3'),
            Word(text='test4', definition='测试4'),
            Word(text='test5', definition='测试5')
        ]
        for word in words:
            db.session.add(word)
        db.session.commit()
        
        # 创建评估记录
        assessment = UserLevelAssessment(
            user_id=1,
            book_id=1
        )
        db.session.add(assessment)
        db.session.commit()
        
        # 创建评估题目
        questions = [
            AssessmentQuestion(
                assessment=assessment,
                word=words[0],
                question_type='choice',
                options=['测试1', '测试2', '测试3', '测试4'],
                correct_answer='测试1',
                user_answer='测试1',
                is_correct=True
            ),
            AssessmentQuestion(
                assessment=assessment,
                word=words[1],
                question_type='choice',
                options=['测试1', '测试2', '测试3', '测试4'],
                correct_answer='测试2',
                user_answer='测试2',
                is_correct=True
            ),
            AssessmentQuestion(
                assessment=assessment,
                word=words[2],
                question_type='choice',
                options=['测试1', '测试2', '测试3', '测试4'],
                correct_answer='测试3',
                user_answer='测试1',
                is_correct=False
            ),
            AssessmentQuestion(
                assessment=assessment,
                word=words[3],
                question_type='choice',
                options=['测试1', '测试2', '测试3', '测试4'],
                correct_answer='测试4',
                user_answer='测试2',
                is_correct=False
            ),
            AssessmentQuestion(
                assessment=assessment,
                word=words[4],
                question_type='choice',
                options=['测试1', '测试2', '测试3', '测试4'],
                correct_answer='测试5',
                user_answer='测试5',
                is_correct=True
            )
        ]
        for question in questions:
            db.session.add(question)
        db.session.commit()
        
        # 分析评估结果
        result = AnalysisService.analyze_assessment(assessment.id)
        
        # 验证结果
        assert 'accuracy_rate' in result
        assert result['accuracy_rate'] == 0.6  # 3/5 = 0.6
        assert 'difficulty_stats' in result
        assert 'weak_words' in result
        assert len(result['weak_words']) == 2  # 两个错误的单词
        assert result['weak_words'][0]['text'] in ['test3', 'test4']
        assert result['weak_words'][1]['text'] in ['test3', 'test4']

def test_analyze_assessment_not_found(app):
    """测试分析不存在的评估"""
    with app.app_context():
        with pytest.raises(ValueError) as excinfo:
            AnalysisService.analyze_assessment(999)
        assert str(excinfo.value) == 'Assessment not found'

def test_analyze_learning_progress(app):
    """测试分析学习进度"""
    with app.app_context():
        # 创建测试单词
        words = [
            Word(text='test1', definition='测试1'),
            Word(text='test2', definition='测试2'),
            Word(text='test3', definition='测试3'),
            Word(text='test4', definition='测试4'),
            Word(text='test5', definition='测试5')
        ]
        for word in words:
            db.session.add(word)
        db.session.commit()
        
        # 创建评估记录
        assessment = UserLevelAssessment(
            user_id=1,
            book_id=1,
            level='intermediate',
            score=75
        )
        db.session.add(assessment)
        db.session.commit()
        
        # 创建评估题目
        questions = [
            AssessmentQuestion(
                assessment=assessment,
                word=words[0],
                question_type='multiple_choice',
                options=['测试1', '测试2', '测试3', '测试4'],
                correct_answer='测试1',
                user_answer='测试1',
                is_correct=True
            ),
            AssessmentQuestion(
                assessment=assessment,
                word=words[1],
                question_type='multiple_choice',
                options=['测试1', '测试2', '测试3', '测试4'],
                correct_answer='测试2',
                user_answer='测试2',
                is_correct=True
            ),
            AssessmentQuestion(
                assessment=assessment,
                word=words[2],
                question_type='multiple_choice',
                options=['测试1', '测试2', '测试3', '测试4'],
                correct_answer='测试3',
                user_answer='测试1',
                is_correct=False
            ),
            AssessmentQuestion(
                assessment=assessment,
                word=words[3],
                question_type='multiple_choice',
                options=['测试1', '测试2', '测试3', '测试4'],
                correct_answer='测试4',
                user_answer='测试2',
                is_correct=False
            )
        ]
        for question in questions:
            db.session.add(question)
        db.session.commit()
        
        # 分析学习进度
        result = AnalysisService.analyze_learning_progress(assessment.id)
        
        # 验证结果
        assert 'accuracy_rate' in result
        assert result['accuracy_rate'] == 0.5  # 2/4 = 0.5
        assert 'weak_words' in result
        assert len(result['weak_words']) == 2  # 两个错误的单词
        assert result['weak_words'][0]['text'] in ['test3', 'test4']
        assert result['weak_words'][1]['text'] in ['test3', 'test4']

def test_analyze_test_history(app):
    """测试分析测试历史"""
    with app.app_context():
        # 创建测试单词
        words = [
            Word(text='test6', definition='测试6'),
            Word(text='test7', definition='测试7'),
            Word(text='test8', definition='测试8'),
            Word(text='test9', definition='测试9')
        ]
        for word in words:
            db.session.add(word)
        db.session.commit()
        
        # 创建评估记录
        assessment = UserLevelAssessment(
            user_id=1,
            book_id=1,
            level='intermediate',
            score=75
        )
        db.session.add(assessment)
        db.session.commit()
        
        # 创建评估题目
        questions = [
            AssessmentQuestion(
                assessment=assessment,
                word=words[0],
                question_type='multiple_choice',
                options=['测试6', '测试7', '测试8', '测试9'],
                correct_answer='测试6',
                user_answer='测试6',
                is_correct=True
            ),
            AssessmentQuestion(
                assessment=assessment,
                word=words[1],
                question_type='multiple_choice',
                options=['测试6', '测试7', '测试8', '测试9'],
                correct_answer='测试7',
                user_answer='测试7',
                is_correct=True
            ),
            AssessmentQuestion(
                assessment=assessment,
                word=words[2],
                question_type='multiple_choice',
                options=['测试6', '测试7', '测试8', '测试9'],
                correct_answer='测试8',
                user_answer='测试6',
                is_correct=False
            ),
            AssessmentQuestion(
                assessment=assessment,
                word=words[3],
                question_type='multiple_choice',
                options=['测试6', '测试7', '测试8', '测试9'],
                correct_answer='测试9',
                user_answer='测试7',
                is_correct=False
            )
        ]
        for question in questions:
            db.session.add(question)
        db.session.commit()
        
        # 分析测试历史
        result = AnalysisService.analyze_test_history(assessment.id)
        
        # 验证结果
        assert 'accuracy_rate' in result
        assert result['accuracy_rate'] == 0.5  # 2/4 = 0.5
        assert 'weak_words' in result
        assert len(result['weak_words']) == 2  # 两个错误的单词
        assert result['weak_words'][0]['text'] in ['test8', 'test9']
        assert result['weak_words'][1]['text'] in ['test8', 'test9'] 