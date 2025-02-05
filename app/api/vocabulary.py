from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.learning import LearningRecord, LearningGoal
from app.models.learning import ReviewPlan
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import random
from .auth import token_required
from . import vocabulary_bp  # 从__init__.py导入蓝图

@vocabulary_bp.route('/books', methods=['GET'])
@token_required
def get_books(current_user):
    """获取词汇书列表"""
    books = db.session.query(VocabularyBook).filter_by(user_id=current_user.id).all()
    return jsonify({
        'code': 200,
        'data': {
            'items': [book.to_dict() for book in books],
            'total': len(books)
        }
    })

@vocabulary_bp.route('/books', methods=['POST'])
@token_required
def create_book(current_user):
    """创建词汇书"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({
                'code': 400001,
                'message': '缺少必要参数'
            }), 400

        book = VocabularyBook(
            name=data['name'],
            description=data.get('description', ''),
            level=data.get('level', 'beginner'),
            user_id=current_user.id,
            tags=data.get('tags', [])
        )
        db.session.add(book)
        db.session.commit()

        return jsonify({
            'code': 200,
            'data': book.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 400004,
            'message': str(e)
        }), 400

@vocabulary_bp.route('/books/<int:book_id>', methods=['GET'])
@token_required
def get_book_detail(current_user, book_id):
    """获取词汇书详情"""
    book = db.session.get(VocabularyBook, book_id)
    
    if not book:
        return jsonify({'code': 404, 'message': '词汇书不存在'}), 404
    
    if book.user_id != current_user.id:
        return jsonify({'code': 403001, 'message': '无权访问此词汇书'}), 403
    
    return jsonify({
        'code': 200,
        'data': book.to_dict()
    })

@vocabulary_bp.route('/books/<int:book_id>', methods=['PUT'])
@token_required
def update_book(current_user, book_id):
    """更新词汇书"""
    book = db.session.get(VocabularyBook, book_id)
    if not book:
        return jsonify({'code': 404, 'message': '词汇书不存在'}), 404
    
    if book.user_id != current_user.id:
        return jsonify({'code': 403001, 'message': '无权修改此词汇书'}), 403
    
    data = request.get_json()
    
    if 'name' in data:
        book.name = data['name']
    if 'description' in data:
        book.description = data['description']
    if 'level' in data:
        book.level = data['level']
    if 'tags' in data:
        book.tags = ','.join(data['tags']) if data['tags'] else None
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'data': book.to_dict()
    })

@vocabulary_bp.route('/books/<int:book_id>', methods=['DELETE'])
@token_required
def delete_book(current_user, book_id):
    """删除词汇书"""
    book = db.session.get(VocabularyBook, book_id)
    if not book:
        return jsonify({'code': 404, 'message': '词汇书不存在'}), 404
    
    if book.user_id != current_user.id:
        return jsonify({'code': 403001, 'message': '无权删除此词汇书'}), 403
    
    db.session.delete(book)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '词汇书删除成功'
    })

@vocabulary_bp.route('/books/<int:book_id>/words', methods=['POST'])
@token_required
def add_words(current_user, book_id):
    """添加单词"""
    book = db.session.get(VocabularyBook, book_id)
    if not book:
        return jsonify({'code': 404, 'message': '词汇书不存在'}), 404
    
    if book.user_id != current_user.id:
        return jsonify({'code': 403001, 'message': '无权访问此词汇书'}), 403

    data = request.get_json()
    
    if 'word_ids' in data:  # 批量添加
        word_ids = data['word_ids']
        words = db.session.query(Word).filter(Word.id.in_(word_ids)).all()
        if len(words) != len(word_ids):
            return jsonify({'code': 400001, 'message': '部分单词不存在'}), 400
            
        max_order = db.session.query(db.func.max(WordRelation.order)).filter_by(book_id=book.id).scalar() or 0
        
        word_relations = []
        for i, word in enumerate(words):
            word_relation = WordRelation(
                word_id=word.id,
                book_id=book.id,
                order=max_order + i + 1
            )
            word_relations.append(word_relation)
        
        db.session.bulk_save_objects(word_relations)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '单词添加成功'
        })
    
    elif 'text' in data:  # 单个单词
        word = db.session.query(Word).filter_by(text=data['text']).first()
        if not word:
            word = Word(
                text=data['text'],
                phonetic=data.get('phonetic'),
                definition=data.get('definition'),
                example=data.get('example')
            )
            db.session.add(word)
            db.session.flush()

        max_order = db.session.query(db.func.max(WordRelation.order)).filter_by(book_id=book.id).scalar() or 0
        
        word_relation = WordRelation(
            word_id=word.id,
            book_id=book.id,
            order=max_order + 1
        )
        db.session.add(word_relation)
        db.session.commit()

        return jsonify({
            'code': 200,
            'data': word.to_dict()
        })
    
    else:
        return jsonify({'code': 400001, 'message': '缺少必填字段'}), 400

@vocabulary_bp.route('/books/<int:book_id>/words', methods=['GET'])
@token_required
def get_book_words(current_user, book_id):
    """获取指定单词书的单词列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '')
    
    book = db.session.get(VocabularyBook, book_id)
    if not book:
        return jsonify({'code': 404, 'message': '词汇书不存在'}), 404
        
    if book.user_id != current_user.id:
        return jsonify({'code': 403, 'message': '无权访问此词汇书'}), 403
    
    # 使用join查询获取单词列表
    query = db.session.query(Word).join(WordRelation).filter(WordRelation.book_id == book_id)
    
    # 如果有关键词,添加搜索条件
    if keyword:
        query = query.filter(
            db.or_(
                Word.text.ilike(f'%{keyword}%'),
                Word.definition.ilike(f'%{keyword}%')
            )
        )
    
    # 按order字段排序
    query = query.order_by(WordRelation.order)
    
    total = query.count()
    words = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # 计算总页数
    pages = (total + per_page - 1) // per_page
    
    return jsonify({
        'code': 200,
        'data': {
            'items': [word.to_dict() for word in words],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages
        }
    })

