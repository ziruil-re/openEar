#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量重新生成所有音程音频文件（带音量归一化）"""

import os
import sys
from pydub import AudioSegment

# 添加项目路径
basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, basedir)

def convert_note_name(note_name):
    """将音符名称转换为格式"""
    if '#' in note_name:
        parts = note_name.split('#')
        if len(parts) == 2:
            note_letter, octave = parts
            return f"{note_letter}s{octave}"
    return note_name

def regenerate_interval_audio(note1, note2, force=False):
    """重新生成音程音频文件（带音量归一化）"""
    try:
        note1_openear = convert_note_name(note1)
        note2_openear = convert_note_name(note2)
        
        # 检查音源文件是否存在
        piano_samples_dir = os.path.join(basedir, 'static', 'audio', 'samples', 'piano')
        note1_file = os.path.join(piano_samples_dir, f"{note1_openear}.mp3")
        note2_file = os.path.join(piano_samples_dir, f"{note2_openear}.mp3")
        
        if not os.path.exists(note1_file) or not os.path.exists(note2_file):
            return False, f"音源文件不存在: {note1} 或 {note2}"
        
        # 生成输出文件名
        safe_note1 = note1_openear.replace('#', 'sharp')
        safe_note2 = note2_openear.replace('#', 'sharp')
        interval_dir = os.path.join(basedir, 'static', 'audio', 'interval')
        os.makedirs(interval_dir, exist_ok=True)
        
        # 输出 MP3 文件
        output_filename = f"{safe_note1}_{safe_note2}_1sec.mp3"
        output_path = os.path.join(interval_dir, output_filename)
        
        # 检查旧文件（.wav 和 .mp3）
        wav_path = output_path.replace('.mp3', '.wav')
        old_wav_exists = os.path.exists(wav_path)
        old_mp3_exists = os.path.exists(output_path)
        
        if not force and old_mp3_exists:
            # 如果文件已存在且不强制重新生成，跳过
            return True, f"已存在，跳过: {output_filename}"
        
        # 加载两个音符文件
        audio1 = AudioSegment.from_mp3(note1_file)
        audio2 = AudioSegment.from_mp3(note2_file)
        
        # 每个音符取1秒（1000毫秒）
        audio1_1sec = audio1[:1000]
        audio2_1sec = audio2[:1000]
        
        # 对每个音符进行音量归一化（确保音量一致）
        audio1_1sec = audio1_1sec.normalize()
        audio2_1sec = audio2_1sec.normalize()
        
        # 拼接两个音符（无缝衔接）
        combined_audio = audio1_1sec + audio2_1sec
        
        # 对拼接后的音频再次归一化（确保整体音量一致）
        combined_audio = combined_audio.normalize()
        
        # 删除旧文件（如果存在）
        if old_wav_exists:
            os.remove(wav_path)
            print(f"  删除旧文件: {os.path.basename(wav_path)}")
        if old_mp3_exists:
            os.remove(output_path)
            print(f"  删除旧文件: {os.path.basename(output_path)}")
        
        # 导出为MP3
        combined_audio.export(output_path, format="mp3")
        
        return True, f"✅ 已生成: {output_filename} ({os.path.getsize(output_path) / 1024:.1f} KB)"
        
    except Exception as e:
        return False, f"❌ 生成失败: {e}"

def main():
    """主函数：批量重新生成所有音程音频"""
    print("🔄 开始批量重新生成所有音程音频文件（带音量归一化）...")
    print("=" * 60)
    
    # 音符名称列表
    NOTE_NAMES = []
    octaves = [2, 3, 4, 5, 6]
    note_letters = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    for octave in octaves:
        for note in note_letters:
            NOTE_NAMES.append(f"{note}{octave}")
    
    # 音程定义（半音数）
    INTERVALS = {
        1: 'minor_second', 2: 'major_second', 3: 'minor_third', 4: 'major_third',
        5: 'perfect_fourth', 6: 'tritone', 7: 'perfect_fifth', 8: 'minor_sixth',
        9: 'major_sixth', 10: 'minor_seventh', 11: 'major_seventh', 12: 'octave'
    }
    
    # 生成所有可能的音程组合
    total = 0
    success = 0
    failed = 0
    skipped = 0
    
    for note1_idx in range(len(NOTE_NAMES)):
        for semitones in INTERVALS.keys():
            # 上行音程
            note2_idx = note1_idx + semitones
            if 0 <= note2_idx < len(NOTE_NAMES):
                note1 = NOTE_NAMES[note1_idx]
                note2 = NOTE_NAMES[note2_idx]
                total += 1
                success_flag, message = regenerate_interval_audio(note1, note2, force=True)
                if success_flag:
                    if "跳过" in message:
                        skipped += 1
                    else:
                        success += 1
                        print(f"[{total}] {message}")
                else:
                    failed += 1
                    print(f"[{total}] {message}")
            
            # 下行音程
            note2_idx = note1_idx - semitones
            if 0 <= note2_idx < len(NOTE_NAMES) and semitones != 0:
                note1 = NOTE_NAMES[note1_idx]
                note2 = NOTE_NAMES[note2_idx]
                total += 1
                success_flag, message = regenerate_interval_audio(note1, note2, force=True)
                if success_flag:
                    if "跳过" in message:
                        skipped += 1
                    else:
                        success += 1
                        print(f"[{total}] {message}")
                else:
                    failed += 1
                    print(f"[{total}] {message}")
    
    print("=" * 60)
    print(f"📊 统计:")
    print(f"  总计: {total}")
    print(f"  成功: {success}")
    print(f"  跳过: {skipped}")
    print(f"  失败: {failed}")
    print("=" * 60)
    print("✅ 批量重新生成完成！")

if __name__ == '__main__':
    main()

