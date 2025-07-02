#!/usr/bin/env python3
"""
批次轉換Vocus文章
可以處理目錄下的所有HTML檔案
"""

import os
import sys
import glob
from pathlib import Path
from vocus_converter import VocusArticleConverter


def batch_convert(input_pattern="*.html", output_dir="output", images_dir="images", 
                 skip_existing=False, force_overwrite=False, interactive=True):
    """批次轉換HTML檔案"""
    
    # 找到所有符合條件的HTML檔案
    html_files = glob.glob(input_pattern)
    
    if not html_files:
        print(f"找不到符合條件的HTML檔案: {input_pattern}")
        return
    
    print(f"找到 {len(html_files)} 個HTML檔案")
    print("="*50)
    
    # 先檢查哪些文章已經轉換過
    converted_files = []
    new_files = []
    
    print("檢查已轉換的文章...")
    for html_file in html_files:
        try:
            converter = VocusArticleConverter(
                input_file=html_file,
                output_dir=output_dir,
                images_dir=images_dir
            )
            already_converted, status = converter.check_already_converted()
            if already_converted:
                converted_files.append((html_file, status))
            else:
                new_files.append((html_file, status))
        except Exception as e:
            print(f"檢查檔案 {html_file} 時發生錯誤: {str(e)}")
            new_files.append((html_file, f"檢查失敗: {str(e)}"))
    
    # 顯示檢查結果
    if converted_files:
        print(f"\n已轉換的文章 ({len(converted_files)} 個):")
        for html_file, status in converted_files:
            print(f"  ✓ {html_file} - {status}")
    
    if new_files:
        print(f"\n未轉換的文章 ({len(new_files)} 個):")
        for html_file, status in new_files:
            print(f"  ○ {html_file} - {status}")
    
    # 決定處理策略
    files_to_process = []
    
    if not converted_files:
        # 沒有已轉換的文章，處理所有檔案
        files_to_process = [f[0] for f in new_files]
    elif force_overwrite:
        # 強制覆蓋模式，處理所有檔案
        files_to_process = html_files
        print(f"\n強制覆蓋模式：將重新轉換所有 {len(html_files)} 個文章")
    elif skip_existing:
        # 跳過已存在的檔案
        files_to_process = [f[0] for f in new_files]
        print(f"\n跳過已存在的檔案，將轉換 {len(files_to_process)} 個新文章")
    elif interactive and converted_files:
        # 互動模式，詢問用戶
        print(f"\n發現 {len(converted_files)} 個已轉換的文章。")
        while True:
            choice = input("選擇處理方式：\n"
                         "  [1] 只轉換新文章 (預設)\n"
                         "  [2] 重新轉換所有文章\n"
                         "  [3] 取消操作\n"
                         "請選擇 (1-3): ").strip()
            
            if choice in ['', '1']:
                files_to_process = [f[0] for f in new_files]
                print(f"將轉換 {len(files_to_process)} 個新文章")
                break
            elif choice == '2':
                files_to_process = html_files
                print(f"將重新轉換所有 {len(html_files)} 個文章")
                break
            elif choice == '3':
                print("操作已取消")
                return
            else:
                print("無效的選擇，請重新輸入")
    else:
        # 非互動模式且有已轉換的檔案，預設只處理新檔案
        files_to_process = [f[0] for f in new_files]
    
    if not files_to_process:
        print("\n沒有需要處理的檔案")
        return
    
    # 開始批次轉換
    print(f"\n開始批次轉換 {len(files_to_process)} 個檔案...")
    print("="*50)
    
    success_count = 0
    fail_count = 0
    skip_count = len(html_files) - len(files_to_process)
    
    for idx, html_file in enumerate(files_to_process, 1):
        print(f"\n[{idx}/{len(files_to_process)}] 處理檔案: {html_file}")
        print("-"*50)
        
        try:
            converter = VocusArticleConverter(
                input_file=html_file,
                output_dir=output_dir,
                images_dir=images_dir
            )
            converter.convert()
            success_count += 1
        except Exception as e:
            print(f"錯誤：處理檔案 {html_file} 時發生錯誤: {str(e)}")
            fail_count += 1
    
    print("\n" + "="*50)
    print("批次轉換完成！")
    print(f"成功: {success_count} 個檔案")
    print(f"失敗: {fail_count} 個檔案")
    if skip_count > 0:
        print(f"跳過: {skip_count} 個檔案")
    print("="*50)


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批次轉換Vocus HTML文章')
    parser.add_argument(
        'pattern',
        nargs='?',
        default='*.html',
        help='檔案匹配模式 (預設: *.html)'
    )
    parser.add_argument('--output-dir', '-o', default='output', help='輸出目錄')
    parser.add_argument('--images-dir', '-i', default='images', help='圖片目錄')
    
    # 新增的重複處理選項
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--skip-existing', '-s',
        action='store_true',
        help='自動跳過已轉換的文章'
    )
    group.add_argument(
        '--force-overwrite', '-f',
        action='store_true',
        help='強制重新轉換所有文章（包括已存在的）'
    )
    
    parser.add_argument(
        '--non-interactive', '-n',
        action='store_true',
        help='非互動模式，不詢問用戶選擇'
    )
    
    args = parser.parse_args()
    
    batch_convert(
        input_pattern=args.pattern,
        output_dir=args.output_dir,
        images_dir=args.images_dir,
        skip_existing=args.skip_existing,
        force_overwrite=args.force_overwrite,
        interactive=not args.non_interactive
    )


if __name__ == "__main__":
    main()