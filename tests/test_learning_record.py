import pytest
from datetime import datetime, timedelta
from app import db
from app.models.learning import LearningRecord
from app.models.user import User
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word

@pytest.fixture
def setup_test_data(app):
    """创建测试数据"""
    with app.app_context():
        # 创建测试用户,使用时间戳确保邮箱唯一
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        user = User(
            username=f'test_user_{timestamp}',
            email=f'test_{timestamp}@example.com'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()  # 获取user.id
        
        # 创建测试词书
        book = VocabularyBook(
            name='Test Book',
            description='Test Description',
            user_id=user.id  # 使用flush后的user.id
        )
        db.session.add(book)
        db.session.flush()  # 获取book.id
        
        # 创建测试单词
        word = Word(
            text='test',
            definition='测试'
        )
        db.session.add(word)
        db.session.flush()  # 获取word.id
        
        # 创建单词和词书的关联
        relation = WordRelation(
            word_id=word.id,
            book_id=book.id,
            order=1
        )
        db.session.add(relation)
        db.session.commit()
        
        return {
            'user': user,
            'book': book,
            'word': word
        }

def test_record_creation(setup_test_data, app):
    """测试学习记录创建"""
    with app.app_context():
        data = setup_test_data
        
        # 创建学习记录
        record = LearningRecord(
            user_id=data['user'].id,
            book_id=data['book'].id,
            word_id=data['word'].id,
            status='learning'
        )
        db.session.add(record)
        db.session.commit()
        
        # 验证记录
        assert record.id is not None
        assert record.user_id == data['user'].id
        assert record.book_id == data['book'].id
        assert record.word_id == data['word'].id
        assert record.status == 'learning'
        assert record.created_at is not None

def test_status_update(setup_test_data, app):
    """测试状态更新"""
    with app.app_context():
        data = setup_test_data
        
        # 创建记录
        record = LearningRecord(
            user_id=data['user'].id,
            book_id=data['book'].id,
            word_id=data['word'].id,
            status='learning'
        )
        db.session.add(record)
        db.session.commit()
        
        # 更新状态
        record.status = 'mastered'
        record.mastered_at = datetime.utcnow()
        db.session.commit()
        
        # 验证更新
        updated_record = LearningRecord.query.get(record.id)
        assert updated_record.status == 'mastered'
        assert updated_record.mastered_at is not None

def test_review_plan(setup_test_data, app):
    """测试复习计划"""
    with app.app_context():
        data = setup_test_data
        
        # 创建记录
        record = LearningRecord(
            user_id=data['user'].id,
            book_id=data['book'].id,
            word_id=data['word'].id,
            status='learning',
            next_review_time=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(record)
        db.session.commit()
        
        # 验证复习时间
        assert record.next_review_time > datetime.utcnow()
        
        # 更新复习时间
        record.update_review_time()
        assert record.next_review_time > datetime.utcnow() + timedelta(days=1)

def test_learning_statistics(setup_test_data, app):
    """测试学习统计"""
    with app.app_context():
        data = setup_test_data
        
        # 创建多个不同状态的记录
        records = [
            LearningRecord(
                user_id=data['user'].id,
                book_id=data['book'].id,
                word_id=data['word'].id,
                status=status
            )
            for status in ['learning', 'mastered', 'learning', 'mastered']
        ]
        for record in records:
            db.session.add(record)
        db.session.commit()
        
        # 统计测试
        stats = LearningRecord.get_statistics(data['user'].id, data['book'].id)
        assert stats['total'] == 4
        assert stats['mastered'] == 2
        assert stats['learning'] == 2

def test_record_validation(setup_test_data, app):
    """测试记录验证"""
    with app.app_context():
        data = setup_test_data
        
        # 测试无效状态
        with pytest.raises(ValueError):
            record = LearningRecord(
                user_id=data['user'].id,
                book_id=data['book'].id,
                word_id=data['word'].id,
                status='invalid_status'
            )
            db.session.add(record)
            db.session.commit()

def test_record_deletion(setup_test_data, app):
    """测试记录删除"""
    with app.app_context():
        data = setup_test_data
        
        # 创建记录
        record = LearningRecord(
            user_id=data['user'].id,
            book_id=data['book'].id,
            word_id=data['word'].id,
            status='learning'
        )
        db.session.add(record)
        db.session.commit()
        
        # 删除记录
        db.session.delete(record)
        db.session.commit()
        
        # 验证删除
        deleted_record = LearningRecord.query.get(record.id)
        assert deleted_record is None 