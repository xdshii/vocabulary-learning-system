# 单词管理系统技术实现文档

## 1. 系统架构

### 1.1 技术栈
- 后端框架：Flask
- 数据库：PostgreSQL
- 认证：JWT (JSON Web Token)
- ORM：SQLAlchemy
- 缓存：Redis

### 1.2 目录结构
```
build/
├── app/
│   ├── models/
│   │   ├── vocabulary.py    # 单词相关模型
│   │   └── user.py         # 用户模型
│   ├── api/
│   │   └── vocabulary.py   # 单词相关接口
│   └── services/          # 业务逻辑层
├── docs/                 # 文档
└── tests/               # 测试用例
```

## 2. 核心功能实现

### 2.1 数据模型

#### 单词书模型（VocabularyBook）
```python
class VocabularyBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(20))
    total_words = db.Column(db.Integer, default=0)
    words = db.relationship('Word', backref='book', lazy='dynamic')
```

#### 单词模型（Word）
```python
class Word(db.Model):
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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'))
    status = db.Column(db.String(20), default='new')
    review_count = db.Column(db.Integer, default=0)
    next_review_time = db.Column(db.DateTime)
```

### 2.2 功能实现

#### 单词书管理
- 创建单词书：支持设置名称、描述、难度级别
- 更新单词书：可修改基本信息
- 自动维护单词总数

#### 单词管理
- 添加单词：包含单词、音标、释义、例句
- 更新单词：支持修改所有字段
- 删除单词：自动更新单词书总数

#### 学习记录
- 学习状态：new（新词）、learning（学习中）、mastered（已掌握）
- 复习计数：记录每个单词的复习次数
- 学习进度：统计不同状态的单词数量

#### 搜索功能
- 关键词搜索：支持单词和释义的模糊匹配
- 多条件筛选：单词书、难度级别、学习状态
- 排序功能：按学习次数降序排序
- 分页支持：可配置每页数量

### 2.3 安全措施
- JWT认证保护所有接口
- 用户隔离：每个用户只能访问自己的学习记录
- 参数验证：确保必要字段存在和格式正确
- 错误处理：统一的错误响应格式

## 3. 测试策略

### 3.1 测试环境
- 独立的测试数据库
- 测试用户和认证
- 模拟学习记录数据

### 3.2 测试用例
- 单词书管理测试
- 单词CRUD测试
- 学习记录更新测试
- 搜索功能测试
- 分页和排序测试

## 4. 部署说明

### 4.1 环境要求
- Python 3.8+
- PostgreSQL 12+
- Redis 6+

### 4.2 配置项
```python
class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://...'
    JWT_SECRET_KEY = 'your-secret-key'
    REDIS_URL = 'redis://localhost:6379/0'
```

### 4.3 部署步骤
1. 安装依赖：`pip install -r requirements.txt`
2. 设置环境变量
3. 初始化数据库：`flask db upgrade`
4. 启动应用：`gunicorn app:app`

## 5. 注意事项

### 5.1 性能优化
- 使用索引优化搜索
- 合理的分页大小
- 缓存热门单词书

### 5.2 数据一致性
- 事务管理
- 并发控制
- 数据验证

### 5.3 扩展性
- 支持批量导入
- 预留API版本控制
- 模块化设计 