@vocabulary_bp.route('/books/<int:book_id>/words/<int:word_id>', methods=['GET'])
@token_required
def get_word_detail(current_user, book_id, word_id):
    """获取单词详情"""
    book = db.session.get(VocabularyBook, book_id)
    if not book:
        return jsonify({'code': 404, 'message': '词汇书不存在'}), 404
    
    if book.user_id != current_user.id:
        return jsonify({'code': 403001, 'message': '无权访问此词汇书'}), 403
    
    word = db.session.query(Word).join(WordRelation).filter(
        WordRelation.book_id == book_id,
        Word.id == word_id
    ).first()
    
    if not word:
        return jsonify({'code': 404, 'message': '单词不存在'}), 404
    
    return jsonify({
        'code': 200,
        'data': word.to_dict()
    })

@vocabulary_bp.route('/books/<int:book_id>/words/<int:word_id>', methods=['PUT'])
@token_required
def update_word(current_user, book_id, word_id):
    """更新单词"""
    try:
        book = db.session.get(VocabularyBook, book_id)
        if not book:
            return jsonify({'code': 404, 'message': '词汇书不存在'}), 404
        
        if book.user_id != current_user.id:
            return jsonify({'code': 403001, 'message': '无权修改此词汇书'}), 403
        
        # 检查单词是否存在于词汇书中
        word_relation = db.session.query(WordRelation).filter_by(
            book_id=book_id,
            word_id=word_id
        ).first()
        
        if not word_relation:
            return jsonify({'code': 404, 'message': '单词不存在于此词汇书中'}), 404
            
        word = db.session.get(Word, word_id)
        if not word:
            return jsonify({'code': 404, 'message': '单词不存在'}), 404
            
        data = request.get_json()
        
        if 'phonetic' in data:
            word.phonetic = data['phonetic']
        if 'definition' in data:
            word.definition = data['definition']
        if 'example' in data:
            word.example = data['example']
            
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'data': word.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@vocabulary_bp.route('/books/<int:book_id>/words/<int:word_id>', methods=['DELETE'])
@token_required
def delete_word(current_user, book_id, word_id):
    """删除单词"""
    try:
        book = db.session.get(VocabularyBook, book_id)
        if not book:
            return jsonify({'code': 404, 'message': '词汇书不存在'}), 404
        
        if book.user_id != current_user.id:
            return jsonify({'code': 403001, 'message': '无权修改此词汇书'}), 403
        
        # 检查单词是否存在于词汇书中
        word_relation = db.session.query(WordRelation).filter_by(
            book_id=book_id,
            word_id=word_id
        ).first()
        
        if not word_relation:
            return jsonify({'code': 404, 'message': '单词不存在于此词汇书中'}), 404
            
        # 删除单词关系
        db.session.delete(word_relation)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '单词删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@vocabulary_bp.route('/learning/start', methods=['POST'])
