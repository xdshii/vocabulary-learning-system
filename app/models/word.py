from app import db
from datetime import datetime

class Word(db.Model):
    """单词模型"""
    __tablename__ = 'words'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    phonetic = db.Column(db.String(100))
    audio_url = db.Column(db.String(200))  # 发音音频URL
    definition = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text)
    difficulty_level = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    word_relations = db.relationship('WordRelation', back_populates='word', cascade='all, delete-orphan')
    books = db.relationship(
        'app.models.vocabulary.VocabularyBook',
        secondary='word_relations',
        back_populates='words',
        viewonly=True
    )
    learning_records = db.relationship('LearningRecord', back_populates='word', cascade='all, delete-orphan')
    review_plans = db.relationship('app.models.learning.ReviewPlan', back_populates='word')
    assessment_questions = db.relationship('app.models.assessment.AssessmentQuestion', back_populates='word')
    test_questions = db.relationship('app.models.test.TestQuestion', back_populates='word')

    def __init__(self, text, definition, book_id=None, phonetic=None, example=None, difficulty_level=1.0):
        self.text = text
        self.definition = definition
        self.phonetic = phonetic
        self.example = example
        self.difficulty_level = difficulty_level
        if book_id:
            # 创建单词和词书的关联
            from app.models.vocabulary import WordRelation
            relation = WordRelation(word_id=self.id, book_id=book_id)
            db.session.add(relation)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'text': self.text,
            'phonetic': self.phonetic,
            'definition': self.definition,
            'example': self.example,
            'difficulty_level': self.difficulty_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 