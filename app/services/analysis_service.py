from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models.vocabulary import VocabularyBook
from app.models.word import Word
from app.models.learning import LearningRecord
from app.models.assessment import UserLevelAssessment
from app.models.test import Test, TestRecord
from app.models.vocabulary import WordRelation

class AnalysisService:
    """分析服务"""
    
    @staticmethod
    def analyze_assessment(assessment_id):
        """分析评估结果"""
        assessment = UserLevelAssessment.query.get(assessment_id)
        if not assessment:
            raise ValueError('Assessment not found')
            
        total_questions = len(assessment.questions)
        correct_answers = sum(1 for q in assessment.questions if q.is_correct)
        accuracy_rate = correct_answers / total_questions if total_questions > 0 else 0
        score = accuracy_rate * 100
        
        # 分析难度分布
        difficulty_stats = {
            'easy': 0,
            'medium': 0,
            'hard': 0
        }
        
        weak_words = []
        questions_data = []
        for question in assessment.questions:
            questions_data.append({
                'id': question.id,
                'word': question.word.text,
                'correct_answer': question.correct_answer,
                'user_answer': question.user_answer,
                'is_correct': question.is_correct
            })
            if not question.is_correct:
                weak_words.append(question.word)
                
        # 生成建议
        suggestions = []
        if accuracy_rate < 0.6:
            suggestions.append("建议从基础词汇开始复习")
        elif accuracy_rate < 0.8:
            suggestions.append("继续保持,注意查漏补缺")
        else:
            suggestions.append("可以尝试更高难度的词汇")
            
        return {
            'score': score,
            'correct_count': correct_answers,
            'total_count': total_questions,
            'accuracy_rate': accuracy_rate,
            'difficulty_stats': difficulty_stats,
            'weak_words': [word.to_dict() for word in weak_words],
            'suggestions': suggestions,
            'questions': questions_data
        }
        
    @staticmethod
    def analyze_learning_progress(assessment_id):
        """分析学习进度"""
        assessment = UserLevelAssessment.query.get(assessment_id)
        if not assessment:
            raise ValueError('Assessment not found')
            
        total_questions = len(assessment.questions)
        correct_answers = sum(1 for q in assessment.questions if q.is_correct)
        accuracy_rate = correct_answers / total_questions if total_questions > 0 else 0
        
        weak_words = []
        for question in assessment.questions:
            if not question.is_correct:
                weak_words.append(question.word)
        
        return {
            'total_words': total_questions,
            'learned_words': correct_answers,
            'learning_rate': accuracy_rate,
            'accuracy_rate': accuracy_rate,
            'weak_words': [word.to_dict() for word in weak_words]
        }
        
    @staticmethod
    def analyze_test_history(assessment_id):
        """分析测试历史"""
        assessment = UserLevelAssessment.query.get(assessment_id)
        if not assessment:
            raise ValueError('Assessment not found')
            
        total_questions = len(assessment.questions)
        correct_answers = sum(1 for q in assessment.questions if q.is_correct)
        accuracy_rate = correct_answers / total_questions if total_questions > 0 else 0
        
        weak_words = []
        for question in assessment.questions:
            if not question.is_correct:
                weak_words.append(question.word)
        
        return {
            'test_count': 1,
            'average_score': assessment.score,
            'accuracy_trend': [accuracy_rate],
            'accuracy_rate': accuracy_rate,
            'weak_words': [word.to_dict() for word in weak_words]
        } 