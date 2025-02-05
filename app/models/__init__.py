from app.extensions import db

# 导入基础模型
from .user import User
from .vocabulary import VocabularyBook, WordRelation
from .word import Word

# 导入学习相关模型
from .learning import LearningRecord, LearningGoal
from .learning_plan import LearningPlan
from .assessment import AssessmentQuestion

# 导入测试相关模型
from .test import TestQuestion

__all__ = [
    'db',
    'User',
    'VocabularyBook',
    'WordRelation',
    'Word',
    'LearningRecord',
    'LearningGoal',
    'LearningPlan',
    'AssessmentQuestion',
    'TestQuestion'
]
