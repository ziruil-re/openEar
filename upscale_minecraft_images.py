#!/usr/bin/env python3
"""
将minecrafts目录下所有PNG图片放大到160x160
使用NEAREST方法保持像素风格，然后删除原图
"""
import os
from PIL import Image
import shutil

BASE_DIR = "/Users/liuzirui/Desktop/openEar/openEar/static/images/minecrafts"
TARGET_SIZE = (160, 160)  # 目标尺寸

def get_target_size():
    """从Apple_JE3_BE3.png获取目标尺寸"""
    reference_file = os.path.join(BASE_DIR, "Apple_JE3_BE3.png")
    if os.path.exists(reference_file):
        img = Image.open(reference_file)
        return img.size
    return TARGET_SIZE

def upscale_image(input_path, output_path, target_size):
    """将图片放大到目标尺寸（使用NEAREST保持像素风格）"""
    try:
        img = Image.open(input_path)
        
        # 如果已经是目标尺寸，跳过
        if img.size == target_size:
            return True
        
        # 使用NEAREST方法放大（像素完美）
        upscaled = img.resize(target_size, Image.NEAREST)
        upscaled.save(output_path, 'PNG')
        return True
    except Exception as e:
        print(f"  ✗ 处理失败: {e}")
        return False

def process_directory():
    """处理minecrafts目录下所有PNG文件"""
    print("=" * 60)
    print("放大Minecraft图片到160x160")
    print("=" * 60)
    
    # 获取目标尺寸
    target_size = get_target_size()
    print(f"\n目标尺寸: {target_size[0]}x{target_size[1]}")
    
    # 查找所有PNG文件
    print(f"\n1. 查找所有PNG文件...")
    png_files = []
    
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.lower().endswith('.png'):
                file_path = os.path.join(root, file)
                png_files.append(file_path)
    
    print(f"✓ 找到 {len(png_files)} 个PNG文件")
    
    if len(png_files) == 0:
        print("未找到PNG文件")
        return
    
    # 处理每个文件
    print(f"\n2. 开始处理图片...")
    processed = 0
    skipped = 0
    failed = 0
    
    for idx, file_path in enumerate(png_files, 1):
        filename = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, BASE_DIR)
        
        print(f"[{idx}/{len(png_files)}] {rel_path}")
        
        # 检查当前尺寸
        try:
            img = Image.open(file_path)
            current_size = img.size
            
            # 如果已经是目标尺寸，跳过
            if current_size == target_size:
                print(f"  ⊙ 已是目标尺寸，跳过")
                skipped += 1
                continue
            
            print(f"  {current_size[0]}x{current_size[1]} -> {target_size[0]}x{target_size[1]}")
            
            # 创建临时文件名
            temp_path = file_path + ".tmp"
            
            # 放大图片
            if upscale_image(file_path, temp_path, target_size):
                # 删除原图
                os.remove(file_path)
                # 重命名临时文件
                os.rename(temp_path, file_path)
                processed += 1
                print(f"  ✓ 完成")
            else:
                failed += 1
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            failed += 1
    
    # 总结
    print("\n" + "=" * 60)
    print("完成！")
    print(f"总计: {len(png_files)} 个文件")
    print(f"已处理: {processed} 个")
    print(f"已跳过: {skipped} 个（已是目标尺寸）")
    print(f"失败: {failed} 个")
    print("=" * 60)
    print(f"\n所有图片已放大到 {target_size[0]}x{target_size[1]}，原图已删除")

if __name__ == '__main__':
    try:
        process_directory()
    except ImportError:
        print("需要安装Pillow:")
        print("  pip install Pillow")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

