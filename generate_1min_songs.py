#!/usr/bin/env python3
"""
批量生成所有歌曲的1分钟版本
运行此脚本可以预处理所有音频文件，生成缩短版本以加快加载速度
"""

import os
import sys

# 添加项目路径
basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, basedir)

from app import generate_song_audio_1min

def batch_generate_1min_songs():
    """批量生成所有歌曲的1分钟版本"""
    songs_dir = os.path.join(basedir, 'static', 'audio', 'songs')
    
    if not os.path.exists(songs_dir):
        print(f"❌ 歌曲目录不存在: {songs_dir}")
        return
    
    # 获取所有MP3文件
    mp3_files = [f for f in os.listdir(songs_dir) if f.endswith('.mp3')]
    
    if not mp3_files:
        print(f"⚠️ 未找到MP3文件在目录: {songs_dir}")
        return
    
    print(f"📁 找到 {len(mp3_files)} 个音频文件")
    print("🚀 开始生成1分钟版本...\n")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, filename in enumerate(mp3_files, 1):
        audio_path = f"songs/{filename}"
        print(f"[{i}/{len(mp3_files)}] 处理: {filename}")
        
        result = generate_song_audio_1min(audio_path)
        
        if result is None:
            error_count += 1
            print(f"  ❌ 生成失败")
        elif result == audio_path:
            skip_count += 1
            print(f"  ⏭️  已存在或文件已小于1分钟")
        else:
            success_count += 1
            print(f"  ✅ 成功生成: {result}")
    
    print(f"\n📊 处理完成:")
    print(f"  ✅ 成功: {success_count}")
    print(f"  ⏭️  跳过: {skip_count}")
    print(f"  ❌ 失败: {error_count}")
    print(f"  📁 总计: {len(mp3_files)}")

if __name__ == '__main__':
    try:
        batch_generate_1min_songs()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

