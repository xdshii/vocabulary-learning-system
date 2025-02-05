from app import db
from datetime import datetime

class LearningPlan(db.Model):
    """学习计划模型"""
    __tablename__ = 'learning_plans'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'), nullable=False)
    daily_words = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)  # 添加开始日期
    end_date = db.Column(db.Date)  # 添加结束日期
    status = db.Column(db.String(20), nullable=False, default='active')  # active, completed, paused
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = db.relationship('app.models.user.User', back_populates='learning_plans')
    book = db.relationship('app.models.vocabulary.VocabularyBook', back_populates='learning_plans')

    def __init__(self, user_id, book_id, daily_words, start_date, end_date=None, status='active'):
        """初始化学习计划"""
        if status not in ['active', 'completed', 'paused']:
            raise ValueError('Invalid status value')
            
        self.user_id = user_id
        self.book_id = book_id
        self.daily_words = daily_words
        self.start_date = start_date
        self.end_date = end_date
        self.status = status

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'daily_words': self.daily_words,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def update_status(self, status):
        """更新计划状态"""
        if status not in ['active', 'completed', 'paused']:
            raise ValueError('Invalid status value')
        self.status = status
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def calculate_progress(self):
        """计算学习进度"""
        from app.models.learning import LearningRecord
        
        # 获取已掌握的单词数
        mastered_count = LearningRecord.query.filter_by(
            user_id=self.user_id,
            book_id=self.book_id,
            status='mastered'
        ).count()
        
        # 获取词书总单词数
        total_words = self.book.total_words or 0
        
        if total_words == 0:
            return 0
            
        return round(mastered_count / total_words * 100, 2)

    def get_daily_progress(self):
        """获取今日学习进度"""
        from app.models.learning import LearningRecord
        from datetime import datetime, timedelta
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # 获取今日学习的单词数
        today_learned = LearningRecord.query.filter(
            LearningRecord.user_id == self.user_id,
            LearningRecord.book_id == self.book_id,
            LearningRecord.created_at >= today_start,
            LearningRecord.created_at < today_end
        ).count()
        
        return {
            'target': self.daily_words,
            'completed': today_learned,
            'percentage': round(today_learned / self.daily_words * 100, 2) if self.daily_words > 0 else 0
        } 