@token_required
def start_learning_session(current_user):
    """开始学习会话"""
    data = request.get_json()
    word_id = data.get('word_id')
    
    if not word_id:
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
        
    record = db.session.query(LearningRecord).filter_by(
        user_id=current_user.id,
        word_id=word_id
    ).first()
    
    if not record:
        word = db.session.get(Word, word_id)
        if not word:
            return jsonify({'code': 404, 'message': '单词不存在'}), 404
        record = LearningRecord(user_id=current_user.id, word_id=word_id)
        db.session.add(record)
    
    record.start_study_session()
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '学习会话已开始'
    })

@vocabulary_bp.route('/learning/end', methods=['POST'])
@token_required
def end_learning_session(current_user):
    """结束学习会话"""
    data = request.get_json()
    word_id = data.get('word_id')
    confidence_level = data.get('confidence_level')  # 用户自评掌握程度（1-5）
    
    if not word_id:
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
        
    record = db.session.query(LearningRecord).filter_by(
        user_id=current_user.id,
        word_id=word_id
    ).first()
    
    if not record:
        return jsonify({'code': 404, 'message': '学习记录不存在'}), 404
    
    record.end_study_session()
    if confidence_level:
        record.update_confidence(confidence_level)
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '学习会话已结束',
        'data': {
            'study_duration': record.study_duration,
            'status': record.status
        }
    })

@vocabulary_bp.route('/words/<int:word_id>/status', methods=['PUT'])
@token_required
def update_word_status(current_user, word_id):
    """更新单词学习状态"""
    status = request.json.get('status')
    
    if status not in ['new', 'learning', 'mastered']:
        return jsonify({
            'code': 400,
            'message': '无效的状态值'
        }), 400
    
    record = db.session.query(LearningRecord).filter_by(
        user_id=current_user.id,
        word_id=word_id
    ).first()
    
    if not record:
        record = LearningRecord(
            user_id=current_user.id,
            word_id=word_id,
            review_count=0
        )
        db.session.add(record)
    
    record.status = status
    record.review_count = (record.review_count or 0) + 1
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '状态更新成功'
    })

