# 词汇学习系统API文档

## 1. 概述

### 1.1 基础信息
- 基础URL: `/api/v1`
- 响应格式: JSON
- 认证方式: JWT (JSON Web Token)

### 1.2 通用响应格式
```json
{
    "code": 200,
    "message": "操作成功",
    "data": {
        // 具体的响应数据
    }
}
```

### 1.3 错误码说明
| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或认证失败 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 2. 认证接口

### 2.1 用户登录
```
POST /auth/login
```

#### 请求参数
| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

#### 响应示例
```json
{
    "code": 200,
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
        "token_type": "Bearer",
        "expires_in": 3600
    }
}
```

## 3. 词汇学习接口

### 3.1 创建学习目标
```
POST /vocabulary/goals
```

#### 请求头
```
Authorization: Bearer {token}
```

#### 请求参数
| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| book_id | integer | 是 | 单词书ID |
| daily_words | integer | 是 | 每日学习单词数 |
| target_date | string | 是 | 目标完成日期(ISO8601格式) |

#### 响应示例
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "book_id": 1,
        "daily_words": 20,
        "target_date": "2024-03-20T00:00:00",
        "created_at": "2024-02-20T10:00:00"
    }
}
```

### 3.2 获取复习计划
```
GET /vocabulary/review/plan
```

#### 请求头
```
Authorization: Bearer {token}
```

#### 响应示例
```json
{
    "code": 200,
    "data": [
        {
            "id": 1,
            "word": {
                "word": "ubiquitous",
                "pronunciation": "/juːˈbɪkwɪtəs/",
                "definition": "存在于所有地方的，普遍存在的",
                "example": "Mobile phones have become ubiquitous in modern society."
            },
            "scheduled_time": "2024-02-20T15:00:00",
            "status": "pending"
        }
    ]
}
```

### 3.3 完成复习
```
POST /vocabulary/review/complete/{plan_id}
```

#### 请求头
```
Authorization: Bearer {token}
```

#### 响应示例
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "status": "completed",
        "actual_time": "2024-02-20T15:30:00",
        "next_review_time": "2024-02-22T15:30:00"
    }
}
```

## 4. 数据统计接口

### 4.1 获取学习统计
```
GET /vocabulary/statistics
```

#### 请求头
```
Authorization: Bearer {token}
```

#### 响应示例
```json
{
    "code": 200,
    "data": {
        "total_words": 500,
        "mastered_words": 200,
        "learning_words": 100,
        "review_accuracy": 85.5,
        "daily_streak": 7
    }
}
```

## 5. 错误响应示例

### 5.1 参数错误
```json
{
    "code": 400,
    "message": "参数错误",
    "errors": {
        "daily_words": ["每日单词数必须大于0"],
        "target_date": ["目标日期格式不正确"]
    }
}
```

### 5.2 认证错误
```json
{
    "code": 401,
    "message": "认证失败",
    "error": "无效的token"
}
``` 