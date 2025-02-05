# 智能词汇学习系统技术实现文档

## 1. 系统架构

### 1.1 技术栈
- 后端框架：Flask
- 数据库：PostgreSQL
- 缓存：Redis
- ORM：SQLAlchemy
- 认证：JWT (JSON Web Token)
- 测试框架：pytest

### 1.2 目录结构
```
build/
├── app/
│   ├── __init__.py          # Flask应用初始化
│   ├── config.py            # 配置文件
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py         # 用户模型
│   │   ├── vocabulary.py   # 词汇相关模型
│   │   ├── learning.py     # 学习记录模型
│   │   └── test.py         # 测试相关模型
│   ├── services/           # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py    # 认证服务
│   │   ├── vocabulary_service.py  # 词汇管理服务
│   │   ├── learning_service.py    # 学习服务
│   │   ├── test_service.py       # 测试服务
│   │   └── recommendation_service.py  # 推荐服务
│   ├── api/                # API接口层
│   │   ├── __init__.py
│   │   ├── auth.py        # 认证相关接口
│   │   ├── vocabulary.py  # 词汇管理接口
│   │   ├── learning.py    # 学习相关接口
│   │   └── test.py        # 测试相关接口
│   └── utils/             # 工具函数
│       ├── __init__.py
│       ├── auth.py        # 认证工具
│       └── helpers.py     # 通用工具函数
├── tests/                 # 测试用例
│   ├── __init__.py
│   ├── conftest.py       # 测试配置
│   ├── test_auth.py      # 认证测试
│   ├── test_vocabulary.py # 词汇管理测试
│   └── test_learning.py  # 学习功能测试
└── requirements.txt      # 依赖管理
```

## 2. 核心功能实现

### 2.1 数据模型

#### User 模型
```python
class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    vocabulary_books = db.relationship('VocabularyBook', backref='creator')
    learning_records = db.relationship('LearningRecord', backref='user')
    tests = db.relationship('Test', backref='user')
```

#### VocabularyBook 模型
```python
class VocabularyBook(db.Model):
    """词汇书模型"""
    __tablename__ = 'vocabulary_books'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(20))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    words = db.relationship('Word', backref='book')
    tags = db.Column(db.JSON)
```

#### Word 模型
```python
class Word(db.Model):
    """单词模型"""
    __tablename__ = 'words'
    
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    pronunciation = db.Column(db.String(100))
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'))
    definitions = db.Column(db.JSON)
    difficulty_level = db.Column(db.Float)
    importance_level = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    learning_records = db.relationship('LearningRecord', backref='word')
```

#### LearningRecord 模型
```python
class LearningRecord(db.Model):
    """学习记录模型"""
    __tablename__ = 'learning_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'))
    status = db.Column(db.String(20))  # new, learning, mastered
    review_count = db.Column(db.Integer, default=0)
    last_review_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Test 模型
```python
class Test(db.Model):
    """测试模型"""
    __tablename__ = 'tests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'))
    test_type = db.Column(db.String(20))
    score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    questions = db.relationship('TestQuestion', backref='test')
```

#### UserLevelAssessment 模型
```python
class UserLevelAssessment(db.Model):
    """用户水平评估模型"""
    __tablename__ = 'user_level_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'))
    level_score = db.Column(db.Float)  # 1-5分
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.JSON)  # 存储评估详情
    
    user = db.relationship('User', backref='assessments')
    book = db.relationship('VocabularyBook', backref='user_assessments')
```

#### WordRelation 模型
```python
class WordRelation(db.Model):
    """单词关系模型"""
    __tablename__ = 'word_relations'
    
    id = db.Column(db.Integer, primary_key=True)
    source_word_id = db.Column(db.Integer, db.ForeignKey('words.id'))
    target_word_id = db.Column(db.Integer, db.ForeignKey('words.id'))
    relation_type = db.Column(db.String(20))  # synonym, antonym, similar
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    source_word = db.relationship('Word', foreign_keys=[source_word_id], backref='source_relations')
    target_word = db.relationship('Word', foreign_keys=[target_word_id], backref='target_relations')
