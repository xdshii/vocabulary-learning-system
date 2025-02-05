import pytest
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.assessment import UserLevelAssessment, AssessmentQuestion
from app.models.learning import LearningRecord
from app.services.assessment_service import AssessmentService
import werkzeug.exceptions

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
    
    yield {'user': user, 'book': book, 'words': words}
    
    # 清理数据
    db.session.query(AssessmentQuestion).delete()
    db.session.query(UserLevelAssessment).delete()
    db.session.query(WordRelation).delete()
    db.session.query(Word).delete()
    db.session.query(VocabularyBook).delete()
    db.session.query(User).delete()
    db.session.commit()

def test_start_assessment(init_database, app):
    """测试开始评估"""
    with app.app_context():
        data = init_database
        
        # 开始评估
        assessment, questions = AssessmentService.start_assessment(
            user_id=data['user'].id,
            book_id=data['book'].id,
            question_count=4
        )
        
        # 验证评估记录
        assert isinstance(assessment, UserLevelAssessment)
        assert assessment.user_id == data['user'].id
        assert assessment.book_id == data['book'].id
        assert assessment.status == 'in_progress'
        
        # 验证题目
        assert len(questions) == 4
        for question in questions:
            assert isinstance(question, AssessmentQuestion)
            assert question.assessment_id == assessment.id
            assert question.word_id in [w.id for w in data['words']]
            assert question.question_type == 'choice'
            assert len(question.options) == 4
            assert question.correct_answer in [w.definition for w in data['words']]

def test_submit_answer(init_database, app):
    """测试提交答案"""
    with app.app_context():
        data = init_database
        
        # 开始评估
        assessment, questions = AssessmentService.start_assessment(
            user_id=data['user'].id,
            book_id=data['book'].id,
            question_count=4
        )
        
        # 提交正确答案
        question = questions[0]
        updated_question = AssessmentService.submit_answer(
            assessment_id=assessment.id,
            question_id=question.id,
            answer=question.correct_answer
        )
        
        # 验证答案
        assert updated_question.user_answer == question.correct_answer
        assert updated_question.is_correct is True
        assert updated_question.answered_at is not None
        
        # 提交错误答案
        question = questions[1]
        wrong_answer = 'wrong answer'
        updated_question = AssessmentService.submit_answer(
            assessment_id=assessment.id,
            question_id=question.id,
            answer=wrong_answer
        )
        
        # 验证答案
        assert updated_question.user_answer == wrong_answer
        assert updated_question.is_correct is False
        assert updated_question.answered_at is not None

def test_complete_assessment(init_database, app):
    """测试完成评估"""
    with app.app_context():
        data = init_database
        
        # 开始评估
        assessment, questions = AssessmentService.start_assessment(
            user_id=data['user'].id,
            book_id=data['book'].id,
            question_count=4
        )
        
        # 提交所有答案
        for i, question in enumerate(questions):
            AssessmentService.submit_answer(
                assessment_id=assessment.id,
                question_id=question.id,
                answer=question.correct_answer if i < 2 else 'wrong answer'
            )
        
        # 完成评估
        result = AssessmentService.complete_assessment(assessment.id)
        
        # 验证结果
        assert isinstance(result, dict)
        assert 'score' in result
        assert result['score'] == 50.0  # 4题中答对2题
        assert result['correct_count'] == 2
        assert result['total_questions'] == 4
        assert 'assessment_date' in result
        
        # 验证评估记录
        assessment = UserLevelAssessment.query.get(assessment.id)
        assert assessment.status == 'completed'
        assert assessment.level_score == 50.0
        assert assessment.total_questions == 4
        assert assessment.correct_answers == 2
        
        # 验证学习记录
        learning_records = LearningRecord.query.filter_by(
            user_id=data['user'].id,
            book_id=data['book'].id
        ).all()
        assert len(learning_records) == 2  # 只为答错的题目创建学习记录

def test_get_assessment_history(init_database, app):
    """测试获取评估历史"""
    with app.app_context():
        data = init_database
        
        # 创建多个评估记录
        for i in range(3):
            assessment, questions = AssessmentService.start_assessment(
                user_id=data['user'].id,
                book_id=data['book'].id,
                question_count=4
            )
            
            # 提交答案并完成评估
            for j, question in enumerate(questions):
                AssessmentService.submit_answer(
                    assessment_id=assessment.id,
                    question_id=question.id,
                    answer=question.correct_answer if j < 2 else 'wrong answer'
                )
            AssessmentService.complete_assessment(assessment.id)
        
        # 获取评估历史
        history = AssessmentService.get_assessment_history(data['user'].id)
        
        # 验证历史记录
        assert isinstance(history, list)
        assert len(history) == 3
        for record in history:
            assert isinstance(record, dict)
            assert record['user_id'] == data['user'].id
            assert record['book_id'] == data['book'].id
            assert record['level_score'] == 50.0
            assert record['total_questions'] == 4
            assert record['correct_answers'] == 2
            assert record['status'] == 'completed'
            assert 'assessment_date' in record

def test_start_assessment_no_words(init_database, app):
    """测试开始评估时没有单词的情况"""
    with app.app_context():
        data = init_database
        
        # 创建一个空的词书
        empty_book = VocabularyBook(
            name='Empty Book',
            level='beginner',
            user_id=data['user'].id
        )
        db.session.add(empty_book)
        db.session.flush()
        
        # 尝试开始评估
        with pytest.raises(ValueError) as excinfo:
            AssessmentService.start_assessment(
                user_id=data['user'].id,
                book_id=empty_book.id,
                question_count=4
            )
        assert str(excinfo.value) == 'No words found in the book'

def test_submit_answer_invalid_question(init_database, app):
    """测试提交答案时题目无效的情况"""
    with app.app_context():
        data = init_database
        
        # 开始评估
        assessment, questions = AssessmentService.start_assessment(
            user_id=data['user'].id,
            book_id=data['book'].id,
            question_count=4
        )
        
        # 尝试提交答案给不存在的题目
        with pytest.raises(werkzeug.exceptions.NotFound):
            AssessmentService.submit_answer(
                assessment_id=assessment.id,
                question_id=9999,
                answer='any answer'
            )

def test_complete_assessment_already_completed(init_database, app):
    """测试完成已完成的评估"""
    with app.app_context():
        data = init_database
        
        # 开始并完成评估
        assessment, questions = AssessmentService.start_assessment(
            user_id=data['user'].id,
            book_id=data['book'].id,
            question_count=4
        )
        
        for question in questions:
            AssessmentService.submit_answer(
                assessment_id=assessment.id,
                question_id=question.id,
                answer=question.correct_answer
            )
        AssessmentService.complete_assessment(assessment.id)
        
        # 尝试再次完成评估
        with pytest.raises(ValueError) as excinfo:
            AssessmentService.complete_assessment(assessment.id)
        assert str(excinfo.value) == 'Assessment already completed' 