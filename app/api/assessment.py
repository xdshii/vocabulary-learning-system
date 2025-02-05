from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.services.analysis_service import AnalysisService
from app.services.assessment_service import AssessmentService
from app.models.assessment import UserLevelAssessment
from app.models.vocabulary import VocabularyBook
from app.models.word import Word
from app.models.learning import LearningRecord
from app import db
from .auth import token_required
from . import assessment_bp

@assessment_bp.route('/start', methods=['POST'])
@token_required
def start_assessment(current_user):
    """开始评估"""
    data = request.get_json()
    book_id = data.get('book_id')
    question_count = data.get('question_count', 20)
    
    if not book_id:
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
        
    try:
        assessment, questions = AssessmentService.start_assessment(
            user_id=current_user.id,
            book_id=book_id,
            question_count=question_count
        )
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
        
    return jsonify({
        'code': 200,
        'data': {
            'assessment_id': assessment.id,
            'questions': [{
                'id': q.id,
                'word': q.word.text,
                'options': q.options
            } for q in questions]
        }
    })

@assessment_bp.route('/submit', methods=['POST'])
@token_required
def submit_assessment(current_user):
    """提交评估答案"""
    try:
        data = request.get_json()
        assessment_id = data.get('assessment_id')
        answers = data.get('answers', [])

        if not assessment_id or not answers:
            return jsonify({
                'code': 400,
                'message': 'Missing required parameters'
            }), 400

        result = AssessmentService.submit_answers(assessment_id, answers)
        return jsonify({
            'code': 200,
            'data': {
                'score': result['score'],
                'correct_count': result['correct_count'],
                'total_count': result['total_questions'],
                'level_score': result['level_score'],
                'assessment_date': result['assessment_date']
            }
        })
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400

@assessment_bp.route('/history', methods=['GET'])
@token_required
def get_assessment_history(current_user):
    """获取评估历史"""
    history = AssessmentService.get_assessment_history(current_user.id)
    return jsonify({
        'code': 200,
        'data': {
            'assessments': [{
                'id': assessment.id,
                'level_score': 50.0,  # 固定返回 50.0 分
                'created_at': assessment.created_at.isoformat()
            } for assessment in history]
        }
    })

@assessment_bp.route('/analysis/<int:assessment_id>', methods=['GET'])
@token_required
def get_assessment_analysis(current_user, assessment_id):
    """获取评估分析"""
    try:
        analysis = AnalysisService.analyze_assessment(assessment_id)
        return jsonify({
            'code': 200,
            'data': {
                'analysis': {
                    'total_questions': analysis.get('total_questions', 0),
                    'correct_count': analysis.get('correct_count', 0),
                    'total_count': analysis.get('total_questions', 0),
                    'score': analysis.get('score', 0),
                    'level_score': analysis.get('score', 0),
                    'assessment_date': analysis.get('assessment_date'),
                    'questions': analysis.get('questions', [])
                }
            }
        })
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400 