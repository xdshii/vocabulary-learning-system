from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.services.test_service import TestService
from app.models.user import User
from app.models.word import Word
from app.models.vocabulary import VocabularyBook
from app.models.learning import LearningRecord
from app.models.test import Test, TestQuestion, TestRecord, TestAnswer
from app import db
from . import test_bp
from datetime import datetime, timedelta
import random

@test_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_test():
    """生成测试"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    data = request.get_json()
    
    if not all(k in data for k in ('book_id', 'question_count', 'test_type')):
        return jsonify({
            'code': 400001,
            'message': '缺少必要参数'
        }), 400
    
    book = VocabularyBook.query.get_or_404(data['book_id'])
    if book.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此词汇书'
        }), 403
    
    # 获取词汇书中的所有单词
    words = book.words
    if len(words) < data['question_count']:
        return jsonify({
            'code': 400001,
            'message': '词汇书中的单词数量不足'
        }), 400
    
    # 随机选择单词
    selected_words = random.sample(words, data['question_count'])
    
    # 创建测试
    test = Test(
        user_id=current_user.id,
        book_id=data['book_id'],
        name=f'Generated Test - {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}',
        total_questions=data['question_count'],
        test_type=data['test_type']
    )
    db.session.add(test)
    db.session.commit()  # 先提交测试记录以获取 test.id
    
    # 创建测试题目
    for word in selected_words:
        # 为每个单词生成选项
        options = [word.definition]  # 正确答案
        wrong_options = [w.definition for w in words if w != word]
        options.extend(random.sample(wrong_options, min(3, len(wrong_options))))
        random.shuffle(options)
        
        question = TestQuestion(
            test_id=test.id,
            word_id=word.id,
            question_type=data['test_type'],
            question=f"What is the meaning of '{word.text}'?",
            options=options,
            correct_answer=word.definition
        )
        db.session.add(question)
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'data': {
            'id': test.id,
            'questions': [{
                'id': q.id,
                'question': q.question,
                'options': q.options
            } for q in test.questions]
        }
    })

@test_bp.route('', methods=['POST'])
@jwt_required()
def create_test():
    """创建测试"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    data = request.get_json()
    
    if not all(k in data for k in ('name', 'book_id', 'duration', 'total_questions', 'pass_score')):
        return jsonify({
            'code': 400001,
            'message': '缺少必要参数'
        }), 400
        
    book = VocabularyBook.query.get_or_404(data['book_id'])
    if book.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此词汇书'
        }), 403
        
    test = Test(
        user_id=current_user.id,
        book_id=data['book_id'],
        name=data['name'],
        description=data.get('description'),
        duration=data['duration'],
        total_questions=data['total_questions'],
        pass_score=data['pass_score']
    )
    db.session.add(test)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'data': test.to_dict()
    })

@test_bp.route('', methods=['GET'])
@jwt_required()
def get_tests():
    """获取测试列表"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    tests = Test.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'code': 200,
        'data': {
            'items': [test.to_dict() for test in tests]
        }
    })

@test_bp.route('/<int:test_id>', methods=['GET'])
@jwt_required()
def get_test_detail(test_id):
    """获取测试详情"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此测试'
        }), 403
        
    return jsonify({
        'code': 200,
        'data': test.to_dict(with_questions=True)
    })

@test_bp.route('/<int:test_id>', methods=['PUT'])
@jwt_required()
def update_test(test_id):
    """更新测试"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权修改此测试'
        }), 403
        
    data = request.get_json()
    for field in ['name', 'duration', 'total_questions', 'pass_score']:
        if field in data:
            setattr(test, field, data[field])
            
    db.session.commit()
    return jsonify({
        'code': 200,
        'data': test.to_dict()
    })

@test_bp.route('/<int:test_id>', methods=['DELETE'])
@jwt_required()
def delete_test(test_id):
    """删除测试"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权删除此测试'
        }), 403
        
    db.session.delete(test)
    db.session.commit()
    return jsonify({
        'code': 200,
        'message': '测试删除成功'
    })

@test_bp.route('/<int:test_id>/questions', methods=['POST'])
@jwt_required()
def add_test_question(test_id):
    """添加测试题目"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此测试'
        }), 403
        
    data = request.get_json()
    required_fields = ['word_id', 'question_type', 'question', 'options', 'correct_answer']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'code': 400001,
                'message': f'缺少必要参数: {field}'
            }), 400
            
    question = TestQuestion(
        test_id=test_id,
        word_id=data['word_id'],
        question_type=data['question_type'],
        question=data['question'],
        options=data['options'],
        correct_answer=data['correct_answer']
    )
    db.session.add(question)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'data': question.to_dict()
    })

@test_bp.route('/<int:test_id>/questions', methods=['GET'])
@jwt_required()
def get_test_questions(test_id):
    """获取测试题目列表"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此测试'
        }), 403
        
    return jsonify({
        'code': 200,
        'data': {
            'items': [question.to_dict() for question in test.questions]
        }
    })

@test_bp.route('/<int:test_id>/questions/<int:question_id>', methods=['PUT'])
@jwt_required()
def update_test_question(test_id, question_id):
    """更新测试题目"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此测试'
        }), 403
        
    question = TestQuestion.query.get_or_404(question_id)
    if question.test_id != test_id:
        return jsonify({
            'code': 404,
            'message': '题目不存在'
        }), 404
        
    data = request.get_json()
    for field in ['question_type', 'question', 'options', 'correct_answer']:
        if field in data:
            setattr(question, field, data[field])
            
    db.session.commit()
    return jsonify({
        'code': 200,
        'data': question.to_dict()
    })

@test_bp.route('/<int:test_id>/questions/<int:question_id>', methods=['DELETE'])
@jwt_required()
def delete_test_question(test_id, question_id):
    """删除测试题目"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此测试'
        }), 403
        
    question = TestQuestion.query.get_or_404(question_id)
    if question.test_id != test_id:
        return jsonify({
            'code': 404,
            'message': '题目不存在'
        }), 404
        
    db.session.delete(question)
    db.session.commit()
    return jsonify({
        'code': 200,
        'message': '题目删除成功'
    })

