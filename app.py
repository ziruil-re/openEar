from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, PracticeSession
from datetime import datetime, timedelta, date
import random
import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'opear_secret_key_2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'opear.db')
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 练习类型定义
EXERCISE_TYPES = {
    'interval': {
        'name': '音程辨认',
        'name_en': 'Intervals',
        'icon': '🎵',
        'description': '识别两个音符之间的音程关系'
    },
    'scale_degree': {
        'name': '音阶内音辨认',
        'name_en': 'Scale Degrees',
        'icon': '🎹',
        'description': '识别音阶中的特定音级'
    },
    'chord_quality': {
        'name': '和弦性质',
        'name_en': 'Chord Quality',
        'icon': '🎼',
        'description': '识别和弦的类型和性质'
    },
    'chord_progression': {
        'name': '和弦进行',
        'name_en': 'Chord Progressions',
        'icon': '🎸',
        'description': '识别和弦进行的模式'
    },
    'melody': {
        'name': '旋律片段',
        'name_en': 'Melody',
        'icon': '🎶',
        'description': '识别音阶中的旋律片段'
    }
}

# 音程定义
INTERVALS = {
    0: {'name': 'unison', 'cn': '同度', 'semitones': 0},
    1: {'name': 'minor_second', 'cn': '小二度', 'semitones': 1},
    2: {'name': 'major_second', 'cn': '大二度', 'semitones': 2},
    3: {'name': 'minor_third', 'cn': '小三度', 'semitones': 3},
    4: {'name': 'major_third', 'cn': '大三度', 'semitones': 4},
    5: {'name': 'perfect_fourth', 'cn': '纯四度', 'semitones': 5},
    6: {'name': 'tritone', 'cn': '增四度', 'semitones': 6},
    7: {'name': 'perfect_fifth', 'cn': '纯五度', 'semitones': 7},
    8: {'name': 'minor_sixth', 'cn': '小六度', 'semitones': 8},
    9: {'name': 'major_sixth', 'cn': '大六度', 'semitones': 9},
    10: {'name': 'minor_seventh', 'cn': '小七度', 'semitones': 10},
    11: {'name': 'major_seventh', 'cn': '大七度', 'semitones': 11},
    12: {'name': 'octave', 'cn': '八度', 'semitones': 12}
}

# 音符名称
NOTE_NAMES = []
octaves = [2, 3, 4, 5, 6]
note_letters = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

for octave in octaves:
    for note in note_letters:
        NOTE_NAMES.append(f"{note}{octave}")

def generate_interval_audio(note1, note2, duration=1.0):
    """生成音程音频文件"""
    try:
        import numpy as np
        from scipy.io import wavfile
        
        # 音频文件路径 - 检查多个可能的位置
        note1_path = os.path.join(basedir, 'static', 'audio', 'notes', f"{note1}.wav")
        note2_path = os.path.join(basedir, 'static', 'audio', 'notes', f"{note2}.wav")
        
        # 如果不存在，尝试从Hearzy目录复制
        if not os.path.exists(note1_path):
            hearzy_path = os.path.join(basedir, '..', 'Hearzy', 'static', 'audio', 'notes', f"{note1}.wav")
            if os.path.exists(hearzy_path):
                import shutil
                os.makedirs(os.path.dirname(note1_path), exist_ok=True)
                shutil.copy(hearzy_path, note1_path)
        
        if not os.path.exists(note2_path):
            hearzy_path = os.path.join(basedir, '..', 'Hearzy', 'static', 'audio', 'notes', f"{note2}.wav")
            if os.path.exists(hearzy_path):
                import shutil
                os.makedirs(os.path.dirname(note2_path), exist_ok=True)
                shutil.copy(hearzy_path, note2_path)
        
        # 使用安全的文件名（替换 # 为 sharp）
        safe_note1 = note1.replace('#', 'sharp')
        safe_note2 = note2.replace('#', 'sharp')
        interval_dir = os.path.join(basedir, 'static', 'audio', 'interval')
        os.makedirs(interval_dir, exist_ok=True)
        output_path = os.path.join(interval_dir, f"{safe_note1}_{safe_note2}_1sec.wav")
        
        # 检查输入文件是否存在
        if not os.path.exists(note1_path):
            return False
        
        if not os.path.exists(note2_path):
            return False
        
        # 读取两个音符的音频
        sr1, audio1 = wavfile.read(note1_path)
        sr2, audio2 = wavfile.read(note2_path)
        
        # 确保采样率相同
        if sr1 != sr2:
            print(f"采样率不同: {sr1} vs {sr2}")
            return False
        
        # 处理可能的多声道音频（如果是立体声，取左声道）
        if len(audio1.shape) > 1:
            audio1 = audio1[:, 0]
        if len(audio2.shape) > 1:
            audio2 = audio2[:, 0]
        
        # 取每个音符的前1秒
        samples_per_second = sr1
        audio1_1sec = audio1[:min(samples_per_second, len(audio1))]
        audio2_1sec = audio2[:min(samples_per_second, len(audio2))]
        
        # 如果音频长度不足1秒，用零填充
        if len(audio1_1sec) < samples_per_second:
            padding1 = np.zeros(samples_per_second - len(audio1_1sec), dtype=audio1_1sec.dtype)
            audio1_1sec = np.concatenate([audio1_1sec, padding1])
        if len(audio2_1sec) < samples_per_second:
            padding2 = np.zeros(samples_per_second - len(audio2_1sec), dtype=audio2_1sec.dtype)
            audio2_1sec = np.concatenate([audio2_1sec, padding2])
        
        # 拼接两个音符（先播放note1，再播放note2）
        combined_audio = np.concatenate([audio1_1sec, audio2_1sec])
        
        # 保存音频文件
        wavfile.write(output_path, sr1, combined_audio)
        
        return True
        
    except Exception as e:
        print(f"生成音频失败: {e}")
        return False