```

#### LearningPlan 模型
```python
class LearningPlan(db.Model):
    """学习计划模型"""
    __tablename__ = 'learning_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'))
    daily_word_count = db.Column(db.Integer, default=20)
    target_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='learning_plans')
    book = db.relationship('VocabularyBook', backref='learning_plans')
```

### 2.2 服务层实现

#### VocabularyService
```python
class VocabularyService:
    @staticmethod
    def create_book(user_id, name, description, level, tags=None):
        book = VocabularyBook(
            creator_id=user_id,
            name=name,
            description=description,
            level=level,
            tags=tags or []
        )
        db.session.add(book)
        db.session.commit()
        return book
    
    @staticmethod
    def add_word(book_id, word_data):
        word = Word(
            book_id=book_id,
            word=word_data['word'],
            pronunciation=word_data.get('pronunciation'),
            definitions=word_data['definitions'],
            difficulty_level=word_data.get('difficulty_level', 1.0),
            importance_level=word_data.get('importance_level', 1.0)
        )
        db.session.add(word)
        db.session.commit()
        return word
```

#### LearningService
```python
class LearningService:
    @staticmethod
    def record_learning(user_id, word_id, status, review_count=None):
        record = LearningRecord.query.filter_by(
            user_id=user_id,
            word_id=word_id
        ).first()
        
        if not record:
            record = LearningRecord(
                user_id=user_id,
                word_id=word_id
            )
            db.session.add(record)
        
        record.status = status
        if review_count is not None:
            record.review_count = review_count
        record.last_review_at = datetime.utcnow()
        
        db.session.commit()
        return record
    
    @staticmethod
    def get_learning_progress(user_id, book_id):
        total_words = Word.query.filter_by(book_id=book_id).count()
        learned_words = LearningRecord.query.join(Word).filter(
            LearningRecord.user_id == user_id,
            Word.book_id == book_id,
            LearningRecord.status == 'mastered'
        ).count()
        
        return {
            'total': total_words,
            'learned': learned_words,
            'progress': learned_words / total_words if total_words > 0 else 0
        }
```

#### TestService
```python
class TestService:
    @staticmethod
    def generate_test(user_id, book_id, question_count=20):
        # 创建测试记录
        test = Test(
            user_id=user_id,
            book_id=book_id,
            test_type='vocabulary'
        )
        db.session.add(test)
        
        # 获取用户学习记录
        learning_records = LearningRecord.query.filter_by(
            user_id=user_id
        ).join(Word).filter(
            Word.book_id == book_id
        ).all()
        
        # 生成题目
        words = Word.query.filter_by(book_id=book_id).order_by(
            func.random()
        ).limit(question_count).all()
        
        for word in words:
            question = TestQuestion(
                test_id=test.id,
                word_id=word.id,
                question_type='multiple_choice',
                options=self._generate_options(word)
            )
            db.session.add(question)
        
        db.session.commit()
        return test
    
    @staticmethod
    def submit_test(test_id, user_id, answers):
        test = Test.query.get_or_404(test_id)
        correct_count = 0
        
        for question_id, answer in answers.items():
            question = TestQuestion.query.get(question_id)
            is_correct = answer == question.correct_answer
            if is_correct:
                correct_count += 1
            
            result = TestResult(
                test_id=test_id,
                question_id=question_id,
                user_answer=answer,
                is_correct=is_correct
            )
            db.session.add(result)
        
        test.score = (correct_count / len(answers)) * 100
        test.completed_at = datetime.utcnow()
        
        # 更新学习记录
        for question in test.questions:
            record = LearningRecord.query.filter_by(
                user_id=user_id,
                word_id=question.word_id
            ).first()
            
            if record:
                record.review_count += 1
                if record.status != 'mastered':
                    result = TestResult.query.filter_by(
                        test_id=test_id,
                        question_id=question.id
                    ).first()
                    if result and result.is_correct:
                        record.status = 'mastered'
        
        db.session.commit()
        return test
