from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models.test import Test, TestQuestion
from app.models.word import Word
from app.models.vocabulary import VocabularyBook, WordRelation
from app.models.learning import LearningRecord

class TestService:
    @staticmethod
    def create_test(user_id: int, book_id: int, test_type: str) -> dict:
        """创建测试
        
        Args:
            user_id: 用户ID
            book_id: 词书ID
            test_type: 测试类型（multiple_choice, true_false, fill_blank）
            
        Returns:
            dict: 包含测试ID和题目列表的字典
        """
        # 验证测试类型
        valid_types = ['multiple_choice', 'true_false', 'fill_blank']
        if test_type not in valid_types:
            raise ValueError(f'Invalid test type. Must be one of {valid_types}')
        
        # 获取词书信息
        book = VocabularyBook.query.get_or_404(book_id)
        
        # 创建测试记录
        test = Test(
            user_id=user_id,
            book_id=book_id,
            test_type=test_type,
            name=f'{book.name} - {test_type} Test'
        )
        db.session.add(test)
        db.session.flush()  # 确保 test.id 被生成
        
        # 获取词书中的单词
        words = Word.query.join(WordRelation).filter(WordRelation.book_id == book_id).all()
        if not words:
            raise ValueError('No words found in the book')
        
        # 根据测试类型生成题目
        questions = []
        for word in words:
            question = TestQuestion(
                test_id=test.id,
                word_id=word.id,
                question_type=test_type,
                question=f'What is the meaning of "{word.text}"?',
                correct_answer=word.definition
            )
            
            if test_type == 'multiple_choice':
                # 获取其他单词作为选项
                other_words = Word.query.join(WordRelation).filter(
                    Word.id != word.id,
                    WordRelation.book_id == book_id
                ).order_by(func.random()).limit(3).all()
                
                options = [word.definition] + [w.definition for w in other_words]
                question.options = options
            
            questions.append(question)
            db.session.add(question)
        
        db.session.commit()
        
        return {
            'id': test.id,
            'questions': [q.to_dict() for q in questions]
        }
    
    @staticmethod
    def submit_test(test_id, answers):
        """提交测试答案"""
        test = Test.query.get(test_id)
        if not test:
            raise ValueError('Test not found')
            
        if test.status == 'completed':
            raise ValueError('Test already completed')
            
        if test.status == 'pending':
            test.status = 'in_progress'
            test.start_time = datetime.utcnow()
            
        # 更新答案
        total_score = 0
        total_questions = len(test.questions)
        correct_count = 0
        
        for answer in answers:
            question = TestQuestion.query.get(answer['question_id'])
            if not question or question.test_id != test_id:
                continue
                
            question.user_answer = answer['answer']
            question.is_correct = (question.user_answer == question.correct_answer)
            if question.is_correct:
                total_score += question.score
                correct_count += 1
                
        # 计算百分比得分
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
                
        # 更新测试状态
        test.score = score
        test.status = 'completed'
        test.end_time = datetime.utcnow()
        test.completed_at = datetime.utcnow()
        test.correct_answers = correct_count
        test.total_questions = total_questions
        
        # 更新学习记录
        for question in test.questions:
            if not question.is_correct:
                record = LearningRecord.query.filter_by(
                    user_id=test.user_id,
                    word_id=question.word_id,
                    book_id=test.book_id
                ).first()
                
                if not record:
                    record = LearningRecord(
                        user_id=test.user_id,
                        word_id=question.word_id,
                        book_id=test.book_id,
                        status='learning'
                    )
                    db.session.add(record)
                elif record.status == 'mastered':
                    record.status = 'learning'
                    record.next_review_time = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'test_id': test.id,
            'score': score,
            'status': test.status,
            'total_questions': total_questions,
            'correct_count': correct_count,
            'correct_answers': correct_count,
            'end_time': test.end_time.isoformat()
        }
    
    @staticmethod
    def get_test_results(user_id):
        """获取用户的测试结果"""
        tests = Test.query.filter_by(user_id=user_id).all()
        results = []
        for test in tests:
            result = {
                'id': test.id,
                'user_id': test.user_id,
                'book_id': test.book_id,
                'test_type': test.test_type,
                'score': test.score,
                'total_questions': test.total_questions,
                'correct_answers': test.correct_answers,
                'status': test.status,
                'created_at': test.created_at.isoformat(),
                'completed_at': test.completed_at.isoformat() if test.completed_at else None
            }
            results.append(result)
        return results
    
    @staticmethod
    def get_test_details(test_id: int) -> dict:
        """获取测试详情
        
        Args:
            test_id: 测试ID
            
        Returns:
            dict: 测试详情
        """
        test = Test.query.get_or_404(test_id)
        
        return {
            'test': test.to_dict(),
            'questions': [q.to_dict() for q in test.questions]
        }
    
    @staticmethod
    def get_learning_progress(user_id: int, book_id: int) -> dict:
        """获取学习进度
        
        Args:
            user_id: 用户ID
            book_id: 词书ID
            
        Returns:
            dict: 学习进度统计
        """
        book = VocabularyBook.query.get_or_404(book_id)
        total_words = book.total_words
        
        # 获取已掌握的单词数
        mastered_words = LearningRecord.query.filter_by(
            user_id=user_id,
            status='mastered'
        ).join(Word).join(WordRelation).filter(WordRelation.book_id == book_id).count()
        
        # 获取正在学习的单词数
        learning_words = LearningRecord.query.filter_by(
            user_id=user_id,
            status='learning'
        ).join(Word).join(WordRelation).filter(WordRelation.book_id == book_id).count()
        
        # 获取最近一次测试成绩
        latest_test = Test.query.filter_by(
            user_id=user_id,
            book_id=book_id
        ).order_by(Test.created_at.desc()).first()
        
        return {
            'total_words': total_words,
            'mastered_words': mastered_words,
            'learning_words': learning_words,
            'new_words': total_words - mastered_words - learning_words,
            'latest_test_score': latest_test.score if latest_test else None,
            'progress': (mastered_words / total_words * 100) if total_words > 0 else 0
        } 