from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PracticeSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise_type = db.Column(db.String(20), nullable=False)  # interval, scale_degree, etc.
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # 秒
    total_questions = db.Column(db.Integer, default=20)
    correct_answers = db.Column(db.Integer, default=0)
    settings = db.Column(db.Text)  # JSON格式存储练习设置

class Question(db.Model):
    """通用题目表，支持多种练习类型"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('practice_session.id'), nullable=False)
    exercise_type = db.Column(db.String(20), nullable=False)
    question_data = db.Column(db.Text)  # JSON格式存储题目数据
    correct_answer = db.Column(db.String(100), nullable=False)
    sub_item = db.Column(db.String(100))  # 细分项，如音程练习中的"小二度"、"大二度"等
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_answer = db.Column(db.String(100))
    is_correct = db.Column(db.Boolean)
    response_time = db.Column(db.Float)  # 响应时间（秒）
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