```

### 2.3 推荐系统实现

#### RecommendationService
```python
class RecommendationService:
    @staticmethod
    def get_recommended_words(user_id, book_id, count=20):
        # 获取用户水平
        user_level = UserLevelAssessment.query.filter_by(
            user_id=user_id,
            book_id=book_id
        ).order_by(UserLevelAssessment.assessment_date.desc()).first()
        
        if not user_level:
            # 如果没有评估记录，进行评估
            user_level = RecommendationService.assess_user_level(user_id, book_id)
        
        # 根据用户水平推荐单词
        level_score = user_level.level_score
        words = []
        
        # 30% 低于用户水平的单词
        lower_words = Word.query.filter(
            Word.book_id == book_id,
            Word.difficulty_level < level_score
        ).order_by(func.random()).limit(int(count * 0.3)).all()
        words.extend(lower_words)
        
        # 50% 匹配用户水平的单词
        matching_words = Word.query.filter(
            Word.book_id == book_id,
            Word.difficulty_level.between(level_score - 0.5, level_score + 0.5)
        ).order_by(func.random()).limit(int(count * 0.5)).all()
        words.extend(matching_words)
        
        # 20% 高于用户水平的单词
        higher_words = Word.query.filter(
            Word.book_id == book_id,
            Word.difficulty_level > level_score
        ).order_by(func.random()).limit(int(count * 0.2)).all()
        words.extend(higher_words)
        
        return words
```

### 2.4 评估系统实现

#### AssessmentService
```python
class AssessmentService:
    @staticmethod
    def start_assessment(user_id, book_id, question_count=20):
        """开始水平评估"""
        # 创建评估记录
        assessment = UserLevelAssessment(
            user_id=user_id,
            book_id=book_id
        )
        db.session.add(assessment)
        
        # 根据词汇书难度分布选择测试单词
        words = Word.query.filter_by(book_id=book_id).order_by(
            Word.difficulty_level
        ).all()
        
        # 按难度分层抽样
        selected_words = []
        difficulty_ranges = [(1,2), (2,3), (3,4), (4,5)]
        for diff_range in difficulty_ranges:
            range_words = [w for w in words if diff_range[0] <= w.difficulty_level < diff_range[1]]
            count = int(question_count * 0.25)  # 每个难度范围25%的题目
            if range_words:
                selected_words.extend(random.sample(range_words, min(count, len(range_words))))
        
        # 生成测试题目
        questions = []
        for word in selected_words:
            question = TestQuestion(
                test_id=assessment.id,
                word_id=word.id,
                question_type='multiple_choice',
                options=cls._generate_options(word)
            )
            db.session.add(question)
            questions.append(question)
        
        db.session.commit()
        return assessment, questions
    
    @staticmethod
    def submit_assessment(assessment_id, answers):
        """提交评估答案"""
        assessment = UserLevelAssessment.query.get_or_404(assessment_id)
        correct_count = 0
        weighted_score = 0
        
        for question_id, answer in answers.items():
            question = TestQuestion.query.get(question_id)
            word = Word.query.get(question.word_id)
            
            is_correct = answer == question.correct_answer
            if is_correct:
                correct_count += 1
                weighted_score += word.difficulty_level
        
        # 计算水平分数
        total_questions = len(answers)
        accuracy_rate = correct_count / total_questions
        average_difficulty = weighted_score / correct_count if correct_count > 0 else 0
        
        # 综合计算得分 (1-5分)
        level_score = (accuracy_rate * 0.7 + (average_difficulty / 5) * 0.3) * 5
        
        # 更新评估记录
        assessment.level_score = level_score
        assessment.details = {
            'total_questions': total_questions,
            'correct_count': correct_count,
            'accuracy_rate': accuracy_rate,
            'average_difficulty': average_difficulty,
            'suggested_level': cls._get_suggested_level(level_score)
        }
        
        db.session.commit()
        return assessment
    
    @staticmethod
    def _get_suggested_level(score):
        """根据分数返回建议级别"""
        if score < 2:
            return 'beginner'
        elif score < 3:
            return 'elementary'
        elif score < 4:
            return 'intermediate'
        else:
            return 'advanced'
```

### 2.5 学习计划实现

#### LearningPlanService
```python
class LearningPlanService:
    @staticmethod
    def create_plan(user_id, book_id, daily_word_count, target_date):
        """创建学习计划"""
        # 检查是否已有计划
        existing_plan = LearningPlan.query.filter_by(
            user_id=user_id,
            book_id=book_id,
            active=True
        ).first()
        
        if existing_plan:
            raise ValueError("已存在活动的学习计划")
        
        # 获取词汇书中未掌握的单词数量
        total_words = Word.query.filter_by(book_id=book_id).count()
        mastered_words = LearningRecord.query.join(Word).filter(
            LearningRecord.user_id == user_id,
            Word.book_id == book_id,
            LearningRecord.status == 'mastered'
        ).count()
        
        remaining_words = total_words - mastered_words
        
        # 计算预计完成日期
        days_needed = math.ceil(remaining_words / daily_word_count)
        estimated_completion_date = datetime.now().date() + timedelta(days=days_needed)
        
        # 创建计划
        plan = LearningPlan(
            user_id=user_id,
            book_id=book_id,
            daily_word_count=daily_word_count,
            target_date=target_date,
            estimated_completion_date=estimated_completion_date,
            remaining_words=remaining_words
        )
        
        db.session.add(plan)
        db.session.commit()
        return plan
    
    @staticmethod
    def update_plan(plan_id, daily_word_count=None, target_date=None):
        """更新学习计划"""
        plan = LearningPlan.query.get_or_404(plan_id)
        
        if daily_word_count:
            plan.daily_word_count = daily_word_count
        
        if target_date:
            plan.target_date = target_date
        
        # 重新计算预计完成日期
        days_needed = math.ceil(plan.remaining_words / plan.daily_word_count)
        plan.estimated_completion_date = datetime.now().date() + timedelta(days=days_needed)
        
        db.session.commit()
        return plan
    
    @staticmethod
    def get_daily_words(user_id, book_id):
        """获取每日推荐单词"""
        plan = LearningPlan.query.filter_by(
            user_id=user_id,
            book_id=book_id,
            active=True
        ).first()
        
        if not plan:
            raise ValueError("未找到活动的学习计划")
        
        # 获取用户水平
        assessment = UserLevelAssessment.query.filter_by(
            user_id=user_id,
            book_id=book_id
        ).order_by(UserLevelAssessment.assessment_date.desc()).first()
        
        if not assessment:
            raise ValueError("请先进行水平评估")
        
        # 根据用户水平和计划推荐单词
        return RecommendationService.get_recommended_words(
            user_id=user_id,
            book_id=book_id,
            count=plan.daily_word_count,
            user_level=assessment.level_score
        )
```

## 3. 测试策略

### 3.1 单元测试
- 使用 pytest 框架
- 每个模块独立测试
- 使用 mock 模拟外部依赖

### 3.2 集成测试
- 测试 API 接口
- 测试数据库交互
- 测试缓存机制

### 3.3 性能测试
- 并发用户测试
- 响应时间测试
- 数据库性能测试

## 4. 部署说明

### 4.1 环境要求
- Python 3.8+
- PostgreSQL 12+
- Redis 6+

### 4.2 配置项
```python
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    REDIS_URL = os.getenv('REDIS_URL')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
```

### 4.3 部署步骤
1. 安装依赖：`pip install -r requirements.txt`
2. 设置环境变量
3. 初始化数据库：`flask db upgrade`
4. 启动应用：`gunicorn app:app`

## 5. 安全措施

### 5.1 认证安全
- 使用 JWT 进行身份验证
- Token 过期机制
- 密码加密存储

### 5.2 数据安全
- SQL 注入防护
- XSS 防护
- CSRF 防护

### 5.3 接口安全
- 请求频率限制
- 输入验证
- 错误处理 