@vocabulary_bp.route('/words/search', methods=['GET'])
@token_required
def search_words(current_user):
    """搜索单词
    支持的参数：
    - keyword: 关键词（单词或释义）
    - book_id: 单词书ID
    - level: 难度级别
    - status: 学习状态
    - page: 页码
    - per_page: 每页数量
    """
    keyword = request.args.get('keyword', '')
    book_id = request.args.get('book_id', type=int)
    level = request.args.get('level')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 构建基础查询
    query = db.session.query(Word)

    # 关键词搜索（支持单词和释义）
    if keyword:
        query = query.filter(
            db.or_(
                Word.text.ilike(f'%{keyword}%'),
                Word.definition.ilike(f'%{keyword}%')
            )
        )
    
    # 按单词书筛选
    if book_id:
        query = query.join(WordRelation).filter(WordRelation.book_id == book_id)
    
    # 按难度级别筛选
    if level:
        query = query.join(VocabularyBook).filter(VocabularyBook.level == level)
    
    # 按学习状态筛选，并添加默认的学习次数排序
    query = query.outerjoin(
        LearningRecord,
        db.and_(
            LearningRecord.word_id == Word.id,
            LearningRecord.user_id == current_user.id
        )
    )
    
    if status:
        query = query.filter(LearningRecord.status == status)
    
    # 默认按学习次数降序排序，未学习的排在后面
    query = query.order_by(
        db.case(
            (LearningRecord.review_count.is_(None), 0),
            else_=LearningRecord.review_count
        ).desc()
    )
    
    # 执行分页查询
    total = query.count()
    words = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # 获取单词的学习状态
    word_ids = [word.id for word in words]
    learning_records = {
        record.word_id: record.status
        for record in db.session.query(LearningRecord).filter(
            LearningRecord.word_id.in_(word_ids),
            LearningRecord.user_id == current_user.id
        )
    }
    
    return jsonify({
        'code': 200,
        'data': {
            'items': [word.to_dict() for word in words],
            'total': total,
            'page': page,
            'per_page': per_page
        }
    })

@vocabulary_bp.route('/goals', methods=['POST'])
@token_required
def create_learning_goal(current_user):
    """创建学习目标"""
    data = request.get_json()
    book_id = data.get('book_id')
    daily_words = data.get('daily_words')
    target_date = data.get('target_date')
    
    if not book_id or not (daily_words or target_date):
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
    
    user = User.query.get(current_user.id)
    book = VocabularyBook.query.get_or_404(book_id)
    
    # 检查是否已有相同书的学习目标
    existing_goal = LearningGoal.query.filter_by(
        user_id=current_user.id,
        book_id=book_id,
        status='active'
    ).first()
    
    if existing_goal:
        return jsonify({'code': 400, 'message': '已存在该单词书的学习目标'}), 400
    
    goal = LearningGoal(user=user, book=book, daily_words=daily_words)
    
    if target_date:
        goal.target_date = datetime.fromisoformat(target_date)
        goal.daily_words = goal.calculate_daily_words()
    else:
        goal.target_date = goal.calculate_target_date()
    
    db.session.add(goal)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '学习目标创建成功',
        'data': goal.to_dict()
    })

@vocabulary_bp.route('/goals/<int:goal_id>', methods=['PUT'])
@token_required
def update_learning_goal(current_user, goal_id):
    """更新学习目标"""
    goal = LearningGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    data = request.get_json()
    daily_words = data.get('daily_words')
    target_date = data.get('target_date')
    
    try:
        goal.adjust_plan(
            daily_words=daily_words,
            target_date=datetime.fromisoformat(target_date) if target_date else None
        )
        db.session.commit()
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    
    return jsonify({
        'code': 200,
        'message': '学习目标更新成功',
        'data': goal.to_dict()
    })

@vocabulary_bp.route('/goals', methods=['GET'])
@token_required
def get_learning_goals(current_user):
    """获取学习目标列表"""
    goals = LearningGoal.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'code': 200,
        'data': [{
            'id': goal.id,
            'book_id': goal.book_id,
            'book_name': goal.book.name,
            'daily_words': goal.daily_words,
            'target_date': goal.target_date.isoformat(),
            'status': goal.status,
            'progress': {
                'total_words': goal.book.total_words,
                'learned_words': LearningRecord.query.filter_by(
                    user_id=current_user.id,
                    status='mastered'
                ).join(Word).filter(Word.book_id == goal.book_id).count()
            }
        } for goal in goals]
    })

