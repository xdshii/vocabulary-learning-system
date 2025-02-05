import os
import sys
import math

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.learning import LearningRecord
from app.models.learning_plan import LearningPlan
from app.services.learning_plan_service import LearningPlanService
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
        user_id=user.id,
        total_words=100
    )
    db.session.add(book)
    db.session.flush()
    
    # 创建单词
    words = [
        Word(text=f'word{i}', definition=f'definition{i}')
        for i in range(100)
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
    
    # 创建部分学习记录（已掌握20个单词）
    for word in words[:20]:
        record = LearningRecord(
            user_id=user.id,
            book_id=book.id,
            word_id=word.id,
            status='mastered'
        )
        db.session.add(record)
    db.session.flush()
    
    yield {'user': user, 'book': book, 'words': words}
    
    # 清理数据
    db.session.query(LearningRecord).delete()
    db.session.query(LearningPlan).delete()
    db.session.query(WordRelation).delete()
    db.session.query(Word).delete()
    db.session.query(VocabularyBook).delete()
    db.session.query(User).delete()
    db.session.commit()

def test_create_plan(init_database, app):
    """测试创建学习计划"""
    with app.app_context():
        data = init_database
        
        # 创建计划
        result = LearningPlanService.create_plan(
            user_id=data['user'].id,
            book_id=data['book'].id,
            daily_words=20
        )
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['user_id'] == data['user'].id
        assert result['book_id'] == data['book'].id
        assert result['daily_words'] == 20
        assert 'start_date' in result
        assert 'end_date' in result
        assert 'created_at' in result
        
        # 验证计划记录
        plan = LearningPlan.query.get(result['id'])
        assert plan is not None
        assert plan.user_id == data['user'].id
        assert plan.book_id == data['book'].id
        assert plan.daily_words == 20
        
        # 计算目标日期（80个未掌握的单词，每天20个，需要4天）
        expected_days = 4
        expected_date = datetime.utcnow().date() + timedelta(days=expected_days)
        assert plan.end_date == expected_date

def test_create_plan_with_target_date(init_database, app):
    """测试创建带目标日期的学习计划"""
    with app.app_context():
        data = init_database
        
        # 设置目标日期为30天后
        target_date = (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        # 创建计划
        result = LearningPlanService.create_plan(
            user_id=data['user'].id,
            book_id=data['book'].id,
            target_date=target_date
        )
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['user_id'] == data['user'].id
        assert result['book_id'] == data['book'].id
        assert 'daily_words' in result
        assert result['end_date'] == target_date
        
        # 验证每日单词数（80个未掌握的单词，30天完成，每天约3个）
        plan = LearningPlan.query.get(result['id'])
        assert plan.daily_words == math.ceil(80 / 30)  # 向上取整

def test_update_plan(init_database, app):
    """测试更新学习计划"""
    with app.app_context():
        data = init_database
        
        # 先创建计划
        plan_result = LearningPlanService.create_plan(
            user_id=data['user'].id,
            book_id=data['book'].id,
            daily_words=20
        )
        
        # 更新每日单词数
        result = LearningPlanService.update_plan(
            plan_id=plan_result['id'],
            daily_words=30
        )
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['daily_words'] == 30
        assert 'end_date' in result
        
        # 验证计划记录
        plan = LearningPlan.query.get(plan_result['id'])
        assert plan.daily_words == 30
        
        # 计算新的目标日期（80个未掌握的单词，每天30个，需要3天）
        expected_days = math.ceil(80 / 30)  # 向上取整
        expected_date = datetime.utcnow().date() + timedelta(days=expected_days)
        assert plan.end_date == expected_date

def test_update_plan_with_target_date(init_database, app):
    """测试更新学习计划的目标日期"""
    with app.app_context():
        data = init_database
        
        # 先创建计划
        plan_result = LearningPlanService.create_plan(
            user_id=data['user'].id,
            book_id=data['book'].id,
            daily_words=20
        )
        
        # 更新目标日期为60天后
        target_date = (datetime.utcnow() + timedelta(days=60)).strftime('%Y-%m-%d')
        result = LearningPlanService.update_plan(
            plan_id=plan_result['id'],
            target_date=target_date
        )
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['end_date'] == target_date
        assert 'daily_words' in result
        
        # 验证计划记录（80个未掌握的单词，60天完成，每天约2个）
        plan = LearningPlan.query.get(plan_result['id'])
        assert plan.daily_words == math.ceil(80 / 60)  # 向上取整

def test_get_plan(init_database, app):
    """测试获取学习计划"""
    with app.app_context():
        data = init_database
        
        # 先创建计划
        plan_result = LearningPlanService.create_plan(
            user_id=data['user'].id,
            book_id=data['book'].id,
            daily_words=20
        )
        
        # 获取计划详情
        result = LearningPlanService.get_plan(plan_result['id'])
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['user_id'] == data['user'].id
        assert result['book_id'] == data['book'].id
        assert result['book_name'] == data['book'].name
        assert result['daily_words'] == 20
        assert result['total_words'] == 100
        assert result['mastered_words'] == 20
        assert result['remaining_words'] == 80
        assert 'days_remaining' in result
        assert 'start_date' in result
        assert 'end_date' in result
        assert 'created_at' in result
        assert 'updated_at' in result

def test_create_plan_already_exists(init_database, app):
    """测试创建已存在的学习计划"""
    with app.app_context():
        data = init_database
        
        # 先创建一个计划
        LearningPlanService.create_plan(
            user_id=data['user'].id,
            book_id=data['book'].id,
            daily_words=20
        )
        
        # 尝试再次创建
        with pytest.raises(ValueError) as excinfo:
            LearningPlanService.create_plan(
                user_id=data['user'].id,
                book_id=data['book'].id,
                daily_words=30
            )
        assert str(excinfo.value) == 'Learning plan already exists'

def test_update_plan_invalid_target_date(init_database, app):
    """测试更新计划时使用无效的目标日期"""
    with app.app_context():
        data = init_database
        
        # 先创建计划
        plan_result = LearningPlanService.create_plan(
            user_id=data['user'].id,
            book_id=data['book'].id,
            daily_words=20
        )
        
        # 尝试更新为过去的日期
        past_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        with pytest.raises(ValueError) as excinfo:
            LearningPlanService.update_plan(
                plan_id=plan_result['id'],
                target_date=past_date
            )
        assert str(excinfo.value) == 'Target date must be in the future'

def test_get_plan_not_found(init_database, app):
    """测试获取不存在的学习计划"""
    with app.app_context():
        with pytest.raises(werkzeug.exceptions.NotFound):
            LearningPlanService.get_plan(999) 