from app.extensions import db
from datetime import datetime, timedelta
import uuid
import math
from app.models.learning import LearningGoal
from app.models.learning_plan import LearningPlan
from app.models.word import Word

class VocabularyBook(db.Model):
    """词汇书"""
    __tablename__ = 'vocabulary_books'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(20))  # beginner, intermediate, advanced
    total_words = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = db.Column(db.String(200))  # 标签，用逗号分隔

    # 关联关系
    user = db.relationship('User', back_populates='vocabulary_books')
    word_relations = db.relationship('WordRelation', back_populates='book', cascade='all, delete-orphan')
    learning_records = db.relationship('LearningRecord', back_populates='book', cascade='all, delete-orphan')
    learning_plans = db.relationship('LearningPlan', back_populates='book', cascade='all, delete-orphan')
    learning_goals = db.relationship('LearningGoal', back_populates='book', cascade='all, delete-orphan')
    words = db.relationship(
        'app.models.word.Word',
        secondary='word_relations',
        back_populates='books',
        viewonly=True
    )
    tests = db.relationship('app.models.test.Test', back_populates='book', lazy='dynamic')
    level_assessments = db.relationship('app.models.assessment.UserLevelAssessment', back_populates='book')

    def __init__(self, name=None, description=None, level=None, user_id=None, tags=None, total_words=0):
        self.name = name
        self.description = description
        self.level = level
        self.user_id = user_id
        self.tags = ','.join(tags) if tags else None
        self.total_words = total_words

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'level': self.level,
            'user_id': self.user_id,
            'tags': self.tags.split(',') if self.tags else [],
            'word_count': len(self.words),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WordRelation(db.Model):
    """单词与词汇书的关联"""
    __tablename__ = 'word_relations'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'), nullable=False)
    order = db.Column(db.Integer)  # 在词汇书中的顺序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    word = db.relationship('app.models.word.Word', back_populates='word_relations')
    book = db.relationship('VocabularyBook', back_populates='word_relations')

    def __init__(self, word_id=None, book_id=None, order=None):
        self.word_id = word_id
        self.book_id = book_id
        self.order = order

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'word_id': self.word_id,
            'book_id': self.book_id,
            'order': self.order,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }