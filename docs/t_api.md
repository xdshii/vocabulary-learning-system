# 智能词汇学习系统 API 测试文档

## 基础信息

- 基础URL: `/api/v1`
- 所有请求和响应均使用 JSON 格式
- 认证使用 Bearer Token 方式

## 错误码说明

| 错误码 | 描述 | 测试状态 |
|--------|------|----------|
| 400001 | 参数缺失或格式错误 | ✅ 已测试 |
| 400002 | 资源不存在 | ✅ 已测试 |
| 400003 | 权限不足 | ✅ 已测试 |
| 400004 | 操作失败 | ✅ 已测试 |
| 403001 | 账号已被禁用 | ✅ 已测试 |
| 404001 | 用户不存在 | ✅ 已测试 |

## API 接口测试状态

### 1. 用户管理

#### 1.1 用户注册 ✅
- 测试用例: `test_register`
- 覆盖场景:
  - 正常注册
  - 用户名已存在
  - 邮箱已存在
  - 密码格式错误

#### 1.2 用户登录 ✅
- 测试用例: `test_password_login`
- 覆盖场景:
  - 正常登录
  - 密码错误
  - 用户不存在

#### 1.3 验证码登录 ⚠️
- 测试用例: `test_verify_code`
- 存在问题:
  - 状态码不一致(期望400,实际200)
- 待优化项:
  - 统一API响应格式

### 2. 词汇书管理

#### 2.1 创建词汇书 ✅
- 测试用例: `test_create_book`
- 覆盖场景:
  - 正常创建
  - 缺少必填字段
  - 权限验证

#### 2.2 获取词汇书列表 ✅
- 测试用例: `test_get_books`
- 覆盖场景:
  - 分页获取
  - 空列表
  - 权限验证

### 3. 单词管理

#### 3.1 添加单词 ✅
- 测试用例: `test_add_single_word`
- 覆盖场景:
  - 单个添加
  - 批量添加
  - 重复添加
  - 参数验证

#### 3.2 获取单词列表 ✅
- 测试用例: `test_get_words`
- 覆盖场景:
  - 分页获取
  - 关键词搜索
  - 排序功能

### 4. 学习管理

#### 4.1 创建学习记录 ❌
- 测试覆盖率: 0%
- 待补充测试:
  - 正常创建
  - 参数验证
  - 重复记录处理

#### 4.2 获取学习进度 ✅
- 测试用例: `test_get_learning_progress`
- 覆盖场景:
  - 总体进度
  - 今日学习
  - 连续天数

### 5. 测试系统

#### 5.1 生成测试 ✅
- 测试用例: `test_create_test`
- 覆盖场景:
  - 不同类型测试
  - 参数验证
  - 随机性验证

#### 5.2 提交测试答案 ✅
- 测试用例: `test_submit_test`
- 覆盖场景:
  - 正确答案
  - 错误答案
  - 重复提交

## API 测试统计

### 测试覆盖情况
- 总接口数: 25
- 已测试: 22
- 部分测试: 2
- 未测试: 1
- 覆盖率: 88%

### 测试用例分布
- 认证相关: 15个
- 词汇管理: 35个
- 学习记录: 12个
- 测试系统: 25个
- 其他模块: 42个

### 发现的主要问题
1. 验证码验证接口响应不一致
2. 学习记录模块测试不足
3. 部分接口缺少边界测试
4. SQLAlchemy警告需要处理 