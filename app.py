from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, PracticeSession, UserAnswer, Question
from datetime import datetime, timedelta, date
import random
import os
import json
import logging
import sys


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'opear_secret_key_2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'opear.db')
# 禁用静态文件缓存（开发环境）
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 添加缓存控制头
@app.after_request
def set_cache_control(response: Response):
    """设置缓存控制头，防止浏览器缓存HTML页面"""
    # 对于HTML页面，禁用缓存
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    # 对于JSON响应，也禁用缓存
    elif response.content_type and 'application/json' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
    # 对于静态文件（CSS/JS），设置较短的缓存时间（开发环境）
    elif response.content_type and any(ct in response.content_type for ct in ['text/css', 'application/javascript', 'text/javascript']):
        response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    return response

# 练习类型定义
EXERCISE_TYPES = {
    'interval': {
        'name': '音程识别',
        'name_en': 'Interval',
        'icon': '🎵',
        'description': '识别两个音符之间的音程关系',
        'category': '基础训练'
    },
    'scale_degree': {
        'name': '音阶练习',
        'name_en': 'Scale Degree',
        'icon': '🎹',
        'description': '识别音阶中的特定音级',
        'category': '音阶训练'
    },
    'chord_quality': {
        'name': '和弦识别',
        'name_en': 'Chord Quality',
        'icon': '🎼',
        'description': '识别和弦的类型和性质',
        'category': '和弦训练'
    },
    'chord_inversion': {
        'name': '和弦转位',
        'name_en': 'Chord Inversion',
        'icon': '🔄',
        'description': '识别和弦的转位形式',
        'category': '和弦训练',
        'status': 'developing'
    },
    'chord_progression': {
        'name': '和弦进行',
        'name_en': 'Chord Progression',
        'icon': '🎶',
        'description': '识别和弦进行的模式',
        'category': '进阶训练',
        'status': 'developing'
    },
    'melody': {
        'name': '旋律片段',
        'name_en': 'Melody',
        'icon': '💿',
        'description': '识别音阶中的旋律片段',
        'category': '旋律训练',
        'status': 'developing'
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

# 音阶定义（半音数序列，从根音开始）
SCALES = {
    'major': {
        'name': '大调',
        'name_en': 'Major',
        'pattern': [0, 2, 4, 5, 7, 9, 11],  # 全全半全全全半
        'degrees': ['1', '2', '3', '4', '5', '6', '7']
    },
    'pentatonic_major': {
        'name': '大调五声音阶',
        'name_en': 'Major Pentatonic',
        'pattern': [0, 2, 4, 7, 9],
        'degrees': ['1', '2', '3', '5', '6']
    },
    'pentatonic_minor': {
        'name': '小调五声音阶',
        'name_en': 'Minor Pentatonic',
        'pattern': [0, 3, 5, 7, 10],
        'degrees': ['1', 'b3', '4', '5', 'b7']
    },
    'dorian': {
        'name': '多利亚调式',
        'name_en': 'Dorian',
        'pattern': [0, 2, 3, 5, 7, 9, 10],
        'degrees': ['1', '2', 'b3', '4', '5', '6', 'b7']
    },
    'mixolydian': {
        'name': '混合利底亚调式',
        'name_en': 'Mixolydian',
        'pattern': [0, 2, 4, 5, 7, 9, 10],
        'degrees': ['1', '2', '3', '4', '5', '6', 'b7']
    },
    'blues': {
        'name': '布鲁斯音阶',
        'name_en': 'Blues',
        'pattern': [0, 3, 5, 6, 7, 10],
        'degrees': ['1', 'b3', '4', 'b5', '5', 'b7']
    },
    'natural_minor': {
        'name': '自然小调',
        'name_en': 'Natural Minor',
        'pattern': [0, 2, 3, 5, 7, 8, 10],  # 等同于minor
        'degrees': ['1', '2', 'b3', '4', '5', 'b6', 'b7']
    },
    'harmonic_minor': {
        'name': '和声小调',
        'name_en': 'Harmonic Minor',
        'pattern': [0, 2, 3, 5, 7, 8, 11],  # 第七音升高半音
        'degrees': ['1', '2', 'b3', '4', '5', 'b6', '7']
    },
    'melodic_minor': {
        'name': '旋律小调',
        'name_en': 'Melodic Minor',
        'pattern': [0, 2, 3, 5, 7, 9, 11],  # 上行：第六、七音升高半音
        'degrees': ['1', '2', 'b3', '4', '5', '6', '7']
    },
    'ionian': {
        'name': '伊奥尼亚调式',
        'name_en': 'Ionian',
        'pattern': [0, 2, 4, 5, 7, 9, 11],  # 等同于major
        'degrees': ['1', '2', '3', '4', '5', '6', '7']
    },
    'lydian': {
        'name': '利底亚调式',
        'name_en': 'Lydian',
        'pattern': [0, 2, 4, 6, 7, 9, 11],  # 第四音升高半音
        'degrees': ['1', '2', '3', '#4', '5', '6', '7']
    },
    'phrygian': {
        'name': '弗里几亚调式',
        'name_en': 'Phrygian',
        'pattern': [0, 1, 3, 5, 7, 8, 10],  # 第二音降低半音
        'degrees': ['1', 'b2', 'b3', '4', '5', 'b6', 'b7']
    },
    'locrian': {
        'name': '洛克里亚调式',
        'name_en': 'Locrian',
        'pattern': [0, 1, 3, 5, 6, 8, 10],  # 第二、五音降低半音
        'degrees': ['1', 'b2', 'b3', '4', 'b5', 'b6', 'b7']
    },
    'aeolian': {
        'name': '爱奥利亚调式',
        'name_en': 'Aeolian',
        'pattern': [0, 2, 3, 5, 7, 8, 10],  # 等同于natural_minor
        'degrees': ['1', '2', 'b3', '4', '5', 'b6', 'b7']
    },
    'whole_tone': {
        'name': '全音阶',
        'name_en': 'Whole Tone',
        'pattern': [0, 2, 4, 6, 8, 10],  # 全音阶（6个音）
        'degrees': ['1', '2', '3', '#4', '#5', 'b7']
    },
    'diminished': {
        'name': '减音阶',
        'name_en': 'Diminished',
        'pattern': [0, 2, 3, 5, 6, 8, 9, 11],  # 减音阶（8个音）
        'degrees': ['1', '2', 'b3', '4', 'b5', 'b6', '6', '7']
    },
    'blues_scale': {
        'name': '布鲁斯音阶',
        'name_en': 'Blues Scale',
        'pattern': [0, 3, 5, 6, 7, 10],  # 等同于blues
        'degrees': ['1', 'b3', '4', 'b5', '5', 'b7']
    }
}

# 调性（12个调）
KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# 和弦类型定义（参照open-ear）
CHORD_TYPES = {
    'major': {'name': 'Major Triad', 'cn': '大三和弦', 'pattern': [0, 4, 7]},  # 根音、大三度、纯五度
    'minor': {'name': 'Minor Triad', 'cn': '小三和弦', 'pattern': [0, 3, 7]},  # 根音、小三度、纯五度
    'diminished': {'name': 'Diminished Triad', 'cn': '减三和弦', 'pattern': [0, 3, 6]},  # 根音、小三度、减五度
    'augmented': {'name': 'Augmented Triad', 'cn': '增三和弦', 'pattern': [0, 4, 8]},  # 根音、大三度、增五度
    'sus4': {'name': 'Suspended 4th', 'cn': '挂四和弦', 'pattern': [0, 5, 7]},  # 根音、纯四度、纯五度
    'sus2': {'name': 'Suspended 2nd', 'cn': '挂二和弦', 'pattern': [0, 2, 7]},  # 根音、大二度、纯五度
    'major6th': {'name': 'Major 6th', 'cn': '大六和弦', 'pattern': [0, 4, 7, 9]},  # 根音、大三度、纯五度、大六度
    'minor6th': {'name': 'Minor 6th', 'cn': '小六和弦', 'pattern': [0, 3, 7, 9]},  # 根音、小三度、纯五度、大六度
    'major7th': {'name': 'Major 7th', 'cn': '大七和弦', 'pattern': [0, 4, 7, 11]},  # 根音、大三度、纯五度、大七度
    'minor7th': {'name': 'Minor 7th', 'cn': '小七和弦', 'pattern': [0, 3, 7, 10]},  # 根音、小三度、纯五度、小七度
    'dominant7th': {'name': 'Dominant 7th', 'cn': '属七和弦', 'pattern': [0, 4, 7, 10]},  # 根音、大三度、纯五度、小七度
    'diminished7th': {'name': 'Diminished 7th', 'cn': '减七和弦', 'pattern': [0, 3, 6, 9]},  # 根音、小三度、减五度、减七度
    'half_diminished7th': {'name': 'Half Diminished 7th', 'cn': '半减七和弦', 'pattern': [0, 3, 6, 10]},  # 根音、小三度、减五度、小七度
    'major9th': {'name': 'Major 9th', 'cn': '大九和弦', 'pattern': [0, 4, 7, 11, 14]},  # 根音、大三度、纯五度、大七度、大九度
    'minor9th': {'name': 'Minor 9th', 'cn': '小九和弦', 'pattern': [0, 3, 7, 10, 14]},  # 根音、小三度、纯五度、小七度、大九度
    'dominant9th': {'name': 'Dominant 9th', 'cn': '属九和弦', 'pattern': [0, 4, 7, 10, 14]},  # 根音、大三度、纯五度、小七度、大九度
    'dominant11th': {'name': 'Dominant 11th', 'cn': '属十一和弦', 'pattern': [0, 4, 7, 10, 14, 17]},  # 根音、大三度、纯五度、小七度、大九度、纯十一度
    'minor11th': {'name': 'Minor 11th', 'cn': '小十一和弦', 'pattern': [0, 3, 7, 10, 14, 17]},  # 根音、小三度、纯五度、小七度、大九度、纯十一度
    'dominant13th': {'name': 'Dominant 13th', 'cn': '属十三和弦', 'pattern': [0, 4, 7, 10, 14, 17, 21]},  # 根音、大三度、纯五度、小七度、大九度、纯十一度、大十三度
}

# 大调音阶中的罗马数字和弦映射（I, ii, iii, IV, V, vi, vii°）
ROMAN_NUMERAL_CHORDS = {
    'I': {'chord_type': 'major', 'scale_degree': 0},      # C大调：C大三和弦
    'ii': {'chord_type': 'minor', 'scale_degree': 2},     # C大调：D小三和弦
    'iii': {'chord_type': 'minor', 'scale_degree': 4},    # C大调：E小三和弦
    'IV': {'chord_type': 'major', 'scale_degree': 5},     # C大调：F大三和弦
    'V': {'chord_type': 'major', 'scale_degree': 7},      # C大调：G大三和弦
    'vi': {'chord_type': 'minor', 'scale_degree': 9},     # C大调：A小三和弦
    'vii°': {'chord_type': 'diminished', 'scale_degree': 11},  # C大调：B减三和弦
}

def generate_interval_audio(note1, note2, duration=1.0):
    """生成音程音频文件"""
    try:
        import numpy as np
        from scipy.io import wavfile
        
        # 音频文件路径
        notes_dir = os.path.join(basedir, 'static', 'audio', 'notes')
        note1_path = os.path.join(notes_dir, f"{note1}.wav")
        note2_path = os.path.join(notes_dir, f"{note2}.wav")
        
        if not os.path.exists(note1_path) or not os.path.exists(note2_path):
            return False
        
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
    """从data/songs目录加载歌曲数据"""
    songs_data = {}
    songs_dir = os.path.join(basedir, 'data', 'songs')
    
    if not os.path.exists(songs_dir):
        # 尝试另一个路径
        songs_dir = os.path.join(os.path.dirname(basedir), 'openEar', 'data', 'songs')
        if not os.path.exists(songs_dir):
            return {}
    
    # 遍历songs目录下的所有子目录（interval, scale_degree, chord_quality等）
    for exercise_type_dir in os.listdir(songs_dir):
        exercise_type_path = os.path.join(songs_dir, exercise_type_dir)
        if not os.path.isdir(exercise_type_path):
            continue
        
        # 初始化该练习类型的数据结构
        if exercise_type_dir not in songs_data:
            songs_data[exercise_type_dir] = {}
        
        # 遍历该目录下的所有JSON文件
        for json_file in os.listdir(exercise_type_path):
            if not json_file.endswith('.json'):
                continue
            
            # 获取文件名（不含扩展名）作为key，如major_second
            key = json_file[:-5]  # 去掉.json后缀
            json_path = os.path.join(exercise_type_path, json_file)
            
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    songs_list = json.load(f)
                    # 确保是列表格式
                    if isinstance(songs_list, list):
                        songs_data[exercise_type_dir][key] = songs_list
                    else:
                        songs_data[exercise_type_dir][key] = []
            except Exception as e:
                print(f"加载歌曲文件失败 {json_path}: {e}")
                continue
    
    return songs_data

def load_intervals_scales_kb():
    """加载音程和音阶知识库（已废弃，改用Markdown笔记）"""
    return {'intervals': [], 'scales': []}

def load_notes_markdown(note_type='intervals'):
    """加载音程或音阶的Markdown笔记"""
    notes_file = os.path.join(basedir, 'knowledge_base', 'videos', 'notes', f'{note_type}.md')
    if not os.path.exists(notes_file):
        notes_file = os.path.join(os.path.dirname(basedir), 'openEar', 'knowledge_base', 'videos', 'notes', f'{note_type}.md')
    
    if os.path.exists(notes_file):
        try:
            with open(notes_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"加载笔记文件失败: {e}")
            return None
    return None

def match_interval_to_kb(interval_name, kb_data, direction='ascending'):
    """根据音程名称匹配知识库数据"""
    # 音程名称映射（从代码中的名称到知识库中的名称）
    # 注意：知识库中可能使用不同的命名，需要灵活匹配
    name_mapping = {
        'minor_second': ['minor second', 'semitone', 'half step'],
        'major_second': ['major second', 'tone', 'whole step'],
        'minor_third': ['minor third'],
        'major_third': ['major third'],
        'perfect_fourth': ['perfect fourth'],
        'tritone': ['tritone', 'augmented fourth', 'diminished fifth'],
        'perfect_fifth': ['perfect fifth'],
        'minor_sixth': ['minor sixth'],
        'major_sixth': ['major sixth'],
        'minor_seventh': ['minor seventh'],
        'major_seventh': ['major seventh'],
        'octave': ['octave']
    }
    
    # 查找匹配的音程
    search_names = name_mapping.get(interval_name, [interval_name.replace('_', ' ')])
    
    # 优先匹配指定方向的音程
    matched_intervals = []
    for interval in kb_data.get('intervals', []):
        kb_name = interval.get('name_en', '').lower().strip()
        kb_direction = interval.get('direction', 'ascending')
        
        for search_name in search_names:
            search_lower = search_name.lower().strip()
            # 精确匹配名称
            if kb_name == search_lower:
                matched_intervals.append((interval, kb_direction == direction))
    
    # 如果找到匹配方向的，优先返回
    for interval, direction_match in matched_intervals:
        if direction_match:
            return interval
    
    # 如果没有找到匹配方向的，返回第一个匹配的（通常是ascending）
    if matched_intervals:
        return matched_intervals[0][0]
    
    # 再尝试包含匹配（但要更严格）
    for interval in kb_data.get('intervals', []):
        kb_name = interval.get('name_en', '').lower().strip()
        kb_direction = interval.get('direction', 'ascending')
        
        for search_name in search_names:
            search_lower = search_name.lower().strip()
            # 避免误匹配：semitone 不应该匹配 major second
            if interval_name == 'major_second' and ('semitone' in kb_name or 'minor' in kb_name):
                continue
            if interval_name == 'minor_second' and 'major' in kb_name:
                continue
            # 包含匹配（要求至少匹配主要关键词）
            if search_lower in kb_name:
                # 对于复合词，要求匹配主要部分
                if interval_name in ['minor_second', 'major_second']:
                    if 'second' in kb_name:
                        if kb_direction == direction:
                            return interval
                elif interval_name in ['minor_third', 'major_third']:
                    if 'third' in kb_name:
                        if kb_direction == direction:
                            return interval
                elif interval_name in ['minor_sixth', 'major_sixth']:
                    if 'sixth' in kb_name:
                        if kb_direction == direction:
                            return interval
                elif interval_name in ['minor_seventh', 'major_seventh']:
                    if 'seventh' in kb_name:
                        if kb_direction == direction:
                            return interval
                else:
                    if kb_direction == direction:
                        return interval
    
    # 如果还是没有找到匹配方向的，返回第一个匹配的
    for interval in kb_data.get('intervals', []):
        kb_name = interval.get('name_en', '').lower().strip()
        for search_name in search_names:
            search_lower = search_name.lower().strip()
            if search_lower in kb_name:
                if interval_name in ['minor_second', 'major_second']:
                    if 'second' in kb_name:
                        return interval
                elif interval_name in ['minor_third', 'major_third']:
                    if 'third' in kb_name:
                        return interval
                elif interval_name in ['minor_sixth', 'major_sixth']:
                    if 'sixth' in kb_name:
                        return interval
                elif interval_name in ['minor_seventh', 'major_seventh']:
                    if 'seventh' in kb_name:
                        return interval
                else:
                    return interval
    
    return None

def match_scale_to_kb(scale_name, kb_data):
    """根据音阶名称匹配知识库数据"""
    # 音阶名称映射
    name_mapping = {
        'major': ['major scale', 'major'],
        'minor': ['natural minor', 'minor scale', 'minor'],
        'harmonic_minor': ['harmonic minor'],
        'melodic_minor': ['melodic minor'],
        'dorian': ['dorian'],
        'mixolydian': ['mixolydian'],
        'lydian': ['lydian'],
        'phrygian': ['phrygian'],
        'locrian': ['locrian']
    }
    
    # 查找匹配的音阶
    search_names = name_mapping.get(scale_name, [scale_name.replace('_', ' ')])
    
    for scale in kb_data.get('scales', []):
        kb_name = scale.get('name_en', '').lower()
        for search_name in search_names:
            if search_name.lower() in kb_name or kb_name in search_name.lower():
                return scale
    
    return None

# 初始化数据库
init_done = False
@app.before_request
def create_tables():
    global init_done
    if not init_done:
        db.create_all()
        init_done = True

# 路由
def get_accuracy_level(accuracy):
    """根据准确率返回ABCDE等级"""
    if accuracy >= 80:
        return 'A'
    elif accuracy >= 60:
        return 'B'
    elif accuracy >= 40:
        return 'C'
    elif accuracy >= 20:
        return 'D'
    else:
        return 'E'

@app.route('/')
def index():
    """首页 - 练习选择"""
    # 获取用户统计数据
    exercise_stats = {}
    if current_user.is_authenticated:
        for exercise_type in EXERCISE_TYPES.keys():
            # 查询该练习类型的所有会话
            sessions = PracticeSession.query.filter_by(
                user_id=current_user.id,
                exercise_type=exercise_type
            ).all()
            
            # 计算总时长（分钟）
            total_duration_minutes = sum((s.duration or 0) for s in sessions) // 60
            
            # 计算总题数和正确数
            total_questions = sum((s.total_questions or 0) for s in sessions)
            total_correct = sum((s.correct_answers or 0) for s in sessions)
            
            # 计算准确率
            accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
            
            # 计算练习次数
            practice_count = len(sessions)
            
            # 获取等级
            level = get_accuracy_level(accuracy) if total_questions > 0 else 'E'
            
            exercise_stats[exercise_type] = {
                'duration_minutes': total_duration_minutes,
                'accuracy': accuracy,
                'practice_count': practice_count,
                'level': level
            }
    else:
        # 未登录用户，所有统计为0
        for exercise_type in EXERCISE_TYPES.keys():
            exercise_stats[exercise_type] = {
                'duration_minutes': 0,
                'accuracy': 0,
                'practice_count': 0,
                'level': 'E'
            }
    
    return render_template('index.html', 
                         exercise_types=EXERCISE_TYPES,
                         exercise_stats=exercise_stats,
                         current_user=current_user)

@app.route('/about')
def about():
    """关于页面"""
    return render_template('about.html', 
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
    
    # 加载Markdown笔记
    intervals_notes = load_notes_markdown('intervals')
    scales_notes = load_notes_markdown('scales')
    
    # 为了向后兼容，保留空的kb字典
    intervals_kb = {}
    scales_kb = {}
    
    return render_template('practice.html',
                         exercise_type=exercise_type,
                         exercise_info=EXERCISE_TYPES[exercise_type],
                         intervals=INTERVALS,
                         scales=SCALES,
                         keys=KEYS,
                         chord_types=CHORD_TYPES,
                         roman_numerals=list(ROMAN_NUMERAL_CHORDS.keys()),
                         tips=tips_data.get(exercise_type, {}),
                         songs_data=songs_data,  # 传递完整的songs_data
                         songs=songs_data.get(exercise_type, {}),  # 向后兼容
                         intervals_kb=intervals_kb,
                         scales_kb=scales_kb,
                         intervals_notes=intervals_notes,
                         scales_notes=scales_notes,
                         current_user=current_user)

def generate_root_audio_4sec(key, octave, root_note_openear, piano_samples_dir):
    """生成4秒的根音音频文件
    
    Args:
        key: 调性（如 'C'）
        octave: 八度（如 4）
        root_note_openear: 根音名称（openEar格式，如 'C4'）
        piano_samples_dir: 钢琴样本目录
    
    Returns:
        成功返回文件路径（相对于 static/audio/），失败返回 None
    """
    try:
        from pydub import AudioSegment
    except ImportError as e:
        # 如果没有pydub，直接返回None
        print(f"⚠️ pydub 未安装，无法生成缩短版根音音频: {e}")
        return None
    
    try:
        # 构建输出文件名
        safe_key = key.replace('#', 'sharp')
        scale_dir = os.path.join(basedir, 'static', 'audio', 'scale')
        
        # 确保目录存在（移动端可能需要）
        try:
            os.makedirs(scale_dir, exist_ok=True)
        except Exception as e:
            print(f"⚠️ 无法创建目录 {scale_dir}: {e}")
            print(f"   错误类型: {type(e).__name__}")
            return None
        
        output_filename = f"{safe_key}_root_oct{octave}_4sec.mp3"
        output_path = os.path.join(scale_dir, output_filename)
        
        # 如果文件已存在，直接返回
        if os.path.exists(output_path):
            print(f"✅ 使用已存在的缩短版根音音频: {output_path}")
            return f"scale/{output_filename}"
        
        # 读取根音MP3文件
        root_file = os.path.join(piano_samples_dir, f"{root_note_openear}.mp3")
        if not os.path.exists(root_file):
            print(f"⚠️ 根音文件不存在: {root_file}")
            print(f"   查找的文件名: {root_note_openear}.mp3")
            print(f"   目录: {piano_samples_dir}")
            print(f"   目录是否存在: {os.path.exists(piano_samples_dir)}")
            # 列出目录中的文件（调试用）
            if os.path.exists(piano_samples_dir):
                try:
                    files = os.listdir(piano_samples_dir)
                    print(f"   目录中的文件数量: {len(files)}")
                    similar_files = [f for f in files if root_note_openear.split('s')[0] in f]
                    if similar_files:
                        print(f"   相似文件: {similar_files[:5]}")
                    else:
                        # 列出前几个文件作为参考
                        print(f"   目录中的前5个文件: {files[:5]}")
                except Exception as e:
                    print(f"   无法列出目录文件: {e}")
            return None
        
        # 加载MP3文件
        try:
            print(f"📂 加载根音文件: {root_file}")
            audio_segment = AudioSegment.from_mp3(root_file)
            print(f"   文件时长: {len(audio_segment)/1000:.2f}秒")
        except Exception as e:
            print(f"⚠️ 无法加载音频文件 {root_file}: {e}")
            print(f"   错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return None
        
        # 截取前4秒
        audio_segment = audio_segment[:4000]  # 4秒 = 4000毫秒
        
        # 导出为MP3
        try:
            print(f"💾 导出缩短版根音音频: {output_path}")
            audio_segment.export(output_path, format="mp3")
            print(f"✅ 成功生成4秒根音音频: {output_path}")
            return f"scale/{output_filename}"
        except Exception as e:
            print(f"⚠️ 无法导出音频文件 {output_path}: {e}")
            print(f"   错误类型: {type(e).__name__}")
            # 检查目录权限
            if not os.access(scale_dir, os.W_OK):
                print(f"   目录无写权限: {scale_dir}")
            else:
                print(f"   目录有写权限，可能是其他问题")
            import traceback
            traceback.print_exc()
            return None
        
    except Exception as e:
        print(f"❌ 生成根音音频失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

def generate_song_audio_1min(audio_path):
    """生成1分钟版本的歌曲音频文件
    
    Args:
        audio_path: 原始音频文件路径（相对于 static/audio/）
        例如: "songs/Somewhere_Over_the_Rainbow_Unknown.mp3"
    
    Returns:
        缩短后的音频文件路径（相对于 static/audio/），如果失败返回 None
    """
    try:
        from pydub import AudioSegment
        
        # 构建完整路径
        full_audio_path = os.path.join(basedir, 'static', 'audio', audio_path)
        
        if not os.path.exists(full_audio_path):
            print(f"⚠️ 音频文件不存在: {full_audio_path}")
            return None
        
        # 构建输出路径（在 songs_1min 目录下）
        audio_dir = os.path.dirname(audio_path)  # "songs"
        audio_filename = os.path.basename(audio_path)  # "Somewhere_Over_the_Rainbow_Unknown.mp3"
        
        # 创建缩短版本的目录
        output_dir = os.path.join(basedir, 'static', 'audio', audio_dir + '_1min')
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            print(f"⚠️ 无法创建目录 {output_dir}: {e}")
            return None
        
        output_path = os.path.join(output_dir, audio_filename)
        
        # 如果1分钟版本已存在，直接返回
        if os.path.exists(output_path):
            return os.path.join(audio_dir + '_1min', audio_filename)
        
        # 加载原始音频
        try:
            audio_segment = AudioSegment.from_mp3(full_audio_path)
        except Exception as e:
            print(f"⚠️ 无法加载音频文件 {full_audio_path}: {e}")
            return None
        
        # 获取音频时长（毫秒）
        duration_ms = len(audio_segment)
        max_duration_ms = 60 * 1000  # 60秒 = 60000毫秒
        
        # 如果音频已经小于1分钟，直接返回原文件路径
        if duration_ms <= max_duration_ms:
            return audio_path
        
        # 截取前60秒
        shortened_audio = audio_segment[:max_duration_ms]
        
        # 导出为MP3
        try:
            shortened_audio.export(output_path, format="mp3")
            print(f"✅ 生成1分钟版本: {output_path} (原始: {duration_ms/1000:.1f}秒)")
            return os.path.join(audio_dir + '_1min', audio_filename)
        except Exception as e:
            print(f"⚠️ 无法导出音频文件 {output_path}: {e}")
            if not os.access(output_dir, os.W_OK):
                print(f"   目录无写权限: {output_dir}")
            return None
        
    except ImportError as e:
        # 如果没有pydub，返回原文件路径
        print(f"⚠️ pydub 未安装，无法生成缩短版本: {e}")
        return audio_path
    except Exception as e:
        print(f"❌ 生成1分钟音频失败: {e}")
        import traceback
        traceback.print_exc()
        # 失败时返回原文件路径，确保功能可用
        return audio_path

def generate_scale_audio_from_mp3(key, scale_type, octave, scale_notes, piano_samples_dir, convert_note_name):
    """从MP3文件拼接生成完整的音阶音频（8个音符，每个0.5秒）
    
    Args:
        key: 调性（如 'C'）
        scale_type: 音阶类型（如 'major'）
        octave: 起始八度（如 4）
        scale_notes: 音阶音符列表（8个音符）
        piano_samples_dir: 钢琴样本目录
        convert_note_name: 音符名称转换函数
    """
    print(f"🔧 generate_scale_audio_from_mp3 开始执行")
    print(f"   参数: key={key}, scale_type={scale_type}, octave={octave}")
    print(f"   scale_notes: {scale_notes}")
    print(f"   piano_samples_dir: {piano_samples_dir}")
    
    try:
        from pydub import AudioSegment
        print(f"✅ pydub 导入成功")
        
        # 构建输出文件名
        safe_key = key.replace('#', 'sharp')
        safe_scale = scale_type.replace('_', '-')
        scale_dir = os.path.join(basedir, 'static', 'audio', 'scale')
        
        # 确保目录存在（移动端可能需要）
        try:
            os.makedirs(scale_dir, exist_ok=True)
        except Exception as e:
            print(f"⚠️ 无法创建目录 {scale_dir}: {e}")
            return None
        
        output_filename = f"{safe_key}_{safe_scale}_oct{octave}_full.mp3"
        output_path = os.path.join(scale_dir, output_filename)
        
        # 如果文件已存在，直接返回
        if os.path.exists(output_path):
            return f"scale/{output_filename}"
        
        # 拼接所有音符（每个0.5秒）
        combined_audio = None
        note_duration_ms = 500  # 0.5秒 = 500毫秒
        
        print(f"📝 开始拼接 {len(scale_notes)} 个音符")
        
        for idx, note in enumerate(scale_notes, 1):
            note_openear = convert_note_name(note)
            note_file = os.path.join(piano_samples_dir, f"{note_openear}.mp3")
            
            print(f"   [{idx}/{len(scale_notes)}] 处理音符: {note} -> {note_openear}")
            print(f"      文件路径: {note_file}")
            
            if not os.path.exists(note_file):
                print(f"⚠️ 音阶音符文件不存在: {note} -> {note_openear} -> {note_file}")
                # 列出目录中的文件（调试用）
                if os.path.exists(piano_samples_dir):
                    files = os.listdir(piano_samples_dir)
                    print(f"      目录中的文件数量: {len(files)}")
                    similar_files = [f for f in files if note_openear.split('s')[0] in f]
                    if similar_files:
                        print(f"      相似文件: {similar_files[:5]}")
                    else:
                        print(f"      目录中的前5个文件: {files[:5]}")
                import sys
                sys.stderr.write(f"⚠️ 音阶音符文件不存在: {note_file}\n")
                return None
            
            # 加载MP3文件
            try:
                print(f"      加载音频文件...")
                audio_segment = AudioSegment.from_mp3(note_file)
                print(f"      音频时长: {len(audio_segment)/1000:.2f}秒")
            except Exception as e:
                print(f"⚠️ 无法加载音频文件 {note_file}: {e}")
                import sys
                sys.stderr.write(f"⚠️ 无法加载音频文件 {note_file}: {e}\n")
                import traceback
                traceback.print_exc()
                return None
            
            # 截取前0.5秒
            audio_segment = audio_segment[:note_duration_ms]
            
            # 拼接
            if combined_audio is None:
                combined_audio = audio_segment
                print(f"      初始化拼接音频")
            else:
                combined_audio = combined_audio + audio_segment
                print(f"      拼接完成，当前总时长: {len(combined_audio)/1000:.2f}秒")
        
        if combined_audio is None:
            print(f"❌ 拼接音频为空")
            import sys
            sys.stderr.write("❌ 拼接音频为空\n")
            return None
        
        print(f"✅ 所有音符拼接完成，总时长: {len(combined_audio)/1000:.2f}秒")
        print(f"📁 准备导出到: {output_path}")
        
        # 导出为MP3
        try:
            print(f"💾 开始导出MP3文件...")
            combined_audio.export(output_path, format="mp3")
            print(f"✅ 生成完整音阶音频: {output_path} (总时长: {len(combined_audio)/1000:.2f}秒)")
            import sys
            sys.stdout.write(f"✅ 生成完整音阶音频: {output_path}\n")
        except Exception as e:
            print(f"⚠️ 无法导出音频文件 {output_path}: {e}")
            import sys
            sys.stderr.write(f"⚠️ 无法导出音频文件 {output_path}: {e}\n")
            import traceback
            traceback.print_exc()
            # 检查目录权限
            if not os.access(scale_dir, os.W_OK):
                print(f"   目录无写权限: {scale_dir}")
                sys.stderr.write(f"   目录无写权限: {scale_dir}\n")
            return None
        
        return f"scale/{output_filename}"
        
    except ImportError as e:
        # 如果没有pydub，直接返回None
        error_msg = f"⚠️ pydub 未安装: {e}"
        print(error_msg)
        import sys
        sys.stderr.write(f"{error_msg}\n")
        return None
    except Exception as e:
        error_msg = f"❌ 生成音阶音频失败: {e}"
        print(error_msg)
        import sys
        sys.stderr.write(f"{error_msg}\n")
        import traceback
        traceback.print_exc()
        return None

def generate_scale_audio(root_note, scale_type, octave=4, octave_range=1):
    """生成音阶音频文件（一个八度，从根音到根音）
    
    Args:
        root_note: 根音（如 'C'）
        scale_type: 音阶类型（如 'major'）
        octave: 起始八度（如 4）
        octave_range: 八度范围（此参数保留用于兼容，但参考音频只生成一个八度）
    """
    try:
        import numpy as np
        from scipy.io import wavfile
        
        if scale_type not in SCALES:
            return False
        
        scale_pattern = SCALES[scale_type]['pattern']
        root_idx = KEYS.index(root_note)
        
        # 构建一个八度的音阶音符（从根音到根音）
        scale_notes = []
        for semitone_offset in scale_pattern:
            note_idx = (root_idx + semitone_offset) % 12
            note_name = note_letters[note_idx]
            # 计算实际八度
            actual_octave = octave + (root_idx + semitone_offset) // 12
            scale_notes.append(f"{note_name}{actual_octave}")
        
        # 在最后添加根音（高八度）
        root_note_octave = octave + 1
        scale_notes.append(f"{root_note}{root_note_octave}")
        
        # 读取所有音符的音频
        audio_segments = []
        sample_rate = None
        
        notes_dir = os.path.join(basedir, 'static', 'audio', 'notes')
        
        for note in scale_notes:
            note_path = os.path.join(notes_dir, f"{note}.wav")
            
            if not os.path.exists(note_path):
                return False
            
            sr, audio = wavfile.read(note_path)
            if sample_rate is None:
                sample_rate = sr
            
            # 处理多声道
            if len(audio.shape) > 1:
                audio = audio[:, 0]
            
            # 取前0.5秒
            samples = int(sample_rate * 0.5)
            audio_seg = audio[:min(samples, len(audio))]
            if len(audio_seg) < samples:
                padding = np.zeros(samples - len(audio_seg), dtype=audio_seg.dtype)
                audio_seg = np.concatenate([audio_seg, padding])
            
            audio_segments.append(audio_seg)
        
        # 拼接所有音符（从根音到根音）
        combined_audio = np.concatenate(audio_segments)
        
        # 保存音频文件
        safe_root = root_note.replace('#', 'sharp')
        safe_scale = scale_type.replace('_', '-')
        scale_dir = os.path.join(basedir, 'static', 'audio', 'scale')
        os.makedirs(scale_dir, exist_ok=True)
        output_path = os.path.join(scale_dir, f"{safe_root}_{safe_scale}_oct{octave}_range{octave_range}.wav")
        wavfile.write(output_path, sample_rate, combined_audio)
        
        return True
        
    except Exception as e:
        print(f"生成音阶音频失败: {e}")
        return False

@app.route('/api/generate_question/<exercise_type>')
def generate_question(exercise_type):
    """生成题目"""
    try:
        if exercise_type == 'interval':
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
            
            # interval_info 已经从 valid_pairs 中获取，不需要重新计算
            
            
            # 使用音源（MP3格式）
            # 将音符名称转换为格式（如 C4 -> C4, C#4 -> Cs4）
            def convert_note_name(note_name):
                """将音符名称转换为格式"""
                if '#' in note_name:
                    parts = note_name.split('#')
                    if len(parts) == 2:
                        note_letter, octave = parts
                        return f"{note_letter}s{octave}"
                return note_name
            
            note1_openear = convert_note_name(note1)
            note2_openear = convert_note_name(note2)
            
            # 检查音源文件是否存在（使用 piano 音源）
            piano_samples_dir = os.path.join(basedir, 'static', 'audio', 'samples', 'piano')
            note1_file = os.path.join(piano_samples_dir, f"{note1_openear}.mp3")
            note2_file = os.path.join(piano_samples_dir, f"{note2_openear}.mp3")
            
            if not os.path.exists(note1_file) or not os.path.exists(note2_file):
                # 如果文件不存在，尝试其他格式或返回错误
                print(f"⚠️ 音源文件检查失败:")
                print(f"  note1: {note1} -> {note1_openear} -> {note1_file} (exists: {os.path.exists(note1_file)})")
                print(f"  note2: {note2} -> {note2_openear} -> {note2_file} (exists: {os.path.exists(note2_file)})")
                print(f"  piano_dir: {piano_samples_dir} (exists: {os.path.exists(piano_samples_dir)})")
                return jsonify({
                    'status': 'error',
                    'msg': f'音源文件不存在: {note1} ({note1_openear}) 或 {note2} ({note2_openear})。请检查文件路径: {piano_samples_dir}'
                })
            
            # 返回两个音符的文件路径，前端将使用 Web Audio API 播放
            audio_files = {
                'note1': f"samples/piano/{note1_openear}.mp3",
                'note2': f"samples/piano/{note2_openear}.mp3",
                'direction': direction
            }
            
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
            
            
            try:
                return jsonify({
                    'status': 'ok',
                    'audio_files': audio_files,  # 音源格式
                    'note1': note1,
                    'note2': note2,
                    'options': [next((interval['cn'] for interval in all_intervals if interval['name'] == opt), opt) for opt in options],
                    'option_values': options,
                    'correct_answer': interval_info['cn'],
                    'correct_value': correct_answer,
                    'sub_item': correct_answer,  # 细分项：音程名称
                    'is_authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False,
                })
            except Exception as e:
                print(f"❌ 返回JSON时出错: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'status': 'error',
                    'msg': f'生成响应时出错: {str(e)}'
                }), 500
        
        elif exercise_type == 'scale_degree':
            # 获取前端传来的参数
            scale_type = request.args.get('scale_type', 'major')
            key = request.args.get('key', 'C')
            octave = int(request.args.get('octave', '4'))
            octave_range = int(request.args.get('octave_range', '1'))  # 1或2
            
            if scale_type not in SCALES:
                return jsonify({'status': 'error', 'msg': '无效的音阶类型'})
            
            if key not in KEYS:
                return jsonify({'status': 'error', 'msg': '无效的调性'})
            
            if octave_range not in [1, 2]:
                octave_range = 1
            
            scale_info = SCALES[scale_type]
            scale_pattern = scale_info['pattern']
            base_degrees = scale_info['degrees']
            
            # 如果是两个八度，扩展音级名称
            if octave_range == 2:
                # 第一个八度：1, 2, 3, 4, 5, 6, 7
                # 第二个八度：8, 9, 10, 11, 12, 13, 14 或者 1(高八度), 2(高八度)...
                degrees = base_degrees + [f"{deg}(高八度)" for deg in base_degrees]
            else:
                degrees = base_degrees
            
            # 计算根音在NOTE_NAMES中的索引
            root_idx = KEYS.index(key)
            
            # 构建音阶中的所有音符（支持一个或两个八度）
            scale_notes = []
            scale_note_indices = []
            scale_degree_indices = []  # 记录每个音符对应的音级索引
            
            # 生成一个或两个八度的音
            for octave_offset in range(octave_range):
                for degree_idx, semitone_offset in enumerate(scale_pattern):
                    # 计算总的半音偏移
                    total_semitones = octave_offset * 12 + semitone_offset
                    note_idx_in_octave = (root_idx + total_semitones) % 12
                    note_letter = note_letters[note_idx_in_octave]
                    
                    # 计算实际八度
                    actual_octave = octave + (root_idx + total_semitones) // 12
                    note_name = f"{note_letter}{actual_octave}"
                    
                    # 找到在NOTE_NAMES中的索引
                    try:
                        note_idx = NOTE_NAMES.index(note_name)
                    except ValueError:
                        # 如果找不到，尝试其他八度
                        for test_octave in [actual_octave-1, actual_octave, actual_octave+1]:
                            test_note = f"{note_letter}{test_octave}"
                            if test_note in NOTE_NAMES:
                                note_idx = NOTE_NAMES.index(test_note)
                                break
                        else:
                            continue
                    
                    scale_notes.append(note_name)
                    scale_note_indices.append(note_idx)
                    # 计算音级索引：第一个八度用原始索引，第二个八度用原始索引+len(base_degrees)
                    degree_index = degree_idx if octave_offset == 0 else degree_idx + len(base_degrees)
                    scale_degree_indices.append(degree_index)
            
            if not scale_notes:
                return jsonify({'status': 'error', 'msg': '无法构建音阶'})
            
            # 随机选择一个音阶内的音作为题目
            question_idx = random.randint(0, len(scale_notes) - 1)
            question_note = scale_notes[question_idx]
            correct_degree_idx = scale_degree_indices[question_idx]
            correct_degree = degrees[correct_degree_idx]
            
            # 使用音源（MP3格式）
            def convert_note_name(note_name):
                """将音符名称转换为格式"""
                if '#' in note_name:
                    parts = note_name.split('#')
                    if len(parts) == 2:
                        note_letter, octave = parts
                        return f"{note_letter}s{octave}"
                return note_name
            
            question_note_openear = convert_note_name(question_note)
            root_note_openear = convert_note_name(f"{key}{octave}")
            
            # 检查音源文件是否存在（使用 piano 音源）
            piano_samples_dir = os.path.join(basedir, 'static', 'audio', 'samples', 'piano')
            question_audio_file = f"samples/piano/{question_note_openear}.mp3"
            question_audio_path = os.path.join(piano_samples_dir, f"{question_note_openear}.mp3")
            root_audio_path = os.path.join(piano_samples_dir, f"{root_note_openear}.mp3")
            
            if not os.path.exists(question_audio_path):
                print(f"⚠️ 题目音频文件不存在: {question_note} -> {question_note_openear} -> {question_audio_path}")
                return jsonify({'status': 'error', 'msg': f'音源文件不存在: {question_note} ({question_note_openear})'})
            
            if not os.path.exists(root_audio_path):
                print(f"⚠️ 根音文件不存在: {key}{octave} -> {root_note_openear} -> {root_audio_path}")
                return jsonify({'status': 'error', 'msg': f'根音文件不存在: {key}{octave} ({root_note_openear})'})
            
            # 生成4秒的根音音频文件
            root_audio_file = generate_root_audio_4sec(key, octave, root_note_openear, piano_samples_dir)
            if not root_audio_file:
                # 如果无法生成缩短版本，回退到使用原始根音文件
                print(f"⚠️ 无法生成缩短版根音音频，使用原始文件: {root_note_openear}.mp3")
                # 使用原始根音文件路径
                root_audio_file = f"samples/piano/{root_note_openear}.mp3"
                # 验证原始文件是否存在
                if not os.path.exists(root_audio_path):
                    error_msg = f'根音文件不存在: {key}{octave} ({root_note_openear})'
                    print(f"❌ {error_msg}")
                    return jsonify({'status': 'error', 'msg': error_msg})
                print(f"✅ 使用原始根音文件: {root_audio_file}")
            
            # 生成音阶音频（直接拼接成完整音频文件）
            # 构建一个八度的完整音阶（从根音到高八度根音，共8个音符）
            first_octave_count = len(base_degrees)  # 通常是7个音符
            
            # 确保取第一个八度的所有音符
            if octave_range == 1:
                first_octave_notes = scale_notes[:first_octave_count]
            else:
                first_octave_notes = scale_notes[:first_octave_count]
            
            # 添加高八度根音
            root_note_high = f"{key}{octave + 1}"
            scale_notes_for_audio = first_octave_notes + [root_note_high]
            
            print(f"🎵 准备生成音阶音频:")
            print(f"   调性: {key}, 音阶类型: {scale_type}, 八度: {octave}")
            print(f"   音阶音符: {scale_notes_for_audio}")
            print(f"   音符数量: {len(scale_notes_for_audio)}")
            
            # 生成完整的音阶音频文件（拼接8个音符，每个0.5秒）
            scale_audio_file = generate_scale_audio_from_mp3(key, scale_type, octave, scale_notes_for_audio, piano_samples_dir, convert_note_name)
            
            # 如果生成失败，不阻止练习继续，只是不提供完整音阶音频
            if not scale_audio_file:
                print(f"⚠️ 音阶音频生成失败，但继续提供练习功能（仅提供根音和题目音频）")
                # 不返回错误，让练习可以继续进行
            
            # 准备选项（音阶内的所有音级）
            options = degrees.copy()
            random.shuffle(options)
            
            # 构建音阶名称显示
            range_text = "（两个八度）" if octave_range == 2 else "（一个八度）"
            scale_name = f"{key} {scale_info['name']}{range_text}"
            
            
            try:
                # 确保 root_audio_file 不为空
                if not root_audio_file:
                    print(f"⚠️ 警告：root_audio_file 为空，使用默认值")
                    root_audio_file = f"samples/piano/{root_note_openear}.mp3"
                
                print(f"✅ 返回音阶练习题目:")
                print(f"   root_audio_file: {root_audio_file}")
                print(f"   scale_audio_file: {scale_audio_file}")
                print(f"   question_audio_file: {question_audio_file}")
                
                return jsonify({
                    'status': 'ok',
                    'audio_file': question_audio_file,  # 题目音频（单个音符）
                    'root_audio_file': root_audio_file,  # 根音音频
                    'scale_audio_file': scale_audio_file,  # 完整音阶音频文件（已拼接好的8个音符）
                    'options': options,
                    'correct_answer': correct_degree,
                    'correct_value': correct_degree,
                    'sub_item': correct_degree,  # 细分项：音级（如"1", "2", "b3"等）
                    'scale_name': scale_name,
                    'is_authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False,
                })
            except Exception as e:
                print(f"❌ 返回JSON时出错: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'status': 'error',
                    'msg': f'生成响应时出错: {str(e)}'
                }), 500
        
        elif exercise_type == 'chord_quality':
            # 获取前端传来的参数
            key = request.args.get('key', 'C')
            included_roman_numerals = request.args.get('roman_numerals', 'I,ii,iii,IV,V,vi').split(',')
            
            if key not in KEYS:
                return jsonify({'status': 'error', 'msg': '无效的调性'})
            
            # 过滤有效的罗马数字
            valid_roman_numerals = [rn for rn in included_roman_numerals if rn in ROMAN_NUMERAL_CHORDS]
            if not valid_roman_numerals:
                valid_roman_numerals = ['I', 'ii', 'iii', 'IV', 'V', 'vi']
            
            # 随机选择一个罗马数字和弦
            roman_numeral = random.choice(valid_roman_numerals)
            chord_info = ROMAN_NUMERAL_CHORDS[roman_numeral]
            chord_type = chord_info['chord_type']
            scale_degree = chord_info['scale_degree']
            
            # 计算根音（在指定调性下）
            key_idx = KEYS.index(key)
            root_idx = (key_idx + scale_degree) % 12
            root_note_letter = note_letters[root_idx]
            
            # 选择八度（使用中间八度）
            octave = 4
            root_note = f"{root_note_letter}{octave}"
            
            # 获取和弦类型信息
            chord_pattern = CHORD_TYPES[chord_type]['pattern']
            
            # 计算和弦中的所有音符
            chord_notes = []
            for semitone_offset in chord_pattern:
                note_idx_in_octave = (root_idx + semitone_offset) % 12
                note_letter = note_letters[note_idx_in_octave]
                # 计算实际八度（考虑跨八度的情况）
                actual_octave = octave + (root_idx + semitone_offset) // 12
                note_name = f"{note_letter}{actual_octave}"
                chord_notes.append(note_name)
            
            # 转换音符名称格式（用于音源文件）
            def convert_note_name(note_name):
                if '#' in note_name:
                    parts = note_name.split('#')
                    if len(parts) == 2:
                        note_letter, octave = parts
                        return f"{note_letter}s{octave}"
                return note_name
            
            # 检查音源文件是否存在
            piano_samples_dir = os.path.join(basedir, 'static', 'audio', 'samples', 'piano')
            chord_audio_files = []
            for note in chord_notes:
                note_openear = convert_note_name(note)
                note_file = os.path.join(piano_samples_dir, f"{note_openear}.mp3")
                if os.path.exists(note_file):
                    chord_audio_files.append(f"samples/piano/{note_openear}.mp3")
                else:
                    print(f"⚠️ 和弦音符文件不存在: {note} -> {note_openear} -> {note_file}")
            
            if not chord_audio_files:
                return jsonify({'status': 'error', 'msg': '无法构建和弦音频文件列表'})
            
            # 生成根音音频文件路径（用于参考）- 使用4秒版本
            root_note_openear = convert_note_name(root_note)
            root_audio_file = generate_root_audio_4sec(key, octave, root_note_openear, piano_samples_dir)
            if not root_audio_file:
                # 如果无法生成4秒版本，回退到原始文件
                root_audio_file_path = os.path.join(piano_samples_dir, f"{root_note_openear}.mp3")
                if os.path.exists(root_audio_file_path):
                    root_audio_file = f"samples/piano/{root_note_openear}.mp3"
                    print(f"⚠️ 无法生成缩短版根音音频，使用原始文件: {root_note_openear}.mp3")
                else:
                    print(f"⚠️ 根音文件不存在: {root_note} -> {root_note_openear} -> {root_audio_file_path}")
            
            # 准备选项（从允许的和弦类型中选择）
            all_chord_types = list(CHORD_TYPES.keys())
            # 默认包含：major, minor, diminished, dominant7th, major7th, minor7th
            default_included = ['major', 'minor', 'diminished', 'dominant7th', 'major7th', 'minor7th']
            included_types = request.args.get('chord_types', ','.join(default_included)).split(',')
            included_types = [ct for ct in included_types if ct in all_chord_types]
            if not included_types:
                included_types = default_included
            
            # 确保正确答案在选项中
            if chord_type not in included_types:
                included_types.append(chord_type)
            
            # 如果选项少于4个，从所有和弦类型中补充
            if len(included_types) <= 4:
                options = included_types.copy()
                while len(options) < 4 and len(options) < len(all_chord_types):
                    additional = [ct for ct in all_chord_types if ct not in options]
                    if additional:
                        options.append(random.choice(additional))
                    else:
                        break
                random.shuffle(options)
            else:
                # 随机选择3个错误答案+1个正确答案
                wrong_options = [ct for ct in included_types if ct != chord_type]
                if len(wrong_options) >= 3:
                    options = random.sample(wrong_options, 3) + [chord_type]
                else:
                    options = wrong_options + [chord_type]
                    while len(options) < 4 and len(options) < len(all_chord_types):
                        additional = [ct for ct in all_chord_types if ct not in options]
                        if additional:
                            options.append(random.choice(additional))
                        else:
                            break
                random.shuffle(options)
            
            
            try:
                return jsonify({
                    'status': 'ok',
                    'chord_audio_files': chord_audio_files,  # 和弦音频文件列表（用于前端同时播放）
                    'root_audio_file': root_audio_file,  # 根音音频文件（用于参考）
                    'chord_notes': chord_notes,  # 和弦音符列表（用于调试）
                    'root_note': root_note,  # 根音（用于显示）
                    'roman_numeral': roman_numeral,  # 罗马数字（用于显示）
                    'key': key,  # 调性（用于显示）
                    'options': [CHORD_TYPES[opt]['cn'] for opt in options],  # 选项（中文）
                    'option_values': options,  # 选项值（英文）
                    'correct_answer': CHORD_TYPES[chord_type]['cn'],  # 正确答案（中文）
                    'correct_value': chord_type,  # 正确答案值（英文）
                    'sub_item': chord_type,  # 细分项：和弦类型（如"major", "minor"等）
                    'is_authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False,
                })
            except Exception as e:
                print(f"❌ 返回JSON时出错: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'status': 'error',
                    'msg': f'生成响应时出错: {str(e)}'
                }), 500
        
        else:
            return jsonify({'status': 'error', 'message': '该练习类型暂未实现'})
    except Exception as e:
        print(f"❌ 生成题目时出错: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'msg': f'服务器错误: {str(e)}'
        }), 500

@app.route('/api/start_session', methods=['POST'])
def start_session():
    """开始练习会话"""
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'msg': '请先登录'}), 401
    
    data = request.get_json()
    exercise_type = data.get('exercise_type', '')
    settings = data.get('settings', {})
    
    if not exercise_type:
        return jsonify({'status': 'error', 'msg': '缺少练习类型'}), 400
    
    # 创建新的练习会话
    session = PracticeSession(
        user_id=current_user.id,
        exercise_type=exercise_type,
        settings=json.dumps(settings) if settings else None
    )
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'status': 'ok',
        'session_id': session.id
    })

