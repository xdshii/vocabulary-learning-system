from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """用户"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(128))
    wechat_id = db.Column(db.String(64), unique=True)
    avatar_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 关系
    vocabulary_books = db.relationship('VocabularyBook', back_populates='user', cascade='all, delete-orphan')
    learning_records = db.relationship('LearningRecord', back_populates='user', cascade='all, delete-orphan')
    learning_goals = db.relationship('LearningGoal', back_populates='user', cascade='all, delete-orphan')
    learning_plans = db.relationship('app.models.learning_plan.LearningPlan', back_populates='user')
    review_plans = db.relationship('app.models.learning.ReviewPlan', back_populates='user')
    level_assessments = db.relationship('app.models.assessment.UserLevelAssessment', back_populates='user')
    tests = db.relationship('app.models.test.Test', back_populates='user')
    test_records = db.relationship('app.models.test.TestRecord', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
