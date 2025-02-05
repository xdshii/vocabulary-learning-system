# 词汇学习系统实现文档

## 1. 系统架构

### 1.1 技术栈
- 后端框架：Flask
- 数据库：PostgreSQL
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
│   │   └── vocabulary.py    # 词汇相关模型
│   ├── api/                 # API接口
│   │   ├── __init__.py
│   │   ├── auth.py         # 认证接口
│   │   └── vocabulary.py    # 词汇学习接口
│   └── utils/              # 工具函数
│       └── __init__.py
├── tests/                  # 测试用例
│   ├── __init__.py
│   ├── conftest.py        # 测试配置
│   └── test_vocabulary.py  # 词汇学习测试
└── requirements.txt       # 依赖管理
```

## 2. 核心功能实现

### 2.1 数据模型

#### 用户模型（User）
```python
class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(255))
    email = db.Column(db.String(255))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### 单词书模型（VocabularyBook）
```python
class VocabularyBook(db.Model):
    __tablename__ = 'vocabulary_books'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(20))
    total_words = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### 单词模型（Word）
```python
class Word(db.Model):
    __tablename__ = 'words'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('vocabulary_books.id'))
    word = db.Column(db.String(100), nullable=False)
    pronunciation = db.Column(db.String(100))
    definition = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text)
```

#### 学习记录模型（LearningRecord）
```python
class LearningRecord(db.Model):
    __tablename__ = 'learning_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'))
    status = db.Column(db.String(20), default='new')
    review_count = db.Column(db.Integer, default=0)
    last_review_time = db.Column(db.DateTime)
    next_review_time = db.Column(db.DateTime)
```

### 2.2 复习算法实现

#### 艾宾浩斯遗忘曲线
```python
def calculate_next_review_time(self):
    """计算下次复习时间"""
    if not self.last_review_time:
        self.last_review_time = datetime.utcnow()
        
    intervals = [1, 2, 4, 7, 15, 30, 60]  # 复习间隔（天）
    if self.review_count >= len(intervals):
        interval = intervals[-1]
    else:
        interval = intervals[self.review_count]
        
    self.next_review_time = self.last_review_time + timedelta(days=interval)
    return self.next_review_time
```

### 2.3 安全措施

#### 密码安全
- 使用bcrypt进行密码加密
- 密码永远不以明文存储
```python
def set_password(self, password):
    """设置密码"""
    salt = bcrypt.gensalt()
    self.password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(self, password):
    """验证密码"""
    if not self.password:
        return False
    return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
```

#### JWT认证
- 使用 `flask-jwt-extended` 实现
- Token有效期30分钟
- 支持Token刷新机制

## 3. 测试策略

### 3.1 测试环境
- 使用独立的测试数据库
- 每个测试前重置数据库状态
- 使用pytest fixtures管理测试数据

### 3.2 测试覆盖
- 单元测试：模型方法和工具函数
- 集成测试：API接口和数据库交互
- 功能测试：完整的用户操作流程

### 3.3 测试数据管理
```python
@pytest.fixture
def init_database(app):
    with app.app_context():
        db.create_all()
        
        # 创建测试用户
        user = User(
            username='testuser',
            phone_number='13800138000'
        )
        user.set_password('test123')
        db.session.add(user)
        
        # 创建测试数据...
        db.session.commit()
        
        yield
        
        db.session.remove()
        db.drop_all()
```

## 4. 部署说明

### 4.1 环境要求
- Python 3.8+
- PostgreSQL 12+
- 操作系统：Linux/Unix

### 4.2 配置说明
```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
```

### 4.3 部署步骤
1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 环境变量配置
```bash
export FLASK_APP=app
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@localhost/dbname
```

3. 数据库迁移
```bash
flask db upgrade
```

4. 启动应用
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
``` 