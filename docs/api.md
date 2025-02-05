# 智能词汇学习系统 API 文档

## 基础信息

- 基础URL: `/api/v1`
- 所有请求和响应均使用 JSON 格式
- 认证使用 Bearer Token 方式

## 错误码说明

| 错误码 | 描述 |
|--------|------|
| 400001 | 参数缺失或格式错误 |
| 400002 | 资源不存在 |
| 400003 | 权限不足 |
| 400004 | 操作失败 |
| 403001 | 账号已被禁用 |
| 404001 | 用户不存在 |

## API 接口

### 1. 用户管理

#### 1.1 用户注册

**请求**
```http
POST /auth/register
Content-Type: application/json

{
    "username": "user123",
    "password": "Password123",
    "email": "user@example.com"
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "access_token": "eyJ0eXAi...",
        "user": {
            "id": "uuid",
            "username": "user123",
            "email": "user@example.com"
        }
    }
}
```

#### 1.2 用户登录

**请求**
```http
POST /auth/login
Content-Type: application/json

{
    "username": "user123",
    "password": "Password123"
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "access_token": "eyJ0eXAi...",
        "user": {
            "id": "uuid",
            "username": "user123",
            "email": "user@example.com"
        }
    }
}
```

### 2. 词汇书管理

#### 2.1 创建词汇书

**请求**
```http
POST /vocabulary-books
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "IELTS核心词汇",
    "description": "IELTS考试必备词汇",
    "level": "advanced",
    "tags": ["IELTS", "考试"]
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "name": "IELTS核心词汇",
        "description": "IELTS考试必备词汇",
        "level": "advanced",
        "tags": ["IELTS", "考试"],
        "created_at": "2024-01-20T10:00:00Z"
    }
}
```

#### 2.2 获取词汇书列表

**请求**
```http
GET /vocabulary-books
Authorization: Bearer <access_token>
```

**响应**
```json
{
    "code": 200,
    "data": {
        "total": 10,
        "items": [
            {
                "id": 1,
                "name": "IELTS核心词汇",
                "description": "IELTS考试必备词汇",
                "level": "advanced",
                "tags": ["IELTS", "考试"],
                "word_count": 5000
            }
        ]
    }
}
```

### 3. 单词管理

#### 3.1 添加单词

**请求**
```http
POST /vocabulary-books/{book_id}/words
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "word": "ephemeral",
    "pronunciation": "ɪˈfem(ə)rəl",
    "definitions": [
        {
            "pos": "adj",
            "meaning": "短暂的，瞬息的",
            "example": "ephemeral pleasures"
        }
    ],
    "difficulty_level": 4.5,
    "importance_level": 4.0
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "word": "ephemeral",
        "pronunciation": "ɪˈfem(ə)rəl",
        "definitions": [...],
        "difficulty_level": 4.5,
        "importance_level": 4.0
    }
}
```

### 4. 学习管理

#### 4.1 获取推荐单词

**请求**
```http
GET /vocabulary-books/{book_id}/recommendations
Authorization: Bearer <access_token>
```

**响应**
```json
{
    "code": 200,
    "data": {
        "words": [
            {
                "id": 1,
                "word": "ephemeral",
                "difficulty_level": 4.5,
                "learning_status": "new"
            }
        ]
    }
}
```

#### 4.2 提交学习记录

**请求**
```http
POST /learning-records
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "word_id": 1,
    "status": "learned",
    "duration": 300,
    "review_count": 1
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "word_id": 1,
        "status": "learned",
        "created_at": "2024-01-20T10:30:00Z"
    }
}
```

### 5. 测试系统

#### 5.1 生成测试

**请求**
```http
POST /tests/generate
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "book_id": 1,
    "question_count": 20,
    "test_type": "vocabulary"
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "test_id": 1,
        "questions": [
            {
                "id": 1,
                "word": "ephemeral",
                "options": ["短暂的", "永恒的", "美丽的", "神秘的"],
                "type": "multiple_choice"
            }
        ]
    }
}
```

#### 5.2 提交测试答案

**请求**
```http
POST /tests/{test_id}/submit
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "answers": [
        {
            "question_id": 1,
            "answer": "短暂的"
        }
    ]
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "score": 95,
        "correct_count": 19,
        "total_count": 20,
        "details": [
            {
                "question_id": 1,
                "is_correct": true,
                "correct_answer": "短暂的"
            }
        ]
    }
}
```

### 6. 统计报告

#### 6.1 获取周报

**请求**
```http
GET /reports/weekly
Authorization: Bearer <access_token>
Query Parameters:
- start_date: 2024-01-14 (可选，默认为上周)
```

**响应**
```json
{
    "code": 200,
    "data": {
        "study_time": 480,
        "words_learned": 150,
        "words_reviewed": 300,
        "accuracy_rate": 0.85,
        "daily_progress": [
            {
                "date": "2024-01-14",
                "study_time": 60,
                "words_count": 20
            }
        ],
        "weak_words": [
            {
                "word": "ephemeral",
                "accuracy_rate": 0.6
            }
        ]
    }
}
```

### 7. 用户水平评估

#### 7.1 开始水平评估

**请求**
```http
POST /vocabulary-books/{book_id}/assessment/start
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "question_count": 20  // 可选，默认20题
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "assessment_id": 1,
        "questions": [
            {
                "id": 1,
                "word": "ephemeral",
                "options": ["短暂的", "永恒的", "美丽的", "神秘的"],
                "type": "multiple_choice"
            }
        ]
    }
}
```

#### 7.2 提交评估答案

**请求**
```http
POST /vocabulary-books/{book_id}/assessment/{assessment_id}/submit
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "answers": [
        {
            "question_id": 1,
            "answer": "短暂的"
        }
    ]
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "level_score": 4.2,
        "assessment_details": {
            "total_questions": 20,
            "correct_count": 16,
            "accuracy_rate": 0.8,
            "suggested_level": "intermediate"
        }
    }
}
```

### 8. 单词关系管理

#### 8.1 添加单词关系

**请求**
```http
POST /words/{word_id}/relations
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "target_word_id": 2,
    "relation_type": "synonym"  // synonym, antonym, similar
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "source_word": {
            "id": 1,
            "word": "ephemeral"
        },
        "target_word": {
            "id": 2,
            "word": "temporary"
        },
        "relation_type": "synonym"
    }
}
```

#### 8.2 获取单词关系

**请求**
```http
GET /words/{word_id}/relations
Authorization: Bearer <access_token>
Query Parameters:
- relation_type: synonym (可选，筛选关系类型)
```

**响应**
```json
{
    "code": 200,
    "data": {
        "relations": [
            {
                "id": 1,
                "target_word": {
                    "id": 2,
                    "word": "temporary"
                },
                "relation_type": "synonym"
            }
        ]
    }
}
```

### 9. 学习计划

#### 9.1 创建学习计划

**请求**
```http
POST /learning-plans
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "book_id": 1,
    "daily_word_count": 20,
    "target_date": "2024-03-01"
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "book_id": 1,
        "daily_word_count": 20,
        "target_date": "2024-03-01",
        "total_words": 500,
        "estimated_completion_date": "2024-02-28"
    }
}
```

#### 9.2 更新学习计划

**请求**
```http
PUT /learning-plans/{plan_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "daily_word_count": 25,
    "target_date": "2024-03-15"
}
```

**响应**
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "daily_word_count": 25,
        "target_date": "2024-03-15",
        "estimated_completion_date": "2024-03-10"
    }
}
``` 