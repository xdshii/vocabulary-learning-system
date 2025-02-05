import pytest
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.assessment import UserLevelAssessment
from app.models.learning import LearningRecord
from app.services.recommendation_service import RecommendationService

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
    
    # 创建评估记录
    assessment = UserLevelAssessment(
        user_id=user.id,
        book_id=book.id,
        level='intermediate',
        status='completed',
        level_score=80,
        total_questions=20,
        correct_answers=16,
        assessment_date=datetime.utcnow()
    )
    db.session.add(assessment)
    db.session.flush()
    
    yield {'user': user, 'book': book, 'words': words, 'assessment': assessment}
    
    # 清理数据
    db.session.query(LearningRecord).delete()
    db.session.query(UserLevelAssessment).delete()
    db.session.query(WordRelation).delete()
    db.session.query(Word).delete()
    db.session.query(VocabularyBook).delete()
    db.session.query(User).delete()
    db.session.commit()

def test_get_recommended_words(init_database, app):
    """测试获取推荐单词"""
    with app.app_context():
        data = init_database
        
        # 创建一个已学习的单词记录
        learning_record = LearningRecord(
            user_id=data['user'].id,
            book_id=data['book'].id,
            word_id=data['words'][0].id,
            status='learning',
            review_count=1
        )
        db.session.add(learning_record)
        db.session.commit()
        
        # 获取推荐单词
        words = RecommendationService.get_recommended_words(
            user_id=data['user'].id,
            book_id=data['book'].id,
            limit=3
        )
        
        assert len(words) == 3
        # 确保已学习的单词不在推荐列表中
        assert all(w['id'] != data['words'][0].id for w in words)

def test_get_recommended_words_no_assessment(init_database, app):
    """测试无评估记录时获取推荐单词"""
    with app.app_context():
        data = init_database
        
        # 删除评估记录
        assessment = UserLevelAssessment.query.get(data['assessment'].id)
        if assessment:
            db.session.delete(assessment)
            db.session.commit()
        
        # 尝试获取推荐单词
        with pytest.raises(ValueError) as excinfo:
            RecommendationService.get_recommended_words(
                user_id=data['user'].id,
                book_id=data['book'].id
            )
        assert 'No assessment found' in str(excinfo.value)

def test_get_review_words(init_database, app):
    """测试获取需要复习的单词"""
    with app.app_context():
        data = init_database
        
        # 创建需要复习的单词记录
        learning_record = LearningRecord(
            user_id=data['user'].id,
            book_id=data['book'].id,
            word_id=data['words'][0].id,
            status='learning',
            review_count=2,
            next_review_time=datetime.utcnow() - timedelta(hours=1)
        )
        db.session.add(learning_record)
        db.session.commit()
        
        # 获取需要复习的单词
        words = RecommendationService.get_review_words(
            user_id=data['user'].id,
            book_id=data['book'].id
        )
        
        assert len(words) == 1
        assert words[0]['id'] == data['words'][0].id
        assert words[0]['review_count'] == 2

def test_get_daily_schedule(init_database, app):
    """测试获取每日学习计划"""
    with app.app_context():
        data = init_database
        
        # 创建今日学习记录
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        learning_record = LearningRecord(
            user_id=data['user'].id,
            book_id=data['book'].id,
            word_id=data['words'][0].id,
            status='learning',
            review_count=1
        )
        db.session.add(learning_record)
        
        # 创建需要复习的记录
        review_record = LearningRecord(
            user_id=data['user'].id,
            book_id=data['book'].id,
            word_id=data['words'][1].id,
            status='learning',
            review_count=2,
            next_review_time=datetime.utcnow() - timedelta(hours=1)
        )
        db.session.add(review_record)
        db.session.commit()
        
        # 获取每日计划
        schedule = RecommendationService.get_daily_schedule(
            user_id=data['user'].id,
            book_id=data['book'].id
        )
        
        assert schedule['book_name'] == 'Test Book'
        assert schedule['total_words'] == 4
        assert schedule['review_words'] == 1
        assert schedule['learned_today'] == 2
        assert schedule['remaining_today'] == 18 