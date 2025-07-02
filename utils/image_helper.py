#!/usr/bin/env python3
"""
圖片輔助工具
幫助處理Vocus文章的圖片
"""

import os
import shutil
from pathlib import Path
from urllib.parse import urlparse, unquote
import re


def copy_downloaded_images(html_file, source_folder, target_base="images"):
    """
    將已下載的圖片複製到正確的目錄結構
    
    參數:
    - html_file: HTML檔案路徑，用於提取發布日期
    - source_folder: 包含已下載圖片的資料夾
    - target_base: 目標基礎目錄
    """
    from bs4 import BeautifulSoup
    import json
    from datetime import datetime
    
    # 讀取HTML提取發布日期
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取發布日期（包含時間）
    publish_date = None
    pubdate_meta = soup.find('meta', {'name': 'pubdate'})
    if pubdate_meta:
        pubdate_str = pubdate_meta.get('content', '')
        try:
            dt = datetime.fromisoformat(pubdate_str.replace('Z', '+00:00'))
            publish_date = dt.strftime('%Y-%m-%d_%H-%M')  # 包含時間避免衝突
        except:
            pass
    
    if not publish_date:
        publish_date = datetime.now().strftime('%Y-%m-%d_%H-%M')
    
    # 建立目標目錄
    target_dir = Path(target_base) / f"article_{publish_date}"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 複製圖片
    source_path = Path(source_folder)
    if not source_path.exists():
        print(f"錯誤：來源資料夾不存在: {source_folder}")
        return
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    copied = 0
    
    for file_path in source_path.iterdir():
        if file_path.suffix.lower() in image_extensions:
            target_path = target_dir / file_path.name
            shutil.copy2(file_path, target_path)
            print(f"複製: {file_path.name} → {target_path}")
            copied += 1
    
    print(f"\n完成！已複製 {copied} 個圖片到 {target_dir}")


def extract_image_urls(html_file, output_file=None):
    """
    從HTML檔案中提取所有圖片URL
    
    參數:
    - html_file: HTML檔案路徑
    - output_file: 輸出的URL列表檔案（如果為None，將輸出到對應的圖片資料夾）
    """
    from bs4 import BeautifulSoup
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取發布日期（包含時間）
    publish_date = None
    pubdate_meta = soup.find('meta', {'name': 'pubdate'})
    if pubdate_meta:
        pubdate_str = pubdate_meta.get('content', '')
        try:
            dt = datetime.fromisoformat(pubdate_str.replace('Z', '+00:00'))
            publish_date = dt.strftime('%Y-%m-%d_%H-%M')
        except:
            pass
    
    if not publish_date:
        publish_date = datetime.now().strftime('%Y-%m-%d_%H-%M')
    
    # 確定輸出檔案路徑
    if output_file is None:
        img_folder = Path("images") / f"article_{publish_date}"
        img_folder.mkdir(parents=True, exist_ok=True)
        output_file = img_folder / "image_urls.txt"
    
    # 提取所有圖片URL
    urls = []
    img_tags = soup.find_all('img')
    
    for img in img_tags:
        img_url = img.get('data-src') or img.get('src')
        if img_url:
            # 如果是resize URL，也提取原始URL
            if 'resize-image.vocus.cc' in img_url:
                urls.append(f"Resize URL: {img_url}")
                match = re.search(r'url=([^&]+)', img_url)
                if match:
                    original_url = unquote(match.group(1))
                    urls.append(f"Original URL: {original_url}")
            else:
                urls.append(img_url)
            
            urls.append("")  # 空行分隔
    
    # 寫入檔案
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"圖片URL列表 - 來自: {html_file}\n")
        f.write("="*50 + "\n\n")
        for url in urls:
            f.write(url + "\n")
    
    print(f"已提取 {len(img_tags)} 個圖片URL")
    print(f"URL列表已儲存至: {output_file}")


def rename_images_by_order(folder, prefix="image"):
    """
    按順序重新命名資料夾中的圖片
    
    參數:
    - folder: 圖片資料夾路徑
    - prefix: 檔名前綴
    """
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"錯誤：資料夾不存在: {folder}")
        return
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    image_files = []
    
    # 收集所有圖片檔案
    for file_path in folder_path.iterdir():
        if file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)
    
    # 按檔名排序
    image_files.sort()
    
    # 重新命名
    for idx, file_path in enumerate(image_files, 1):
        new_name = f"{prefix}_{idx}{file_path.suffix}"
        new_path = file_path.parent / new_name
        
        if file_path != new_path:
            file_path.rename(new_path)
            print(f"重新命名: {file_path.name} → {new_name}")
    
    print(f"\n完成！已重新命名 {len(image_files)} 個圖片")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Vocus文章圖片輔助工具')
    subparsers = parser.add_subparsers(dest='command', help='可用的命令')
    
    # 複製圖片命令
    copy_parser = subparsers.add_parser('copy', help='複製已下載的圖片到正確目錄')
    copy_parser.add_argument('html_file', help='HTML檔案路徑')
    copy_parser.add_argument('source_folder', help='包含圖片的來源資料夾')
    copy_parser.add_argument('--target', '-t', default='images', help='目標基礎目錄')
    
    # 提取URL命令
    extract_parser = subparsers.add_parser('extract', help='提取HTML中的圖片URL')
    extract_parser.add_argument('html_file', help='HTML檔案路徑')
    extract_parser.add_argument('--output', '-o', default='image_urls.txt', help='輸出檔案名')
    
    # 重新命名命令
    rename_parser = subparsers.add_parser('rename', help='按順序重新命名圖片')
    rename_parser.add_argument('folder', help='圖片資料夾路徑')
    rename_parser.add_argument('--prefix', '-p', default='image', help='檔名前綴')
    
    args = parser.parse_args()
    
    if args.command == 'copy':
        copy_downloaded_images(args.html_file, args.source_folder, args.target)
    elif args.command == 'extract':
        extract_image_urls(args.html_file, args.output)
    elif args.command == 'rename':
        rename_images_by_order(args.folder, args.prefix)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()