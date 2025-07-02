#!/usr/bin/env python3
"""
轉換器測試腳本
驗證所有功能是否正常運作
"""

import os
import sys
from pathlib import Path
import subprocess


def run_command(cmd, description):
    """執行命令並顯示結果"""
    print(f"\n{'='*50}")
    print(f"測試: {description}")
    print(f"命令: {cmd}")
    print('='*50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"返回碼: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"執行錯誤: {str(e)}")
        return False


def check_files(file_paths):
    """檢查檔案是否存在"""
    for file_path in file_paths:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            print(f"✓ {file_path} ({size:,} bytes)")
        else:
            print(f"✗ {file_path} (不存在)")


def main():
    """主測試函數"""
    print("Vocus文章轉換器 - 功能測試")
    
    # 檢查是否有測試檔案
    test_file = "AI 資本支出巨浪來襲，誰是這波行情的核心受益者？.html"
    if not Path(test_file).exists():
        print(f"錯誤：找不到測試檔案 {test_file}")
        sys.exit(1)
    
    # 清理舊的輸出
    print("\n清理舊的輸出檔案...")
    subprocess.run("rm -rf output images", shell=True)
    
    # 測試1：基本轉換功能
    success1 = run_command(
        f'python vocus_converter.py "{test_file}"',
        "基本轉換功能（包含圖片下載）"
    )
    
    # 檢查輸出檔案
    print("\n檢查輸出檔案:")
    expected_files = [
        "output/md/AI 資本支出巨浪來襲，誰是這波行情的核心受益者？.md",
        "output/pdf/AI 資本支出巨浪來襲，誰是這波行情的核心受益者？.pdf",
        "images/article_2025-06-30/image_1.jpeg",
        "images/article_2025-06-30/image_2.png",
        "images/article_2025-06-30/image_3.png",
        "images/article_2025-06-30/image_4.png"
    ]
    check_files(expected_files)
    
    # 測試2：圖片URL提取
    success2 = run_command(
        f'python image_helper.py extract "{test_file}"',
        "圖片URL提取功能"
    )
    
    # 檢查URL檔案
    print("\n檢查URL檔案:")
    check_files(["image_urls.txt"])
    
    # 測試3：批次轉換（如果有多個HTML檔案）
    html_files = list(Path(".").glob("*.html"))
    if len(html_files) > 1:
        success3 = run_command(
            "python batch_convert.py",
            "批次轉換功能"
        )
    else:
        print("\n跳過批次轉換測試（只有一個HTML檔案）")
        success3 = True
    
    # 測試4：進階圖片下載器
    subprocess.run("rm -rf images", shell=True)  # 清理圖片
    success4 = run_command(
        f'python advanced_image_downloader.py "{test_file}"',
        "進階圖片下載器"
    )
    
    # 檢查進階下載器的圖片
    print("\n檢查進階下載器的圖片:")
    check_files([
        "images/article_2025-06-30/image_1.jpg",
        "images/article_2025-06-30/image_2.jpg",
        "images/article_2025-06-30/image_3.jpg",
        "images/article_2025-06-30/image_4.jpg"
    ])
    
    # 總結
    print("\n" + "="*50)
    print("測試總結")
    print("="*50)
    
    tests = [
        ("基本轉換功能", success1),
        ("圖片URL提取", success2),
        ("批次轉換功能", success3),
        ("進階圖片下載器", success4)
    ]
    
    for test_name, success in tests:
        status = "✓ 通過" if success else "✗ 失敗"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in tests)
    print(f"\n整體測試結果: {'✓ 全部通過' if all_passed else '✗ 有測試失敗'}")
    
    if all_passed:
        print("\n🎉 恭喜！所有功能都正常運作")
        print("您現在可以開始使用轉換器來處理Vocus文章了！")
    else:
        print("\n⚠️ 部分功能可能需要檢查")


if __name__ == "__main__":
    main()