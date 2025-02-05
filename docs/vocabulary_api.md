# 单词管理系统 API 文档

## 基础信息

- 基础URL: `/api/v1/vocabulary`
- 所有请求和响应均使用 JSON 格式
- 所有接口都需要 JWT 认证，在请求头中添加 `Authorization: Bearer <token>`

## 错误码说明

| 错误码 | 描述 |
|--------|------|
| 400001 | 参数缺失或格式错误 |
| 400002 | 无效的学习状态 |
| 404001 | 单词书不存在 |
| 404002 | 单词不存在 |

## API 接口

### 1. 单词书管理

#### 1.1 获取单词书列表

**请求**
```http
GET /books
Authorization: Bearer <token>
```

**响应**
```json
{
    "code": 200,
    "data": [
        {
            "id": 1,
            "name": "IELTS核心词汇",
            "description": "雅思考试常见词汇集合",
            "level": "advanced",
            "total_words": 100
        }
    ]
}
```

#### 1.2 创建单词书

**请求**
```http
POST /books
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "IELTS核心词汇",
    "description": "雅思考试常见词汇集合",
    "level": "advanced"
}
```

**响应**
```json
{
    "code": 200,
    "message": "单词书创建成功",
    "data": {
        "id": 1,
        "name": "IELTS核心词汇",
        "description": "雅思考试常见词汇集合",
        "level": "advanced"
    }
}
```

### 2. 单词管理

#### 2.1 获取单词列表

**请求**
```http
GET /books/{book_id}/words?page=1&per_page=20
Authorization: Bearer <token>
```

**响应**
```json
{
    "code": 200,
    "data": {
        "words": [
            {
                "id": 1,
                "word": "ubiquitous",
                "pronunciation": "/juːˈbɪkwɪtəs/",
                "definition": "存在于所有地方的，普遍存在的",
                "example": "Mobile phones have become ubiquitous in modern society."
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 100,
            "pages": 5
        }
    }
}
```

#### 2.2 添加单词

**请求**
```http
POST /books/{book_id}/words
Authorization: Bearer <token>
Content-Type: application/json

{
    "word": "ubiquitous",
    "pronunciation": "/juːˈbɪkwɪtəs/",
    "definition": "存在于所有地方的，普遍存在的",
    "example": "Mobile phones have become ubiquitous in modern society."
}
```

**响应**
```json
{
    "code": 200,
    "message": "单词添加成功",
    "data": {
        "id": 1,
        "word": "ubiquitous",
        "pronunciation": "/juːˈbɪkwɪtəs/",
        "definition": "存在于所有地方的，普遍存在的",
        "example": "Mobile phones have become ubiquitous in modern society."
    }
}
```

### 3. 学习记录

#### 3.1 获取学习进度

**请求**
```http
GET /learning/progress
Authorization: Bearer <token>
```

**响应**
```json
{
    "code": 200,
    "data": {
        "new": 50,
        "learning": 30,
        "mastered": 20
    }
}
```

#### 3.2 更新单词状态

**请求**
```http
PUT /words/{word_id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
    "status": "learning"  // new, learning, mastered
}
```

**响应**
```json
{
    "code": 200,
    "message": "状态更新成功"
}
```

### 4. 搜索功能

#### 4.1 搜索单词

**请求**
```http
GET /words/search?keyword=test&book_id=1&level=advanced&status=learning&page=1&per_page=20
Authorization: Bearer <token>
```

**参数说明**
- `keyword`: 搜索关键词（可选）
- `book_id`: 单词书ID（可选）
- `level`: 难度级别（可选）
- `status`: 学习状态（可选）
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认20）

**响应**
```json
{
    "code": 200,
    "data": {
        "words": [
            {
                "id": 1,
                "word": "ubiquitous",
                "pronunciation": "/juːˈbɪkwɪtəs/",
                "definition": "存在于所有地方的，普遍存在的",
                "example": "Mobile phones have become ubiquitous in modern society.",
                "book": {
                    "id": 1,
                    "name": "IELTS核心词汇",
                    "level": "advanced"
                },
                "learning_status": "learning"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 100,
            "pages": 5
        }
    }
}
```

## 注意事项

1. 所有接口都需要有效的JWT Token
2. 分页参数page从1开始
3. 搜索接口默认按学习次数降序排序
4. 单词状态只能是：new、learning、mastered
5. 响应中的code为200表示成功，其他表示错误 