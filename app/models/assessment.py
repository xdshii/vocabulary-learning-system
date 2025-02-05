from app.extensions import db
from app.models.word import Word
from app.models.vocabulary import VocabularyBook
from datetime import datetime

class UserLevelAssessment(db.Model):
    """用户水平评估"""
    __tablename__ = 'user_level_assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # beginner, intermediate, advanced
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed
    level_score = db.Column(db.Float)  # 评估得分
    score = db.Column(db.Float)  # 评估分数
    total_questions = db.Column(db.Integer)  # 总题目数
    correct_answers = db.Column(db.Integer)  # 正确答题数
    assessment_date = db.Column(db.DateTime)  # 评估完成时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # 关系
    user = db.relationship('User', back_populates='level_assessments')
    book = db.relationship('VocabularyBook', back_populates='level_assessments')
    questions = db.relationship('AssessmentQuestion', back_populates='assessment')

    def __init__(self, user_id=None, book_id=None, level='beginner', status='in_progress',
                 level_score=None, score=None, total_questions=None, correct_answers=None, assessment_date=None):
        self.user_id = user_id
        self.book_id = book_id
        self.level = level
        self.status = status
        self.level_score = level_score
        self.score = score
        self.total_questions = total_questions
        self.correct_answers = correct_answers
        self.assessment_date = assessment_date

class AssessmentQuestion(db.Model):
    """评估题目"""
    __tablename__ = 'assessment_questions'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('user_level_assessments.id'), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # multiple_choice, translation, etc.
    options = db.Column(db.JSON)  # For multiple choice questions
    correct_answer = db.Column(db.String(200), nullable=False)
    user_answer = db.Column(db.String(200))  # 用户的答案
    is_correct = db.Column(db.Boolean, default=False)  # 是否答对
    answered_at = db.Column(db.DateTime)  # 答题时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    word = db.relationship('Word', back_populates='assessment_questions')
    assessment = db.relationship('UserLevelAssessment', back_populates='questions')

    def __init__(self, assessment=None, word=None, question_type='choice', options=None, correct_answer=None, user_answer=None, is_correct=False):
        self.assessment = assessment
        self.word = word
        self.question_type = question_type
        self.options = options
        self.correct_answer = correct_answer
        self.user_answer = user_answer
        self.is_correct = is_correct

    def __repr__(self):
        return f'<AssessmentQuestion word_id={self.word_id} type={self.question_type}>' 