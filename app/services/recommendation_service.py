from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.learning import LearningRecord
from app.models.assessment import UserLevelAssessment

class RecommendationService:
    """推荐服务"""
    
    @staticmethod
    def get_recommended_words(user_id: int, book_id: int = None, limit: int = 20) -> List[Dict[str, Any]]:
        """获取推荐单词
        
        Args:
            user_id: 用户ID
            book_id: 词书ID（可选）
            limit: 返回数量限制
            
        Returns:
            推荐单词列表
        """
        # 获取用户最新的评估记录
        assessment = UserLevelAssessment.query.filter_by(
            user_id=user_id,
            book_id=book_id if book_id else None
        ).order_by(UserLevelAssessment.assessment_date.desc()).first()
        
        if not assessment:
            raise ValueError('No assessment found for the user')
            
        # 获取已学习的单词ID列表
        learned_word_ids = db.session.query(LearningRecord.word_id).filter_by(
            user_id=user_id
        ).all()
        learned_word_ids = [w[0] for w in learned_word_ids]
        
        # 查询新单词
        query = Word.query
        if book_id:
            query = query.join(WordRelation).filter(WordRelation.book_id == book_id)
        if learned_word_ids:
            query = query.filter(~Word.id.in_(learned_word_ids))
            
        words = query.limit(limit).all()
        return [word.to_dict() for word in words]
    
    @staticmethod
    def get_review_words(user_id: int, book_id: int = None) -> List[Dict[str, Any]]:
        """获取需要复习的单词
        
        Args:
            user_id: 用户ID
            book_id: 词书ID（可选）
            
        Returns:
            需要复习的单词列表
        """
        # 查询需要复习的记录
        query = LearningRecord.query.filter_by(
            user_id=user_id,
            status='learning'
        ).filter(
            LearningRecord.next_review_time <= datetime.utcnow()
        )
        
        if book_id:
            query = query.join(Word).join(WordRelation).filter(WordRelation.book_id == book_id)
            
        records = query.all()
        return [
            {
                'id': record.word.id,
                'word': record.word.text,  # 修正这里，使用 text 而不是 word
                'definition': record.word.definition,
                'review_count': record.review_count,
                'next_review_time': record.next_review_time.isoformat() if record.next_review_time else None
            }
            for record in records
        ]
    
    @staticmethod
    def get_daily_schedule(user_id: int, book_id: int) -> Dict[str, Any]:
        """获取每日学习计划
        
        Args:
            user_id: 用户ID
            book_id: 词书ID
            
        Returns:
            学习计划详情
        """
        # 获取需要复习的单词数量
        review_count = LearningRecord.query.filter_by(
            user_id=user_id,
            status='learning'
        ).join(Word).join(WordRelation).filter(
            WordRelation.book_id == book_id,
            LearningRecord.next_review_time <= datetime.utcnow()
        ).count()
        
        # 获取今日已学习的单词数量
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        learned_today = LearningRecord.query.filter(
            LearningRecord.user_id == user_id,
            LearningRecord.created_at >= today_start
        ).join(Word).join(WordRelation).filter(
            WordRelation.book_id == book_id
        ).count()
        
        # 获取词书信息
        book = VocabularyBook.query.get_or_404(book_id)
        
        return {
            'book_name': book.name,
            'total_words': book.total_words,
            'review_words': review_count,
            'learned_today': learned_today,
            'remaining_today': max(20 - learned_today, 0)  # 假设每日目标20个单词
        } 