@vocabulary_bp.route('/review/plan', methods=['GET'])
@token_required
def get_review_plan(current_user):
    """获取今日复习计划"""
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    # 获取计划复习的单词
    plans = ReviewPlan.query.filter(
        ReviewPlan.user_id == current_user.id,
        ReviewPlan.scheduled_time >= today,
        ReviewPlan.scheduled_time < tomorrow,
        ReviewPlan.status == 'pending'
    ).order_by(ReviewPlan.scheduled_time).all()
    
    return jsonify({
        'code': 200,
        'data': [{
            'id': plan.id,
            'word': {
                'id': plan.word.id,
                'word': plan.word.text,
                'pronunciation': plan.word.phonetic,
                'definition': plan.word.definition,
                'example': plan.word.example
            },
            'scheduled_time': plan.scheduled_time.isoformat(),
            'status': plan.status
        } for plan in plans]
    })

@vocabulary_bp.route('/review/complete/<int:plan_id>', methods=['POST'])
@token_required
def complete_review(current_user, plan_id):
    """完成复习任务"""
    plan = ReviewPlan.query.filter_by(
        id=plan_id,
        user_id=current_user.id,
        status='pending'
    ).first_or_404()
    
    # 更新复习计划状态
    plan.status = 'completed'
    plan.actual_time = datetime.utcnow()
    
    # 更新学习记录
    record = LearningRecord.query.filter_by(
        user_id=current_user.id,
        word_id=plan.word_id
    ).first()
    
    if record:
        record.review_count = (record.review_count or 0) + 1
        record.last_review_time = datetime.utcnow()
        record.calculate_next_review_time()

        # 根据复习次数更新状态
        if record.review_count >= 5:
            record.status = 'mastered'
        elif record.review_count >= 2:
            record.status = 'learning'

    db.session.commit()
    
    # 生成下次复习计划
    if record and record.status != 'mastered':
        next_plan = ReviewPlan(
            user=plan.user,
            word=plan.word,
            scheduled_time=record.next_review_time
        )
        db.session.add(next_plan)
        db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '复习完成',
        'data': {
            'next_review_time': record.next_review_time.isoformat() if record else None
        }
    })

@vocabulary_bp.route('/words/<int:word_id>/relations', methods=['GET'])
@token_required
def get_word_relations(current_user, word_id):
    """获取单词关系"""
    word = Word.query.get_or_404(word_id)
    relations = WordRelation.query.filter_by(word_id=word_id).all()
    
    result = {}
    for relation in relations:
        relation_type = relation.relation_type
        if relation_type not in result:
            result[relation_type] = []
        
        related_word = relation.related_word
        result[relation_type].append({
            'id': related_word.id,
            'word': related_word.text,
            'definition': related_word.definition
        })
    
    return jsonify({
        'code': 200,
        'data': result
    })

@vocabulary_bp.route('/books/<int:book_id>/progress', methods=['GET'])
@token_required
def get_learning_progress(current_user, book_id):
    """获取词汇书学习进度"""
    book = VocabularyBook.query.get_or_404(book_id)
    
    if book.user_id != current_user.id:
        return jsonify({'code': 403001, 'message': '无权访问此词汇书'}), 403

    # 获取词汇书中的所有单词ID
    word_ids = db.session.query(WordRelation.word_id).filter_by(book_id=book_id).all()
    word_ids = [w[0] for w in word_ids]
    
    # 获取学习记录
    records = LearningRecord.query.filter(
        LearningRecord.user_id == current_user.id,
        LearningRecord.book_id == book_id,
        LearningRecord.word_id.in_(word_ids)
    ).all()

    # 统计不同状态的单词数量
    status_counts = {
        'new': len(word_ids) - len(records),
        'learning': len([r for r in records if r.status == 'learning']),
        'mastered': len([r for r in records if r.status == 'mastered'])
    }

    # 计算总学习时长（秒）
    total_study_time = sum(r.study_time for r in records)

    # 获取今日学习的单词数
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_learned_count = LearningRecord.query.filter(
        LearningRecord.user_id == current_user.id,
        LearningRecord.book_id == book_id,
        LearningRecord.created_at >= today_start
    ).count()

    # 计算连续学习天数
    consecutive_days = 0
    current_date = today_start
    while True:
        has_record = LearningRecord.query.filter(
            LearningRecord.user_id == current_user.id,
            LearningRecord.book_id == book_id,
            LearningRecord.created_at >= current_date,
            LearningRecord.created_at < current_date + timedelta(days=1)
        ).first() is not None

        if not has_record:
            break
        consecutive_days += 1
        current_date -= timedelta(days=1)

    return jsonify({
        'code': 200,
        'data': {
            'total_words': len(word_ids),
            'learning_words': status_counts['learning'],
            'mastered_words': status_counts['mastered'],
            'new_words': status_counts['new'],
            'total_study_time': total_study_time,
            'today_learned_count': today_learned_count,
            'consecutive_days': consecutive_days
        }
    })

