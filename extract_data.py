#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从转录文件中提取Tips和歌曲信息
"""

import os
import json
import re
from pathlib import Path

def extract_interval_songs():
    """从转录文件中提取音程相关的歌曲"""
    transcriptions_dir = Path(__file__).parent.parent / "transcriptions" / "audio"
    
    songs_by_interval = {}
    
    # 从转录文件中提取歌曲信息
    interval_files = {
        'major_second': ['03-major-minor-2nd-intervals-zh.md', '04-major-minor-2nd-intervals-zh.md'],
        'minor_second': ['03-major-minor-2nd-intervals-zh.md', '04-major-minor-2nd-intervals-zh.md'],
        'major_third': ['05-major-minor-3rd-intervals-zh.md', '06-major-minor-3rd-intervals-zh.md'],
        'minor_third': ['05-major-minor-3rd-intervals-zh.md', '06-major-minor-3rd-intervals-zh.md'],
        'perfect_fourth': ['07-perfect-4ths-augmented-4ths-perfect-5th-intervals-zh.md'],
        'perfect_fifth': ['07-perfect-4ths-augmented-4ths-perfect-5th-intervals-zh.md'],
    }
    
    # 已知的歌曲参考（从转录内容中提取）
    known_songs = {
        'major_second': [
            {'name': '待补充', 'url': '#'}
        ],
        'minor_second': [
            {'name': '待补充', 'url': '#'}
        ],
        'major_third': [
            {'name': 'Summertime (George Gershwin)', 'url': 'https://music.163.com/#/song?id=待补充'},
            {'name': 'Georgia on my mind', 'url': 'https://music.163.com/#/song?id=待补充'}
        ],
        'minor_third': [
            {'name': 'Georgia on my mind', 'url': 'https://music.163.com/#/song?id=待补充'}
        ],
        'perfect_fourth': [
            {'name': 'Here comes the bride', 'url': 'https://music.163.com/#/song?id=待补充'}
        ],
        'perfect_fifth': [
            {'name': 'Twinkle, twinkle little star', 'url': 'https://music.163.com/#/song?id=待补充'}
        ]
    }
    
    return known_songs

def extract_tips():
    """从转录文件中提取Tips和说明"""
    transcriptions_dir = Path(__file__).parent.parent / "transcriptions" / "audio"
    
    tips = {
        'interval': {
            'explanation': '''
            <p>音程辨认是听力训练的基础。在这个练习中，您将听到两个音符依次播放，需要识别它们之间的音程关系。</p>
            <p><strong>练习方法：</strong></p>
            <ul>
                <li>仔细聆听两个音符的方向（上行或下行）和距离</li>
                <li>使用参考歌曲帮助记忆音程特征</li>
                <li>反复练习，直到能够快速识别</li>
            </ul>
            ''',
            'tips': [
                '大二度和小二度在爵士乐中是最常用的音程',
                '使用第20页的音程表作为参考框架',
                '当听到两个音符时，想想参考歌曲的前两个音符',
                '如果参考歌曲匹配，那就是答案',
                '音程识别是识别和弦、音阶、模式的关键'
            ]
        },
        'scale_degree': {
            'explanation': '''
            <p>音阶内音辨认练习帮助您识别音阶中的特定音级。这是功能性和声训练的基础。</p>
            ''',
            'tips': []
        },
        'chord_quality': {
            'explanation': '''
            <p>和弦性质辨认是爵士乐训练的核心。您需要识别和弦的类型、转位和性质。</p>
            ''',
            'tips': []
        },
        'chord_progression': {
            'explanation': '''
            <p>和弦进行练习帮助您识别常见的和弦进行模式，如ii-V-I等。</p>
            ''',
            'tips': []
        },
        'melody': {
            'explanation': '''
            <p>旋律片段练习提升您的音乐性和实际应用能力。</p>
            ''',
            'tips': []
        }
    }
    
    # 从转录文件中读取更详细的内容
    interval_file = transcriptions_dir / "03-major-minor-2nd-intervals-zh.md"
    if interval_file.exists():
        content = interval_file.read_text(encoding='utf-8')
        # 提取关键信息
        if '耐心' in content:
            tips['interval']['tips'].append('要有耐心，不要灰心')
        if '多次' in content:
            tips['interval']['tips'].append('可能需要多次练习才能掌握')
    
    return tips

def main():
    """主函数：提取数据并保存为JSON"""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 提取Tips
    tips = extract_tips()
    tips_file = data_dir / "tips.json"
    with open(tips_file, 'w', encoding='utf-8') as f:
        json.dump(tips, f, ensure_ascii=False, indent=2)
    print(f"✓ Tips已保存到: {tips_file}")
    
    # 提取歌曲
    songs = extract_interval_songs()
    songs_data = {
        'interval': songs
    }
    songs_file = data_dir / "songs.json"
    with open(songs_file, 'w', encoding='utf-8') as f:
        json.dump(songs_data, f, ensure_ascii=False, indent=2)
    print(f"✓ 歌曲数据已保存到: {songs_file}")
    
    print("\n数据提取完成！")

if __name__ == "__main__":
    main()

