from datetime import datetime
from app.extensions import db

class Test(db.Model):
    """测试"""
    __tablename__ = 'tests'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    test_type = db.Column(db.String(20))  # 测试类型
    duration = db.Column(db.Integer)  # 考试时长（分钟）
    total_questions = db.Column(db.Integer, default=0)
    pass_score = db.Column(db.Integer, default=60)  # 及格分数
    score = db.Column(db.Float)  # 测试得分
    correct_answers = db.Column(db.Integer, default=0)  # 正确答案数量
    start_time = db.Column(db.DateTime)  # 开始时间
    end_time = db.Column(db.DateTime)  # 结束时间
    completed_at = db.Column(db.DateTime)  # 完成时间
    status = db.Column(db.String(20), default='pending')  # 测试状态: pending, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = db.relationship('User', back_populates='tests')
    book = db.relationship('app.models.vocabulary.VocabularyBook', back_populates='tests')
    questions = db.relationship('TestQuestion', back_populates='test', cascade='all, delete-orphan')
    test_records = db.relationship('TestRecord', back_populates='test', cascade='all, delete-orphan')

    def __init__(self, user_id=None, book_id=None, name=None, description=None, test_type=None, duration=None, total_questions=None, pass_score=None):
        self.user_id = user_id
        self.book_id = book_id
        self.name = name
        self.description = description
        self.test_type = test_type
        self.duration = duration
        self.total_questions = total_questions
        self.pass_score = pass_score
        self.score = None

    def to_dict(self, with_questions=False):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'name': self.name,
            'description': self.description,
            'test_type': self.test_type,
            'duration': self.duration,
            'total_questions': self.total_questions,
            'pass_score': self.pass_score,
            'score': self.score,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if with_questions:
            data['questions'] = [question.to_dict() for question in self.questions]
        return data

class TestQuestion(db.Model):
    """测试题目"""
    __tablename__ = 'test_questions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # choice, fill, etc.
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)  # 选项列表
    correct_answer = db.Column(db.String(200), nullable=False)
    user_answer = db.Column(db.String(200))  # 用户的答案
    is_correct = db.Column(db.Boolean, default=False)  # 是否答对
    score = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    test = db.relationship('Test', back_populates='questions')
    word = db.relationship('app.models.word.Word', back_populates='test_questions')
    answers = db.relationship('TestAnswer', back_populates='question', cascade='all, delete-orphan')

    def __init__(self, test_id=None, word_id=None, question_type=None, question=None, options=None, correct_answer=None, score=None):
        self.test_id = test_id
        self.word_id = word_id
        self.question_type = question_type
        self.question = question
        self.options = options
        self.correct_answer = correct_answer
        self.score = score
        self.is_correct = False
        self.user_answer = None

    def to_dict(self, include_answer=True):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'test_id': self.test_id,
            'word_id': self.word_id,
            'question_type': self.question_type,
            'question': self.question,
            'options': self.options,
            'score': self.score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_answer:
            data['correct_answer'] = self.correct_answer
        return data

class TestRecord(db.Model):
    """测试记录"""
    __tablename__ = 'test_records'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    score = db.Column(db.Integer)
    correct_count = db.Column(db.Integer, default=0)  # 添加正确答题数
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, timeout
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    test = db.relationship('Test', back_populates='test_records')
    user = db.relationship('User', back_populates='test_records')
    answers = db.relationship('TestAnswer', back_populates='record', cascade='all, delete-orphan')

    def __init__(self, test_id=None, user_id=None, start_time=None, end_time=None, score=None, status=None, correct_count=None):
        self.test_id = test_id
        self.user_id = user_id
        self.start_time = start_time
        self.end_time = end_time
        self.score = score
        self.status = status or 'in_progress'
        self.correct_count = correct_count or 0

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'test_id': self.test_id,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'score': self.score,
            'correct_count': self.correct_count,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class TestAnswer(db.Model):
    """测试答案"""
    __tablename__ = 'test_answers'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('test_records.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('test_questions.id'), nullable=False)
    answer = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    record = db.relationship('TestRecord', back_populates='answers')
    question = db.relationship('TestQuestion', back_populates='answers')

    def __init__(self, record_id=None, question_id=None, answer=None, is_correct=None):
        self.record_id = record_id
        self.question_id = question_id
        self.answer = answer
        self.is_correct = is_correct

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'record_id': self.record_id,
            'question_id': self.question_id,
            'answer': self.answer,
            'is_correct': self.is_correct,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 