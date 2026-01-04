#!/usr/bin/env python3
"""生成虚拟测试数据用于统计页面展示"""

import os
import sys
import random
from datetime import datetime, timedelta
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, PracticeSession, Question, UserAnswer

# 练习类型
EXERCISE_TYPES = ['interval', 'scale_degree', 'chord_quality']

# 音程类型（用于interval练习）
INTERVALS = ['minor_second', 'major_second', 'minor_third', 'major_third', 
             'perfect_fourth', 'tritone', 'perfect_fifth', 'minor_sixth', 
             'major_sixth', 'minor_seventh', 'major_seventh', 'octave']

# 音级（用于scale_degree练习）
SCALE_DEGREES = ['1', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']

# 和弦类型（用于chord_quality练习）
CHORD_TYPES = ['major', 'minor', 'diminished', 'augmented', 'sus4', 'sus2',
               'major7th', 'minor7th', 'dominant7th', 'diminished7th']

def generate_test_data(user_id, days_back=90, sessions_per_day_range=(1, 5)):
    """生成测试数据
    
    Args:
        user_id: 用户ID
        days_back: 生成多少天前的数据
        sessions_per_day_range: 每天生成多少个会话（范围）
    """
    print(f"开始为用户ID {user_id} 生成测试数据...")
    
    # 计算开始日期
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    total_sessions = 0
    total_questions = 0
    
    # 按天生成数据
    current_date = start_date
    while current_date <= end_date:
        # 每天随机生成1-5个会话
        num_sessions = random.randint(sessions_per_day_range[0], sessions_per_day_range[1])
        
        for _ in range(num_sessions):
            # 随机选择练习类型
            exercise_type = random.choice(EXERCISE_TYPES)
            
            # 随机生成会话时间（当天的一个随机时间）
            session_time = current_date.replace(
                hour=random.randint(8, 22),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            # 生成题目数量（10-30题）
            num_questions = random.randint(10, 30)
            
            # 创建练习会话
            session = PracticeSession(
                user_id=user_id,
                exercise_type=exercise_type,
                start_time=session_time,
                end_time=session_time + timedelta(minutes=random.randint(5, 30)),
                duration=random.randint(300, 1800),  # 5-30分钟
                total_questions=num_questions,
                correct_answers=random.randint(int(num_questions * 0.3), int(num_questions * 0.9)),
                settings=json.dumps({'test': True})
            )
            db.session.add(session)
            db.session.flush()  # 获取session.id
            
            # 为每个会话生成题目和答案
            for q_idx in range(num_questions):
                # 根据练习类型生成不同的细分项
                if exercise_type == 'interval':
                    sub_item = random.choice(INTERVALS)
                    correct_answer = sub_item
                elif exercise_type == 'scale_degree':
                    sub_item = random.choice(SCALE_DEGREES)
                    correct_answer = sub_item
                elif exercise_type == 'chord_quality':
                    sub_item = random.choice(CHORD_TYPES)
                    correct_answer = sub_item
                else:
                    sub_item = ''
                    correct_answer = 'test'
                
                # 创建题目
                question = Question(
                    session_id=session.id,
                    exercise_type=exercise_type,
                    question_data=json.dumps({
                        'exercise_type': exercise_type,
                        'sub_item': sub_item
                    }),
                    correct_answer=correct_answer,
                    sub_item=sub_item,
                    created_at=session_time + timedelta(seconds=q_idx * 10)
                )
                db.session.add(question)
                db.session.flush()  # 获取question.id
                
                # 创建用户答案（70%正确率）
                is_correct = random.random() < 0.7
                user_answer = correct_answer if is_correct else random.choice(
                    INTERVALS if exercise_type == 'interval' else 
                    SCALE_DEGREES if exercise_type == 'scale_degree' else 
                    CHORD_TYPES
                )
                
                answer = UserAnswer(
                    user_id=user_id,
                    question_id=question.id,
                    user_answer=user_answer,
                    is_correct=is_correct,
                    response_time=random.uniform(2.0, 15.0),  # 2-15秒
                    timestamp=session_time + timedelta(seconds=q_idx * 10 + 5)
                )
                db.session.add(answer)
                
                total_questions += 1
            
            total_sessions += 1
        
        # 移动到下一天
        current_date += timedelta(days=1)
    
    # 提交所有数据
    try:
        db.session.commit()
        print(f"✅ 成功生成数据:")
        print(f"   - 会话数: {total_sessions}")
        print(f"   - 题目数: {total_questions}")
        print(f"   - 时间范围: {start_date.date()} 至 {end_date.date()}")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 生成数据失败: {e}")
        raise

if __name__ == '__main__':
    with app.app_context():
        # 查找用户
        user = User.query.filter_by(username='re').first()
        if not user:
            print("❌ 未找到用户 're'")
            sys.exit(1)
        
        print(f"找到用户: {user.username} (ID: {user.id})")
        
        # 询问是否清除旧数据
        response = input("是否清除该用户的所有旧数据？(y/N): ")
        if response.lower() == 'y':
            print("清除旧数据...")
            # 删除用户的所有答案
            UserAnswer.query.filter_by(user_id=user.id).delete()
            # 删除所有题目
            Question.query.filter(
                Question.session_id.in_(
                    db.session.query(PracticeSession.id).filter_by(user_id=user.id)
                )
            ).delete()
            # 删除所有会话
            PracticeSession.query.filter_by(user_id=user.id).delete()
            db.session.commit()
            print("✅ 旧数据已清除")
        
        # 生成新数据
        generate_test_data(user.id, days_back=120, sessions_per_day_range=(1, 4))
        print("✅ 数据生成完成！")