@vocabulary_bp.route('/books/<int:book_id>/words', methods=['DELETE'])
@token_required
def batch_delete_words(current_user, book_id):
    """批量删除单词"""
    book = VocabularyBook.query.get_or_404(book_id)
    
    if book.user_id != current_user.id:
        return jsonify({'code': 403001, 'message': '无权访问此词汇书'}), 403
    
    data = request.get_json()
    if 'word_ids' not in data:
        return jsonify({'code': 400001, 'message': '缺少必填字段'}), 400
    
    # 删除单词关系
    WordRelation.query.filter(
        WordRelation.book_id == book_id,
        WordRelation.word_id.in_(data['word_ids'])
    ).delete(synchronize_session=False)
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '单词删除成功'
    })

@vocabulary_bp.route('/books/<int:book_id>/words/reorder', methods=['PUT'])
@token_required
def reorder_words(current_user, book_id):
    """重新排序单词"""
    book = db.session.get(VocabularyBook, book_id)
    if not book:
        return jsonify({'code': 404, 'message': '词汇书不存在'}), 404
        
    if book.user_id != current_user.id:
        return jsonify({'code': 403001, 'message': '无权修改此词汇书'}), 403
    
    data = request.get_json()
    if not data or 'word_ids' not in data:
        return jsonify({'code': 400001, 'message': '缺少必要参数'}), 400
    
    word_ids = data['word_ids']
    
    # 验证所有单词是否存在于词汇书中
    word_relations = db.session.query(WordRelation).filter(
        WordRelation.book_id == book_id,
        WordRelation.word_id.in_(word_ids)
    ).all()
    
    if len(word_relations) != len(word_ids):
        return jsonify({'code': 400001, 'message': '部分单词不存在于词汇书中'}), 400
    
    # 更新单词顺序
    word_relation_dict = {relation.word_id: relation for relation in word_relations}
    for i, word_id in enumerate(word_ids):
        word_relation_dict[word_id].order = i + 1
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '单词顺序更新成功'
    })

@vocabulary_bp.route('/books/<int:book_id>/statistics', methods=['GET'])
@token_required
def get_book_statistics(current_user, book_id):
    """获取词汇书统计信息"""
    book = VocabularyBook.query.get_or_404(book_id)
    
    if book.user_id != current_user.id:
        return jsonify({'code': 403001, 'message': '无权访问此词汇书'}), 403
    
    # 获取单词总数
    total_words = WordRelation.query.filter_by(book_id=book_id).count()
    
    return jsonify({
        'code': 200,
        'data': {
            'total_words': total_words
        }
    })

def get_words_query(book_id, keyword=None):
    """构建获取单词的查询"""
    query = Word.query.join(WordRelation).filter(
        WordRelation.book_id == book_id
    )
    
    if keyword:
        query = query.filter(Word.text.ilike(f'%{keyword}%'))
    
    return query.order_by(WordRelation.order) 