@app.route('/api/end_session', methods=['POST'])
def end_session():
    """结束练习会话"""
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'msg': '请先登录'}), 401
    
    data = request.get_json()
    session_id = data.get('session_id')
    duration = data.get('duration', 0)  # 秒
    total_questions = data.get('total_questions', 0)
    correct_answers = data.get('correct_answers', 0)
    
    if not session_id:
        return jsonify({'status': 'error', 'msg': '缺少会话ID'}), 400
    
    # 更新会话信息
    session = PracticeSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first()
    
    if not session:
        return jsonify({'status': 'error', 'msg': '会话不存在'}), 404
    
    session.end_time = datetime.utcnow()
    session.duration = duration
    session.total_questions = total_questions
    session.correct_answers = correct_answers
    db.session.commit()
    
    return jsonify({'status': 'ok'})

@app.route('/api/statistics', methods=['GET'])
@login_required
def get_statistics():
    """获取用户统计数据"""
    try:
        # 1. 用户总练习时长和题目总数
        all_sessions = PracticeSession.query.filter_by(user_id=current_user.id).all()
        total_duration = sum((s.duration or 0) for s in all_sessions)  # 秒
        total_questions = sum((s.total_questions or 0) for s in all_sessions)
        
        # 2. 各练习卡片的统计数据
        exercise_stats = {}
        for exercise_type in EXERCISE_TYPES.keys():
            sessions = PracticeSession.query.filter_by(
                user_id=current_user.id,
                exercise_type=exercise_type
            ).all()
            
            exercise_duration = sum((s.duration or 0) for s in sessions)
            exercise_questions = sum((s.total_questions or 0) for s in sessions)
            exercise_correct = sum((s.correct_answers or 0) for s in sessions)
            exercise_accuracy = (exercise_correct / exercise_questions * 100) if exercise_questions > 0 else 0
            
            # 3. 各练习卡片里细分项的统计数据
            sub_item_stats = {}
            if exercise_type == 'interval':
                # 查询该练习类型的所有题目
                session_ids = [s.id for s in sessions]
                if session_ids:
                    questions = Question.query.filter(
                        Question.session_id.in_(session_ids),
                        Question.exercise_type == exercise_type
                    ).all()
                    
                    # 按细分项统计
                    for question in questions:
                        sub_item = question.sub_item or ''
                        if sub_item:
                            if sub_item not in sub_item_stats:
                                sub_item_stats[sub_item] = {
                                    'duration': 0,
                                    'total_questions': 0,
                                    'correct_answers': 0
                                }
                            # 获取该题目的答案
                            answer = UserAnswer.query.filter_by(
                                question_id=question.id,
                                user_id=current_user.id
                            ).first()
                            if answer:
                                sub_item_stats[sub_item]['total_questions'] += 1
                                if answer.is_correct:
                                    sub_item_stats[sub_item]['correct_answers'] += 1
                                # 使用响应时间累加作为时长估算
                                if answer.response_time:
                                    sub_item_stats[sub_item]['duration'] += int(answer.response_time)
                    
                    # 计算细分项的正确率
                    for sub_item, stats in sub_item_stats.items():
                        stats['accuracy'] = (stats['correct_answers'] / stats['total_questions'] * 100) if stats['total_questions'] > 0 else 0
            elif exercise_type == 'scale_degree':
                # 音阶练习的细分项是音级（如"1", "2", "b3"等）
                session_ids = [s.id for s in sessions]
                if session_ids:
                    questions = Question.query.filter(
                        Question.session_id.in_(session_ids),
                        Question.exercise_type == exercise_type
                    ).all()
                    
                    for question in questions:
                        sub_item = question.sub_item or question.correct_answer or ''
                        if sub_item:
                            if sub_item not in sub_item_stats:
                                sub_item_stats[sub_item] = {
                                    'duration': 0,
                                    'total_questions': 0,
                                    'correct_answers': 0
                                }
                            answer = UserAnswer.query.filter_by(
                                question_id=question.id,
                                user_id=current_user.id
                            ).first()
                            if answer:
                                sub_item_stats[sub_item]['total_questions'] += 1
                                if answer.is_correct:
                                    sub_item_stats[sub_item]['correct_answers'] += 1
                                if answer.response_time:
                                    sub_item_stats[sub_item]['duration'] += int(answer.response_time)
                    
                    for sub_item, stats in sub_item_stats.items():
                        stats['accuracy'] = (stats['correct_answers'] / stats['total_questions'] * 100) if stats['total_questions'] > 0 else 0
            elif exercise_type == 'chord_quality':
                # 和弦练习的细分项是和弦类型（如"major", "minor"等）
                session_ids = [s.id for s in sessions]
                if session_ids:
                    questions = Question.query.filter(
                        Question.session_id.in_(session_ids),
                        Question.exercise_type == exercise_type
                    ).all()
                    
                    for question in questions:
                        sub_item = question.sub_item or question.correct_answer or ''
                        if sub_item:
                            if sub_item not in sub_item_stats:
                                sub_item_stats[sub_item] = {
                                    'duration': 0,
                                    'total_questions': 0,
                                    'correct_answers': 0
                                }
                            answer = UserAnswer.query.filter_by(
                                question_id=question.id,
                                user_id=current_user.id
                            ).first()
                            if answer:
                                sub_item_stats[sub_item]['total_questions'] += 1
                                if answer.is_correct:
                                    sub_item_stats[sub_item]['correct_answers'] += 1
                                if answer.response_time:
                                    sub_item_stats[sub_item]['duration'] += int(answer.response_time)
                    
                    for sub_item, stats in sub_item_stats.items():
                        stats['accuracy'] = (stats['correct_answers'] / stats['total_questions'] * 100) if stats['total_questions'] > 0 else 0
            
            # 计算练习次数
            practice_count = len(sessions)
            
            exercise_stats[exercise_type] = {
                'duration': exercise_duration,
                'total_questions': exercise_questions,
                'accuracy': round(exercise_accuracy, 2),
                'practice_count': practice_count,
                'sub_items': sub_item_stats
            }
        
        # 4. 用户每天活跃日期和时长
        daily_stats = {}
        for session in all_sessions:
            if session.start_time:
                date_key = session.start_time.date().isoformat()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        'date': date_key,
                        'duration': 0,
                        'sessions': 0
                    }
                daily_stats[date_key]['duration'] += (session.duration or 0)
                daily_stats[date_key]['sessions'] += 1
        
        # 转换为列表并按日期排序
        daily_stats_list = sorted(daily_stats.values(), key=lambda x: x['date'], reverse=True)
        
        # 5. 计算总正确数和练习天数
        total_correct = sum((s.correct_answers or 0) for s in all_sessions)
        practice_days = len(set(s.start_time.date() for s in all_sessions if s.start_time))
        
        # 6. 按周/月/年分组的时长分布
        weekly_stats = {}  # {year-week: duration}
        monthly_stats = {}  # {year-month: duration}
        yearly_stats = {}  # {year: duration}
        
        for session in all_sessions:
            if session.start_time and session.duration:
                dt = session.start_time
                duration = session.duration or 0
                
                # 按周统计（ISO周）
                year, week, _ = dt.isocalendar()
                week_key = f"{year}-W{week:02d}"
                if week_key not in weekly_stats:
                    weekly_stats[week_key] = 0
                weekly_stats[week_key] += duration
                
                # 按月统计
                month_key = f"{dt.year}-{dt.month:02d}"
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = 0
                monthly_stats[month_key] += duration
                
                # 按年统计
                year_key = str(dt.year)
                if year_key not in yearly_stats:
                    yearly_stats[year_key] = 0
                yearly_stats[year_key] += duration
        
        # 转换为列表并排序
        weekly_list = sorted([{'period': k, 'duration': v} for k, v in weekly_stats.items()], 
                            key=lambda x: x['period'], reverse=True)
        monthly_list = sorted([{'period': k, 'duration': v} for k, v in monthly_stats.items()], 
                             key=lambda x: x['period'], reverse=True)
        yearly_list = sorted([{'period': k, 'duration': v} for k, v in yearly_stats.items()], 
                            key=lambda x: x['period'], reverse=True)
        
        return jsonify({
            'status': 'ok',
            'total_duration': total_duration,  # 秒
            'total_questions': total_questions,
            'total_correct': total_correct,
            'practice_days': practice_days,
            'exercise_stats': exercise_stats,
            'daily_stats': daily_stats_list,
            'weekly_stats': weekly_list,
            'monthly_stats': monthly_list,
            'yearly_stats': yearly_list
        })
    except Exception as e:
        print(f"获取统计数据失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'msg': f'获取统计数据失败: {str(e)}'
        }), 500

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    """提交答案"""
    data = request.get_json()
    user_answer = data.get('answer', '')
    correct_value = data.get('correct_value', '')
    session_id = data.get('session_id')
    question_data = data.get('question_data', {})  # 题目完整数据
    response_time = data.get('response_time', 0)  # 响应时间（秒）
    sub_item = data.get('sub_item', '')  # 细分项，如"小二度"、"大二度"等
    
    is_correct = (user_answer == correct_value)
    
    # 如果用户已登录，保存到数据库
    if current_user.is_authenticated and session_id:
        try:
            # 创建题目记录
            question = Question(
                session_id=session_id,
                exercise_type=question_data.get('exercise_type', ''),
                question_data=json.dumps(question_data),
                correct_answer=correct_value,
                sub_item=sub_item
            )
            db.session.add(question)
            db.session.flush()  # 获取question.id
            
            # 创建用户答案记录
            user_answer_record = UserAnswer(
                user_id=current_user.id,
                question_id=question.id,
                user_answer=user_answer,
                is_correct=is_correct,
                response_time=response_time
            )
            db.session.add(user_answer_record)
            db.session.commit()
        except Exception as e:
            print(f"保存答案失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
    
    # 获取用户答案的中文名称
    user_answer_cn = user_answer
    for interval in INTERVALS.values():
        if interval['name'] == user_answer:
            user_answer_cn = interval['cn']
            break
    
    # 获取正确答案的中文名称
    correct_answer_cn = next((interval['cn'] for interval in INTERVALS.values() if interval['name'] == correct_value), correct_value)
    # 如果是音阶练习，直接使用correct_value
    if not correct_answer_cn or correct_answer_cn == correct_value:
        correct_answer_cn = correct_value
    
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

@app.route('/statistics')
@login_required
def statistics():
    """统计页面"""
    return render_template('statistics.html', 
                         exercise_types=EXERCISE_TYPES,
                         current_user=current_user)

@app.route('/logs')
@login_required
def view_logs():
    """查看服务器日志（需要登录）"""
    try:
        # 尝试读取日志文件
        log_file = os.path.join(basedir, '..', 'logs', 'app.log')
        if not os.path.exists(log_file):
            # 尝试其他可能的日志位置
            log_file = os.path.join(basedir, 'logs', 'app.log')
            if not os.path.exists(log_file):
                # 如果没有日志文件，返回最近的print输出
                return render_template('logs.html', 
                                     logs="暂无日志文件。日志会显示在服务器控制台。\n\n提示：如果使用 gunicorn，日志通常在 logs/app.log",
                                     error="未找到日志文件")
        
        # 读取最后1000行日志
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            # 取最后1000行
            recent_logs = ''.join(lines[-1000:]) if len(lines) > 1000 else ''.join(lines)
        
        return render_template('logs.html', logs=recent_logs, error=None)
    except Exception as e:
        return render_template('logs.html', 
                             logs=f"读取日志时出错: {str(e)}", 
                             error=str(e))

@app.route('/api/logs/recent')
@login_required
def get_recent_logs():
    """获取最近的日志（API，用于实时刷新）"""
    try:
        log_file = os.path.join(basedir, '..', 'logs', 'app.log')
        if not os.path.exists(log_file):
            log_file = os.path.join(basedir, 'logs', 'app.log')
            if not os.path.exists(log_file):
                return jsonify({'status': 'error', 'msg': '未找到日志文件'})
        
        # 读取最后200行
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            recent_logs = ''.join(lines[-200:]) if len(lines) > 200 else ''.join(lines)
        
        return jsonify({'status': 'ok', 'logs': recent_logs})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)})

if __name__ == '__main__':
    # 开发环境：允许局域网访问
    # 访问地址：http://你的IP地址:5001
    app.run(host='0.0.0.0', port=5001, debug=True)

