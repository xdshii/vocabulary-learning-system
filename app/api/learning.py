from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.models.learning import LearningRecord, LearningGoal
from app.models.learning_plan import LearningPlan
from app.models.vocabulary import VocabularyBook
from app.models.word import Word
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
from .auth import token_required
from . import learning_bp

@learning_bp.route('/goals', methods=['POST'])
@token_required
def create_learning_goal(current_user):
    """创建学习目标"""
    try:
        data = request.get_json()
        
        if not all(k in data for k in ('book_id', 'daily_words', 'target_date')):
            return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
            
        # 创建学习目标
        goal = LearningGoal(
            user_id=current_user.id,
            book_id=data['book_id'],
            daily_word_count=data['daily_words'],
            target_date=datetime.fromisoformat(data['target_date'].replace('Z', '+00:00')),
            status='active'
        )
        
        db.session.add(goal)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'data': goal.to_dict()
        })
    except ValueError as e:
        return jsonify({
            'code': 400,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@learning_bp.route('/goals', methods=['GET'])
@token_required
def get_learning_goals(current_user):
    """获取学习目标列表"""
    goals = db.session.query(LearningGoal).filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'code': 200,
        'data': {
            'items': [goal.to_dict() for goal in goals]
        }
    })

@learning_bp.route('/review/plan', methods=['GET'])
@token_required
def get_review_plan(current_user):
    """获取复习计划"""
    try:
        # 获取需要复习的记录
        records = db.session.query(LearningRecord).filter(
            LearningRecord.user_id == current_user.id,
            LearningRecord.status == 'learning',
            LearningRecord.next_review_time <= datetime.utcnow()
        ).all()

        # 获取单词详情
        words = []
        for record in records:
            word = db.session.get(Word, record.word_id)
            if word:
                word_dict = word.to_dict()
                word_dict['record_id'] = record.id
                words.append(word_dict)

        return jsonify({
            'code': 200,
            'data': {
                'words': words,
                'total': len(words)
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@learning_bp.route('/review/complete/<int:record_id>', methods=['POST'])
@token_required
def complete_review(current_user, record_id):
    """完成复习"""
    try:
        record = db.session.get(LearningRecord, record_id)
        if not record:
            return jsonify({'code': 404, 'message': '学习记录不存在'}), 404
            
        if record.user_id != current_user.id:
            return jsonify({'code': 403, 'message': '无权访问此学习记录'}), 403

        data = request.get_json()
        result = data.get('result')
        
        if result not in ['remembered', 'forgotten']:
            return jsonify({'code': 400, 'message': '无效的复习结果'}), 400

        # 更新复习次数和下次复习时间
        record.review_count += 1
        if result == 'remembered':
            # 根据艾宾浩斯遗忘曲线设置下次复习时间
            intervals = [1, 2, 4, 7, 15, 30, 60]  # 复习间隔(天)
            next_interval = intervals[min(record.review_count, len(intervals) - 1)]
            record.next_review_time = datetime.utcnow() + timedelta(days=next_interval)
            if record.review_count >= len(intervals):
                record.status = 'mastered'  # 掌握了
        else:
            # 如果忘记了,明天再复习
            record.next_review_time = datetime.utcnow() + timedelta(days=1)

        db.session.commit()
        return jsonify({
            'code': 200,
            'data': record.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@learning_bp.route('/plans', methods=['POST'])
@token_required
def create_learning_plan(current_user):
    """创建学习计划"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['book_id', 'daily_words', 'start_date']):
            return jsonify({
                'code': 400,
                'message': '缺少必要参数'
            }), 400
            
        # 创建学习计划
        plan = LearningPlan(
            user_id=current_user.id,
            book_id=data['book_id'],
            daily_words=data['daily_words'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if 'end_date' in data else None,
            status='active'
        )
        
        db.session.add(plan)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'data': plan.to_dict()
        })
    except ValueError as e:
        return jsonify({
            'code': 400,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@learning_bp.route('/plans', methods=['GET'])
@token_required
def get_learning_plans(current_user):
    """获取学习计划列表"""
    try:
        plans = db.session.query(LearningPlan).filter_by(
            user_id=current_user.id,
            status='active'
        ).all()

        return jsonify({
            'code': 200,
            'data': {
                'plans': [plan.to_dict() for plan in plans]
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@learning_bp.route('/plans/<int:plan_id>', methods=['PUT'])
@token_required
def update_learning_plan(current_user, plan_id):
    """更新学习计划"""
    try:
        plan = db.session.get(LearningPlan, plan_id)
        if not plan:
            return jsonify({'code': 404, 'message': '学习计划不存在'}), 404
            
        if plan.user_id != current_user.id:
            return jsonify({'code': 403, 'message': '无权访问此学习计划'}), 403

        data = request.get_json()
        if 'daily_words' in data:
            plan.daily_words = data['daily_words']
        if 'status' in data:
            plan.status = data['status']

        db.session.commit()
        return jsonify({
            'code': 200,
            'data': plan.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@learning_bp.route('/records', methods=['POST'])
@token_required
def create_learning_record(current_user):
    """创建学习记录"""
    try:
        data = request.get_json()
        book_id = data.get('book_id')
        word_id = data.get('word_id')
        status = data.get('status', 'learning')

        if not book_id or not word_id:
            return jsonify({
                'code': 400,
                'message': '缺少必要参数'
            }), 400

        # 检查是否已存在记录
        record = db.session.query(LearningRecord).filter_by(
            user_id=current_user.id,
            book_id=book_id,
            word_id=word_id
        ).first()

        if record:
            record.status = status
            record.updated_at = datetime.utcnow()
        else:
            record = LearningRecord(
                user_id=current_user.id,
                book_id=book_id,
                word_id=word_id,
                status=status
            )
            db.session.add(record)

        db.session.commit()
        return jsonify({
            'code': 200,
            'data': record.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@learning_bp.route('/records', methods=['GET'])
@token_required
def get_learning_records(current_user):
    """获取学习记录列表"""
    records = db.session.query(LearningRecord).filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'code': 200,
        'data': {
            'items': [record.to_dict() for record in records]
        }
    })

@learning_bp.route('/records/<int:record_id>', methods=['PUT'])
@token_required
def update_learning_record(current_user, record_id):
    """更新学习记录"""
    try:
        record = db.session.get(LearningRecord, record_id)
        if not record:
            return jsonify({'code': 404, 'message': '学习记录不存在'}), 404
            
        if record.user_id != current_user.id:
            return jsonify({'code': 403, 'message': '无权访问此学习记录'}), 403

        data = request.get_json()
        if 'status' in data:
            record.status = data['status']
            record.updated_at = datetime.utcnow()

        db.session.commit()
        return jsonify({
            'code': 200,
            'data': record.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@learning_bp.route('/statistics', methods=['GET'])
@token_required
def get_learning_statistics(current_user):
    """获取学习统计"""
    try:
        # 获取总单词数
        total_words = db.session.query(func.count(LearningRecord.id)).filter_by(
            user_id=current_user.id
        ).scalar()

        # 获取已掌握的单词数
        mastered_words = db.session.query(func.count(LearningRecord.id)).filter_by(
            user_id=current_user.id,
            status='mastered'
        ).scalar()

        # 获取正在学习的单词数
        learning_words = db.session.query(func.count(LearningRecord.id)).filter_by(
            user_id=current_user.id,
            status='learning'
        ).scalar()

        # 获取今日学习的单词数
        today = datetime.utcnow().date()
        today_words = db.session.query(func.count(LearningRecord.id)).filter(
            LearningRecord.user_id == current_user.id,
            func.date(LearningRecord.created_at) == today
        ).scalar()

        # 获取新学习的单词数(今天创建的记录)
        new_words = db.session.query(func.count(LearningRecord.id)).filter(
            LearningRecord.user_id == current_user.id,
            func.date(LearningRecord.created_at) == today,
            LearningRecord.review_count == 0
        ).scalar()

        # 计算平均复习次数
        avg_review_count = db.session.query(func.avg(LearningRecord.review_count)).filter(
            LearningRecord.user_id == current_user.id
        ).scalar()

        return jsonify({
            'code': 200,
            'data': {
                'total': total_words,
                'mastered': mastered_words,
                'learning': learning_words,
                'today': today_words,
                'new_words': new_words,
                'avg_review_count': round(avg_review_count if avg_review_count else 0, 2)
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@learning_bp.route('/review/list', methods=['GET'])
@token_required
def get_review_list(current_user):
    """获取复习列表"""
    try:
        # 获取需要复习的记录
        records = db.session.query(LearningRecord).filter(
            LearningRecord.user_id == current_user.id,
            LearningRecord.status == 'learning',
            LearningRecord.next_review_time <= datetime.utcnow()
        ).all()

        # 获取单词详情
        words = []
        for record in records:
            word = db.session.get(Word, record.word_id)
            if word:
                word_dict = word.to_dict()
                word_dict['record_id'] = record.id
                words.append(word_dict)

        # 直接返回列表
        return jsonify({
            'code': 200,
            'data': words
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@learning_bp.route('/review/submit', methods=['POST'])
@token_required
def submit_review_result(current_user):
    """提交复习结果"""
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        result = data.get('result')

        if not record_id or not result:
            return jsonify({
                'code': 400,
                'message': '缺少必要参数'
            }), 400

        record = db.session.get(LearningRecord, record_id)
        if not record:
            return jsonify({'code': 404, 'message': '学习记录不存在'}), 404
            
        if record.user_id != current_user.id:
            return jsonify({'code': 403, 'message': '无权访问此学习记录'}), 403

        # 修改结果映射
        result_map = {
            'correct': 'remembered',
            'incorrect': 'forgotten'
        }
        mapped_result = result_map.get(result)
        if not mapped_result:
            return jsonify({'code': 400, 'message': '无效的复习结果'}), 400

        # 更新复习次数和下次复习时间
        record.review_count += 1
        if mapped_result == 'remembered':
            # 根据艾宾浩斯遗忘曲线设置下次复习时间
            intervals = [1, 2, 4, 7, 15, 30, 60]  # 复习间隔(天)
            next_interval = intervals[min(record.review_count, len(intervals) - 1)]
            record.next_review_time = datetime.utcnow() + timedelta(days=next_interval)
            if record.review_count >= len(intervals):
                record.status = 'mastered'  # 掌握了
        else:
            # 如果忘记了,明天再复习
            record.next_review_time = datetime.utcnow() + timedelta(days=1)

        db.session.commit()
        return jsonify({
            'code': 200,
            'data': record.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500 