@test_bp.route('/<int:test_id>/start', methods=['POST'])
@jwt_required()
def start_test(test_id):
    """开始测试"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此测试'
        }), 403
        
    if test.start_time:
        return jsonify({
            'code': 400001,
            'message': '测试已经开始'
        }), 400
        
    test.start_time = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'data': {
            'test_id': test.id,
            'start_time': test.start_time.isoformat(),
            'duration': test.duration,
            'questions': [question.to_dict(include_answer=False) for question in test.questions]
        }
    })

@test_bp.route('/<int:test_id>/submit', methods=['POST'])
@jwt_required()
def submit_test(test_id):
    """提交测试答案"""
    # 首先验证请求数据格式
    data = request.get_json()
    if not data or 'answers' not in data:
        return jsonify({
            'code': 400001,
            'message': '缺少必要参数'
        }), 400
    
    answers = data['answers']
    if not isinstance(answers, list):
        return jsonify({
            'code': 400001,
            'message': '答案格式错误'
        }), 400

    # 然后验证用户权限
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此测试'
        }), 403
    
    # 创建测试记录
    test_record = TestRecord(
        test_id=test_id,
        user_id=current_user.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow()
    )
    db.session.add(test_record)
    db.session.flush()  # 获取test_record.id
    
    # 保存答案
    correct_count = 0
    for answer in answers:
        if not isinstance(answer, dict) or 'question_id' not in answer or 'answer' not in answer:
            continue
            
        question = TestQuestion.query.get(answer['question_id'])
        if not question or question.test_id != test_id:
            continue
            
        is_correct = question.correct_answer == answer['answer']
        if is_correct:
            correct_count += 1
            
        test_answer = TestAnswer(
            test_record_id=test_record.id,
            question_id=answer['question_id'],
            answer=answer['answer'],
            is_correct=is_correct
        )
        db.session.add(test_answer)
    
    # 计算得分
    total_questions = len(test.questions)
    score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    test_record.score = score
    test_record.correct_count = correct_count
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'data': {
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'pass_score': test.pass_score,
            'is_passed': score >= test.pass_score
        }
    })

@test_bp.route('/<int:test_id>/results', methods=['GET'])
@jwt_required()
def get_test_results(test_id):
    """获取测试结果"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此测试'
        }), 403
    
    records = TestRecord.query.filter_by(
        test_id=test_id,
        user_id=current_user.id
    ).order_by(TestRecord.created_at.desc()).all()
    
    return jsonify({
        'code': 200,
        'data': {
            'items': [{
                'id': record.id,
                'score': record.score,
                'correct_count': record.correct_count,
                'total_questions': len(test.questions),
                'start_time': record.start_time.isoformat(),
                'end_time': record.end_time.isoformat(),
                'is_passed': record.score >= test.pass_score
            } for record in records]
        }
    })

@test_bp.route('/history', methods=['GET'])
@jwt_required()
def get_test_history():
    """获取测试历史"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    records = TestRecord.query.filter_by(
        user_id=current_user.id
    ).order_by(TestRecord.created_at.desc()).all()
    
    return jsonify({
        'code': 200,
        'data': {
            'items': [{
                'id': record.id,
                'test_id': record.test_id,
                'test_name': record.test.name,
                'score': record.score,
                'correct_count': record.correct_count,
                'total_questions': len(record.test.questions),
                'start_time': record.start_time.isoformat(),
                'end_time': record.end_time.isoformat(),
                'is_passed': record.score >= record.test.pass_score
            } for record in records]
        }
    })

@test_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_test_statistics():
    """获取测试统计信息"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    # 获取所有测试记录
    records = TestRecord.query.filter_by(
        user_id=current_user.id
    ).all()
    
    # 计算统计数据
    total_tests = len(records)
    if total_tests == 0:
        return jsonify({
            'code': 200,
            'data': {
                'total_tests': 0,
                'average_score': 0,
                'pass_rate': 0,
                'total_questions': 0,
                'correct_rate': 0
            }
        })
    
    total_score = sum(record.score for record in records)
    passed_tests = sum(1 for record in records if record.score >= record.test.pass_score)
    total_questions = sum(len(record.test.questions) for record in records)
    total_correct = sum(record.correct_count for record in records)
    
    return jsonify({
        'code': 200,
        'data': {
            'total_tests': total_tests,
            'average_score': total_score / total_tests,
            'pass_rate': (passed_tests / total_tests) * 100,
            'total_questions': total_questions,
            'correct_rate': (total_correct / total_questions) * 100 if total_questions > 0 else 0
        }
    })

@test_bp.route('/<int:test_id>/questions/<int:question_id>', methods=['GET'])
@jwt_required()
def get_test_question(test_id, question_id):
    """获取测试题目详情"""
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        return jsonify({
            'code': 401002,
            'message': '用户不存在'
        }), 401
    
    test = Test.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({
            'code': 403001,
            'message': '无权访问此测试'
        }), 403
        
    question = TestQuestion.query.get_or_404(question_id)
    if question.test_id != test_id:
        return jsonify({
            'code': 404,
            'message': '题目不存在'
        }), 404
        
    return jsonify({
        'code': 200,
        'data': question.to_dict()
    }) 