# 加载Tips和歌曲数据
def load_tips_data():
    """从数据文件加载Tips"""
    tips_file = os.path.join(basedir, '..', 'data', 'tips.json')
    if os.path.exists(tips_file):
        with open(tips_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_songs_data():
    """从数据文件加载歌曲数据"""
    songs_file = os.path.join(basedir, '..', 'data', 'songs.json')
    if os.path.exists(songs_file):
        with open(songs_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 初始化数据库
init_done = False
@app.before_request
def create_tables():
    global init_done
    if not init_done:
        db.create_all()
        init_done = True

# 路由
@app.route('/')
def index():
    """首页 - 练习选择"""
    return render_template('index.html', 
                         exercise_types=EXERCISE_TYPES,
                         current_user=current_user)

@app.route('/practice/<exercise_type>')
def practice(exercise_type):
    """练习页面"""
    if exercise_type not in EXERCISE_TYPES:
        flash('无效的练习类型')
        return redirect(url_for('index'))
    
    tips_data = load_tips_data()
    songs_data = load_songs_data()
    
    return render_template('practice.html',
                         exercise_type=exercise_type,
                         exercise_info=EXERCISE_TYPES[exercise_type],
                         intervals=INTERVALS,
                         tips=tips_data.get(exercise_type, {}),
                         songs=songs_data.get(exercise_type, {}),
                         current_user=current_user)

@app.route('/api/generate_question/<exercise_type>')
def generate_question(exercise_type):
    """生成题目"""
    if exercise_type != 'interval':
        return jsonify({'status': 'error', 'message': '该练习类型暂未实现'})
    
    # 获取前端传来的参数
    intervals = request.args.get('intervals', '')
    directions = request.args.get('directions', '')
    
    if intervals:
        allowed_intervals = intervals.split(',')
    else:
        allowed_intervals = [v['name'] for v in INTERVALS.values() if v['name'] != 'unison']
    
    if directions:
        allowed_directions = directions.split(',')
    else:
        allowed_directions = ['up', 'down']
    
    # 预先生成所有合法组合
    valid_pairs = []
    for note1_idx in range(len(NOTE_NAMES)):
        for direction in allowed_directions:
            for semitones, interval in INTERVALS.items():
                if interval['name'] not in allowed_intervals:
                    continue
                if direction == 'up':
                    note2_idx = note1_idx + semitones
                else:
                    note2_idx = note1_idx - semitones
                if 0 <= note2_idx < len(NOTE_NAMES) and semitones != 0:
                    valid_pairs.append((note1_idx, note2_idx, semitones, interval, direction))
    
    if not valid_pairs:
        return jsonify({'status': 'error', 'msg': '没有符合条件的题目，请调整选择'})
    
    # 随机抽取一个组合
    note1_idx, note2_idx, semitones, interval_info, direction = random.choice(valid_pairs)
    note1 = NOTE_NAMES[note1_idx]
    note2 = NOTE_NAMES[note2_idx]
    
    # 计算音程
    semitones = abs(note2_idx - note1_idx)
    interval_info = INTERVALS.get(semitones, INTERVALS[0])
    
    # 检查对应的音程音频文件是否存在
    safe_note1 = note1.replace('#', 'sharp')
    safe_note2 = note2.replace('#', 'sharp')
    audio_file = f"interval/{safe_note1}_{safe_note2}_1sec.wav"
    audio_path = os.path.join(basedir, 'static', 'audio', audio_file)
    
    # 如果不存在，就生成这个音程的音频文件
    if not os.path.exists(audio_path):
        success = generate_interval_audio(note1, note2)
        if not success:
            # 如果生成失败，返回错误而不是使用单个音符
            return jsonify({
                'status': 'error',
                'msg': f'无法生成音程音频: {note1} - {note2}，请检查音频文件是否存在'
            })
    
    # 准备选项
    all_intervals = list(INTERVALS.values())
    correct_answer = interval_info['name']
    
    # 根据 allowed_intervals 控制选项范围
    allowed_intervals_set = set(allowed_intervals)
    allowed_interval_names = [interval['name'] for interval in all_intervals if interval['name'] in allowed_intervals_set]
    
    if len(allowed_interval_names) <= 4:
        # 如果允许的音程数量少于等于4个，全部使用
        options = allowed_interval_names.copy()
        # 确保正确答案在选项中
        if correct_answer not in options:
            if len(options) < 4:
                options.append(correct_answer)
            else:
                options[0] = correct_answer
        # 如果选项不足4个，从所有音程中补充
        while len(options) < 4:
            all_interval_names = [interval['name'] for interval in all_intervals if interval['name'] != 'unison']
            additional = [name for name in all_interval_names if name not in options]
            if additional:
                options.append(random.choice(additional))
            else:
                break
        random.shuffle(options)
    else:
        # 如果允许的音程数量超过4个，随机选择3个错误答案+1个正确答案
        wrong_options = [name for name in allowed_interval_names if name != correct_answer]
        if len(wrong_options) >= 3:
            options = random.sample(wrong_options, 3) + [correct_answer]
        else:
            options = wrong_options + [correct_answer]
            # 如果还不够4个，从所有音程中补充
            all_interval_names = [interval['name'] for interval in all_intervals if interval['name'] != 'unison']
            while len(options) < 4:
                additional = [name for name in all_interval_names if name not in options]
                if additional:
                    options.append(random.choice(additional))
                else:
                    break
        random.shuffle(options)
    
    return jsonify({
        'status': 'ok',
        'audio_file': audio_file,
        'options': [next((interval['cn'] for interval in all_intervals if interval['name'] == opt), opt) for opt in options],
        'option_values': options,
        'correct_answer': interval_info['cn'],
        'correct_value': correct_answer,
        'is_authenticated': current_user.is_authenticated
    })

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    """提交答案"""
    data = request.get_json()
    user_answer = data.get('answer', '')
    correct_value = data.get('correct_value', '')
    
    is_correct = (user_answer == correct_value)
    
    # 如果用户已登录，保存到数据库
    if current_user.is_authenticated:
        # TODO: 实现数据库保存逻辑
        pass
    
    # 获取用户答案的中文名称
    user_answer_cn = user_answer
    for interval in INTERVALS.values():
        if interval['name'] == user_answer:
            user_answer_cn = interval['cn']
            break
    
    correct_answer_cn = next((interval['cn'] for interval in INTERVALS.values() if interval['name'] == correct_value), correct_value)
    
    return jsonify({
        'status': 'ok',
        'is_correct': is_correct,
        'correct_answer': correct_answer_cn,
        'user_answer': user_answer_cn,
        'is_authenticated': current_user.is_authenticated
    })

# 用户认证路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('该邮箱已注册')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
        if not user:
            flash('用户不存在')
            return redirect(url_for('login'))
        if not user.check_password(password):
            flash('密码错误')
            return redirect(url_for('login'))
        login_user(user)
        flash('登录成功')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已登出')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)

