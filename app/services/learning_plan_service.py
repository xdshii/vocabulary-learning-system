from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import func
import math
from app import db
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.learning import LearningRecord, LearningGoal
from app.models.learning_plan import LearningPlan

class LearningPlanService:
    """学习计划服务"""
    
    @staticmethod
    def create_plan(user_id: int, book_id: int, daily_words: int = 20, target_date: str = None) -> Dict[str, Any]:
        """创建学习计划
        
        Args:
            user_id: 用户ID
            book_id: 词书ID
            daily_words: 每日单词数，默认20
            target_date: 目标完成日期（可选）
            
        Returns:
            创建的学习计划
        """
        # 检查是否已存在计划
        existing_plan = LearningPlan.query.filter_by(
            user_id=user_id,
            book_id=book_id
        ).first()
        
        if existing_plan:
            raise ValueError('Learning plan already exists')
            
        # 获取词书中的剩余单词数
        book = VocabularyBook.query.get_or_404(book_id)
        mastered_words = LearningRecord.query.filter_by(
            user_id=user_id,
            status='mastered'
        ).join(Word).join(WordRelation).filter(WordRelation.book_id == book_id).count()
        
        remaining_words = book.total_words - mastered_words
        start_date = datetime.utcnow().date()
        
        # 如果没有指定目标日期，根据每日单词数计算
        if not target_date:
            days_needed = math.ceil(remaining_words / daily_words)
            end_date = start_date + timedelta(days=days_needed)
        else:
            end_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            days_available = (end_date - start_date).days
            if days_available <= 0:
                raise ValueError('Target date must be in the future')
            daily_words = math.ceil(remaining_words / days_available)
            
        # 创建计划
        plan = LearningPlan(
            user_id=user_id,
            book_id=book_id,
            daily_words=daily_words,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(plan)
        db.session.commit()
        
        return {
            'id': plan.id,
            'user_id': plan.user_id,
            'book_id': plan.book_id,
            'daily_words': plan.daily_words,
            'start_date': plan.start_date.isoformat(),
            'end_date': plan.end_date.isoformat(),
            'created_at': plan.created_at.isoformat()
        }
    
    @staticmethod
    def update_plan(plan_id: int, daily_words: int = None, target_date: str = None) -> Dict[str, Any]:
        """更新学习计划
        
        Args:
            plan_id: 计划ID
            daily_words: 新的每日单词数
            target_date: 新的目标日期
            
        Returns:
            更新后的计划
        """
        plan = LearningPlan.query.get_or_404(plan_id)
        
        if daily_words:
            plan.daily_words = daily_words
            # 根据新的每日单词数重新计算目标日期
            book = VocabularyBook.query.get(plan.book_id)
            mastered_words = LearningRecord.query.filter_by(
                user_id=plan.user_id,
                status='mastered'
            ).join(Word).join(WordRelation).filter(WordRelation.book_id == plan.book_id).count()
            
            remaining_words = book.total_words - mastered_words
            days_needed = math.ceil(remaining_words / daily_words)
            plan.end_date = datetime.utcnow().date() + timedelta(days=days_needed)
            
        if target_date:
            end_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            # 根据新的目标日期重新计算每日单词数
            book = VocabularyBook.query.get(plan.book_id)
            mastered_words = LearningRecord.query.filter_by(
                user_id=plan.user_id,
                status='mastered'
            ).join(Word).join(WordRelation).filter(WordRelation.book_id == plan.book_id).count()
            
            remaining_words = book.total_words - mastered_words
            days_available = (end_date - datetime.utcnow().date()).days
            if days_available <= 0:
                raise ValueError('Target date must be in the future')
            plan.daily_words = math.ceil(remaining_words / days_available)
            plan.end_date = end_date
            
        db.session.commit()
        
        return {
            'id': plan.id,
            'user_id': plan.user_id,
            'book_id': plan.book_id,
            'daily_words': plan.daily_words,
            'start_date': plan.start_date.isoformat(),
            'end_date': plan.end_date.isoformat(),
            'updated_at': plan.updated_at.isoformat()
        }
    
    @staticmethod
    def get_plan(plan_id: int) -> Dict[str, Any]:
        """获取学习计划
        
        Args:
            plan_id: 计划ID
            
        Returns:
            计划详情
        """
        plan = LearningPlan.query.get_or_404(plan_id)
        
        # 获取学习进度
        book = VocabularyBook.query.get(plan.book_id)
        mastered_words = LearningRecord.query.filter_by(
            user_id=plan.user_id,
            status='mastered'
        ).join(Word).join(WordRelation).filter(WordRelation.book_id == plan.book_id).count()
        
        remaining_words = book.total_words - mastered_words
        days_remaining = (plan.end_date - datetime.utcnow().date()).days
        
        return {
            'id': plan.id,
            'user_id': plan.user_id,
            'book_id': plan.book_id,
            'book_name': book.name,
            'daily_words': plan.daily_words,
            'start_date': plan.start_date.isoformat(),
            'end_date': plan.end_date.isoformat(),
            'total_words': book.total_words,
            'mastered_words': mastered_words,
            'remaining_words': remaining_words,
            'days_remaining': days_remaining,
            'created_at': plan.created_at.isoformat(),
            'updated_at': plan.updated_at.isoformat()
        } 