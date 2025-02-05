from flask import Blueprint

# 创建蓝图
auth_bp = Blueprint('auth', __name__)
vocabulary_bp = Blueprint('vocabulary', __name__)
learning_bp = Blueprint('learning', __name__)
assessment_bp = Blueprint('assessment', __name__)
test_bp = Blueprint('test', __name__)

# 导入路由
from . import auth, vocabulary, learning, assessment, test
