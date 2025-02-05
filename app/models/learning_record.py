from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

class LearningRecord(db.Model):
    """学习记录模型"""
    __tablename__ = 'learning_records'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='learning')  # learning, mastered, reviewing
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_review_time = db.Column(db.DateTime)
    next_review_time = db.Column(db.DateTime)
    review_count = db.Column(db.Integer, default=0)
    mastery_level = db.Column(db.Float, default=0.0)
    study_time = db.Column(db.Float, default=0.0)

    # 关联关系
    user = db.relationship('User', back_populates='learning_records')
    book = db.relationship('VocabularyBook', back_populates='learning_records')
    word = db.relationship('Word', back_populates='learning_records')

    def update_review_time(self):
        """更新复习时间"""
        self.last_review_time = datetime.utcnow()
        
        # 根据复习次数调整下次复习时间间隔
        intervals = {
            0: timedelta(days=2),  # 修改为2天
            1: timedelta(days=3),
            2: timedelta(days=4),
            3: timedelta(days=7),
            4: timedelta(days=15),
            5: timedelta(days=30),
            6: timedelta(days=60)
        }
        
        interval = intervals.get(self.review_count, timedelta(days=60))
        new_next_review_time = datetime.utcnow() + interval
        
        # 如果当前的next_review_time更晚，就保持不变
        if self.next_review_time and self.next_review_time > new_next_review_time:
            new_next_review_time = self.next_review_time
            
        self.next_review_time = new_next_review_time
        self.review_count += 1
        
        # 更新掌握程度
        self.mastery_level = min(1.0, self.mastery_level + 0.2)
        
        db.session.commit()

    @classmethod
    def get_statistics(cls, user_id, book_id=None):
        """获取学习统计信息"""
        query = cls.query.filter_by(user_id=user_id)
        if book_id:
            query = query.filter_by(book_id=book_id)
            
        total = query.count()
        mastered = query.filter_by(status='mastered').count()
        learning = query.filter_by(status='learning').count()
        reviewing = query.filter_by(status='reviewing').count()
        
        # 计算平均掌握程度
        avg_mastery = db.session.query(func.avg(cls.mastery_level))\
            .filter_by(user_id=user_id)\
            .scalar() or 0.0
            
        return {
            'total': total,
            'mastered': mastered,
            'learning': learning,
            'reviewing': reviewing,
            'average_mastery': float(avg_mastery)
        }

    def __init__(self, user_id, book_id, word_id, status='learning', study_time=0, review_count=0, next_review_time=None, last_review_time=None):
        """初始化学习记录"""
        if status not in ['learning', 'mastered', 'reviewing']:
            raise ValueError('Invalid status value')
            
        self.user_id = user_id
        self.book_id = book_id
        self.word_id = word_id
        self.status = status
        self.study_time = study_time
        self.review_count = review_count
        self.next_review_time = next_review_time
        self.last_review_time = last_review_time
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.mastery_level = 0.0

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'word_id': self.word_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_review_time': self.last_review_time.isoformat() if self.last_review_time else None,
            'next_review_time': self.next_review_time.isoformat() if self.next_review_time else None,
            'review_count': self.review_count,
            'mastery_level': self.mastery_level
        } 