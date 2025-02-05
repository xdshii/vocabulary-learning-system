from app.extensions import db
from datetime import datetime, timedelta
import math
from app.models.word import Word
from app.models.learning_record import LearningRecord

class LearningGoal(db.Model):
    """学习目标"""
    __tablename__ = 'learning_goals'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'), nullable=False)
    daily_word_count = db.Column(db.Integer, nullable=False)  # 每日目标单词数
    target_date = db.Column(db.DateTime, nullable=False)  # 目标完成日期
    status = db.Column(db.String(20), default='active')  # active, completed, paused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = db.relationship('app.models.user.User', back_populates='learning_goals')
    book = db.relationship('app.models.vocabulary.VocabularyBook', back_populates='learning_goals')

    def __init__(self, user_id=None, book_id=None, daily_word_count=None, target_date=None, status=None):
        self.user_id = user_id
        self.book_id = book_id
        self.daily_word_count = daily_word_count
        self.target_date = target_date
        self.status = status or 'active'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'daily_word_count': self.daily_word_count,
            'target_date': self.target_date.isoformat(),
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ReviewPlan(db.Model):
    """复习计划"""
    __tablename__ = 'review_plans'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    next_review_time = db.Column(db.DateTime, nullable=False)
    review_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, completed, skipped
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = db.relationship('app.models.user.User', back_populates='review_plans')
    word = db.relationship('app.models.word.Word', back_populates='review_plans')

    def __init__(self, user=None, word=None, next_review_time=None):
        """初始化复习计划"""
        self.user = user
        self.word = word
        self.next_review_time = next_review_time or datetime.utcnow()
        self.status = 'pending'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'word_id': self.word_id,
            'next_review_time': self.next_review_time.isoformat(),
            'review_count': self.review_count,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 