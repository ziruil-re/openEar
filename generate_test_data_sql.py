#!/usr/bin/env python3
"""生成虚拟测试数据用于统计页面展示 - 直接操作数据库"""

import sqlite3
import random
from datetime import datetime, timedelta
import json

# 数据库路径
DB_PATH = '/Users/liuzirui/Desktop/openEar/opear.db'

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
    """生成测试数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"开始为用户ID {user_id} 生成测试数据...")
    
    # 计算开始日期
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # 为每种练习类型设置目标题目数（50-100题）
    exercise_targets = {}
    for ex_type in EXERCISE_TYPES:
        exercise_targets[ex_type] = {
            'target': random.randint(50, 100),
            'current': 0
        }
    
    total_sessions = 0
    total_questions = 0
    
    # 按天生成数据
    current_date = start_date
    while current_date <= end_date:
        # 每天随机生成1-3个会话
        num_sessions = random.randint(sessions_per_day_range[0], sessions_per_day_range[1])
        
        for _ in range(num_sessions):
            # 优先选择还未达到目标的练习类型
            available_types = [et for et in EXERCISE_TYPES 
                             if exercise_targets[et]['current'] < exercise_targets[et]['target']]
            if not available_types:
                # 如果都达到了，随机选择
                available_types = EXERCISE_TYPES
            
            # 随机选择练习类型
            exercise_type = random.choice(available_types)
            
            # 随机生成会话时间（当天的一个随机时间）
            session_time = current_date.replace(
                hour=random.randint(8, 22),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            # 生成题目数量（每个会话5-15题，但不超过剩余目标）
            remaining = exercise_targets[exercise_type]['target'] - exercise_targets[exercise_type]['current']
            max_questions = min(15, remaining) if remaining > 0 else random.randint(5, 15)
            num_questions = random.randint(5, max(5, max_questions))
            correct_answers = random.randint(int(num_questions * 0.3), int(num_questions * 0.9))
            duration = random.randint(300, 1800)  # 5-30分钟
            end_time = session_time + timedelta(seconds=duration)
            
            # 创建练习会话
            cursor.execute("""
                INSERT INTO practice_session 
                (user_id, exercise_type, start_time, end_time, duration, total_questions, correct_answers, settings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                exercise_type,
                session_time.isoformat(),
                end_time.isoformat(),
                duration,
                num_questions,
                correct_answers,
                json.dumps({'test': True})
            ))
            session_id = cursor.lastrowid
            
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
                question_time = session_time + timedelta(seconds=q_idx * 10)
                cursor.execute("""
                    INSERT INTO question 
                    (session_id, exercise_type, question_data, correct_answer, sub_item, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    exercise_type,
                    json.dumps({
                        'exercise_type': exercise_type,
                        'sub_item': sub_item
                    }),
                    correct_answer,
                    sub_item,
                    question_time.isoformat()
                ))
                question_id = cursor.lastrowid
                
                # 创建用户答案（70%正确率）
                is_correct = random.random() < 0.7
                if exercise_type == 'interval':
                    options = INTERVALS
                elif exercise_type == 'scale_degree':
                    options = SCALE_DEGREES
                else:
                    options = CHORD_TYPES
                
                user_answer = correct_answer if is_correct else random.choice([o for o in options if o != correct_answer])
                response_time = random.uniform(2.0, 15.0)
                answer_time = question_time + timedelta(seconds=5)
                
                cursor.execute("""
                    INSERT INTO user_answer 
                    (user_id, question_id, user_answer, is_correct, response_time, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    question_id,
                    user_answer,
                    1 if is_correct else 0,
                    response_time,
                    answer_time.isoformat()
                ))
                
                total_questions += 1
            
            # 更新该类型的题目计数
            exercise_targets[exercise_type]['current'] += num_questions
            total_sessions += 1
        
        # 移动到下一天
        current_date += timedelta(days=1)
    
    # 提交所有数据
    conn.commit()
    conn.close()
    
    print(f"✅ 成功生成数据:")
    print(f"   - 会话数: {total_sessions}")
    print(f"   - 题目数: {total_questions}")
    print(f"   - 时间范围: {start_date.date()} 至 {end_date.date()}")

if __name__ == '__main__':
    # 查找用户
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM user WHERE username='re'")
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        print("❌ 未找到用户 're'")
        exit(1)
    
    user_id, username, email = user
    print(f"找到用户: {username} (ID: {user_id})")
    
    # 询问是否清除旧数据
    response = input("是否清除该用户的所有旧数据？(y/N): ")
    if response.lower() == 'y':
        print("清除旧数据...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 删除用户的所有答案
        cursor.execute("DELETE FROM user_answer WHERE user_id = ?", (user_id,))
        # 删除所有题目（通过会话ID）
        cursor.execute("""
            DELETE FROM question 
            WHERE session_id IN (SELECT id FROM practice_session WHERE user_id = ?)
        """, (user_id,))
        # 删除所有会话
        cursor.execute("DELETE FROM practice_session WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        print("✅ 旧数据已清除")
    
    # 生成新数据（2周，每种练习类型50-100题）
    generate_test_data(user_id, days_back=14, sessions_per_day_range=(1, 3))
    print("✅ 数据生成完成！")

