import random
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models.assessment import UserLevelAssessment, AssessmentQuestion
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.word import Word
from app.models.learning import LearningRecord
from app.models.user import User
from typing import List, Tuple, Dict, Any

class AssessmentService:
    """评估服务"""
    
    @staticmethod
    def start_assessment(user_id: int, book_id: int, question_count: int = 20) -> Tuple[UserLevelAssessment, List[AssessmentQuestion]]:
        """开始评估
        
        Args:
            user_id: 用户ID
            book_id: 词书ID
            question_count: 题目数量，默认20题
            
        Returns:
            评估记录和题目列表
        """
        # 创建评估记录
        assessment = UserLevelAssessment(
            user_id=user_id,
            book_id=book_id
        )
        db.session.add(assessment)
        
        # 获取词书中的单词
        words = Word.query.join(WordRelation).filter(WordRelation.book_id == book_id).all()
        if not words:
            raise ValueError('No words found in the book')
            
        # 随机选择单词生成题目
        selected_words = random.sample(words, min(len(words), question_count))
        questions = []
        
        for word in selected_words:
            # 生成选项
            options = [word.definition]  # 正确答案
            other_words = [w for w in words if w != word]
            distractors = random.sample(other_words, min(len(other_words), 3))
            options.extend([d.definition for d in distractors])
            random.shuffle(options)
            
            # 创建题目
            question = AssessmentQuestion(
                assessment=assessment,
                word=word,
                question_type='choice',
                options=options,
                correct_answer=word.definition
            )
            questions.append(question)
            db.session.add(question)
            
        db.session.commit()
        return assessment, questions
    
    @staticmethod
    def submit_answer(assessment_id: int, question_id: int, answer: str) -> AssessmentQuestion:
        """提交答案
        
        Args:
            assessment_id: 评估ID
            question_id: 题目ID
            answer: 用户答案
            
        Returns:
            更新后的题目记录
        """
        question = AssessmentQuestion.query.get_or_404(question_id)
        if question.assessment_id != assessment_id:
            raise ValueError('Question does not belong to the assessment')
            
        question.user_answer = answer
        question.is_correct = (answer == question.correct_answer)
        question.answered_at = datetime.utcnow()
        
        db.session.commit()
        return question
    
    @staticmethod
    def complete_assessment(assessment_id: int) -> Dict[str, Any]:
        """完成评估"""
        assessment = UserLevelAssessment.query.get(assessment_id)
        if not assessment:
            raise ValueError('Assessment not found')
            
        if assessment.status == 'completed':
            raise ValueError('Assessment already completed')
            
        # 计算得分
        questions = assessment.questions
        total = len(questions)
        if total == 0:
            raise ValueError('No questions found in the assessment')
            
        correct = sum(1 for q in questions if q.is_correct)
        score = (correct / total * 100)
        
        # 更新评估记录
        assessment.status = 'completed'
        assessment.level_score = score
        assessment.total_questions = total
        assessment.correct_answers = correct
        assessment.completed_at = datetime.utcnow()
        
        # 更新学习记录
        for question in questions:
            if not question.is_correct:
                record = LearningRecord.query.filter_by(
                    user_id=assessment.user_id,
                    word_id=question.word_id,
                    book_id=assessment.book_id
                ).first()
                
                if not record:
                    record = LearningRecord(
                        user_id=assessment.user_id,
                        word_id=question.word_id,
                        book_id=assessment.book_id,
                        status='learning'
                    )
                    db.session.add(record)
                elif record.status == 'mastered':
                    record.status = 'learning'
                    record.next_review_time = datetime.utcnow()
        
        db.session.commit()
        
        # 返回结果
        return {
            'score': score,
            'level_score': score,
            'total_questions': total,
            'correct_count': correct,
            'assessment_date': assessment.completed_at.isoformat()
        }
    
    @staticmethod
    def get_assessment_history(user_id: int) -> List[Dict[str, Any]]:
        """获取评估历史"""
        assessments = UserLevelAssessment.query.filter_by(
            user_id=user_id,
            status='completed'
        ).order_by(UserLevelAssessment.created_at.desc()).all()
        
        return [{
            'id': assessment.id,
            'user_id': assessment.user_id,
            'book_id': assessment.book_id,
            'level_score': assessment.level_score,
            'total_questions': assessment.total_questions,
            'correct_answers': assessment.correct_answers,
            'assessment_date': assessment.completed_at.isoformat() if assessment.completed_at else None,
            'created_at': assessment.created_at.isoformat(),
            'completed_at': assessment.completed_at.isoformat() if assessment.completed_at else None,
            'status': assessment.status
        } for assessment in assessments]

    @staticmethod
    def _get_suggested_level(score):
        """根据分数返回建议级别"""
        if score < 2:
            return 'beginner'
        elif score < 3:
            return 'elementary'
        elif score < 4:
            return 'intermediate'
        else:
            return 'advanced'

    @staticmethod
    def _generate_distractors(word, all_words, count=3):
        """生成干扰选项
        
        Args:
            word: 目标单词
            all_words: 所有可选单词
            count: 干扰选项数量
            
        Returns:
            list: 干扰选项列表
        """
        # 排除当前单词的释义
        available_words = [w for w in all_words if w.id != word.id]
        
        # 优先选择相近难度的单词
        similar_difficulty_words = [
            w for w in available_words
            if abs(w.difficulty_level - word.difficulty_level) <= 0.5
        ]
        
        # 如果相近难度的单词不够，就从所有单词中选择
        if len(similar_difficulty_words) < count:
            distractors = random.sample(available_words, min(count, len(available_words)))
        else:
            distractors = random.sample(similar_difficulty_words, count)
        
        return [d.definitions[0]['meaning'] for d in distractors]

    @staticmethod
    def _generate_options(word):
        """生成选项
        
        Args:
            word: 目标单词
            
        Returns:
            list: 选项列表
        """
        # 生成干扰项
        other_words = [w for w in Word.query.filter_by(book_id=word.book_id).all() if w.id != word.id]
        distractors = random.sample(other_words, 3)
        options = [word.word] + [d.word for d in distractors]
        random.shuffle(options)
        
        return options

    @staticmethod
    def submit_answers(assessment_id: int, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量提交答案
        
        Args:
            assessment_id: 评估ID
            answers: 答案列表，每个答案包含 question_id 和 answer
            
        Returns:
            评估结果
        """
        # 提交每个答案
        for answer in answers:
            question_id = answer.get('question_id')
            user_answer = answer.get('answer')
            if not question_id or not user_answer:
                continue
            AssessmentService.submit_answer(assessment_id, question_id, user_answer)
            
        # 完成评估并返回结果
        return AssessmentService.complete_assessment(assessment_id) 