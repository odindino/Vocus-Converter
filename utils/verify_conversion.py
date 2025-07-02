#!/usr/bin/env python3
"""
轉換結果驗證腳本
檢查生成的檔案是否正確
"""

import os
from pathlib import Path
import re


def verify_conversion():
    """驗證轉換結果"""
    print("="*60)
    print("轉換結果驗證")
    print("="*60)
    
    # 檢查基本目錄結構
    print("\n1. 檢查目錄結構:")
    required_dirs = ["output/pdf", "output/md", "images", "article_html"]
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} (不存在)")
    
    # 檢查圖片目錄
    print("\n2. 檢查圖片目錄:")
    images_dir = Path("images")
    if images_dir.exists():
        for article_dir in images_dir.iterdir():
            if article_dir.is_dir():
                print(f"  ✓ {article_dir.name}")
                
                # 檢查圖片檔案
                image_files = list(article_dir.glob("image_*.{jpeg,jpg,png,gif}"))
                print(f"    - 圖片數量: {len(image_files)}")
                
                # 檢查image_urls.txt
                urls_file = article_dir / "image_urls.txt"
                if urls_file.exists():
                    print(f"    ✓ image_urls.txt")
                else:
                    print(f"    ✗ image_urls.txt (不存在)")
    
    # 檢查輸出檔案
    print("\n3. 檢查輸出檔案:")
    pdf_dir = Path("output/pdf")
    md_dir = Path("output/md")
    
    pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    md_files = list(md_dir.glob("*.md")) if md_dir.exists() else []
    
    print(f"  PDF檔案: {len(pdf_files)}")
    for pdf_file in pdf_files:
        size_mb = pdf_file.stat().st_size / (1024 * 1024)
        print(f"    ✓ {pdf_file.name} ({size_mb:.1f} MB)")
    
    print(f"  Markdown檔案: {len(md_files)}")
    for md_file in md_files:
        size_kb = md_file.stat().st_size / 1024
        print(f"    ✓ {md_file.name} ({size_kb:.1f} KB)")
    
    # 檢查HTML檔案管理
    print("\n4. 檢查HTML檔案管理:")
    html_dir = Path("article_html")
    if html_dir.exists():
        html_files = list(html_dir.glob("*.html"))
        print(f"  管理的HTML檔案: {len(html_files)}")
        for html_file in html_files:
            size_kb = html_file.stat().st_size / 1024
            print(f"    ✓ {html_file.name} ({size_kb:.1f} KB)")
    
    # 檢查Markdown中的圖片路徑
    print("\n5. 檢查Markdown圖片路徑:")
    for md_file in md_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 找到所有圖片引用
        image_refs = re.findall(r'!\[.*?\]\((.*?)\)', content)
        local_image_refs = [ref for ref in image_refs if ref.startswith('../../images/')]
        
        print(f"  {md_file.name}:")
        print(f"    - 總圖片引用: {len(image_refs)}")
        print(f"    - 本地圖片引用: {len(local_image_refs)}")
        
        # 檢查本地圖片是否存在
        missing_images = []
        for ref in local_image_refs:
            # 移除 '../../' 前綴
            local_path = Path(ref[6:])
            if not local_path.exists():
                missing_images.append(ref)
        
        if missing_images:
            print(f"    ✗ 缺失圖片: {len(missing_images)}")
            for missing in missing_images:
                print(f"      - {missing}")
        else:
            print(f"    ✓ 所有本地圖片都存在")
    
    # 檢查日期時間格式
    print("\n6. 檢查日期時間格式:")
    for article_dir in images_dir.iterdir() if images_dir.exists() else []:
        if article_dir.is_dir() and article_dir.name.startswith('article_'):
            date_part = article_dir.name.replace('article_', '')
            if re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}', date_part):
                print(f"    ✓ {article_dir.name} (正確的日期時間格式)")
            else:
                print(f"    ✗ {article_dir.name} (錯誤的日期時間格式)")
    
    print("\n" + "="*60)
    print("驗證完成")
    print("="*60)


def show_file_tree():
    """顯示文件樹結構"""
    print("\n文件樹結構:")
    print("-" * 40)
    
    def print_tree(path, prefix="", is_last=True):
        if path.is_dir():
            print(f"{prefix}{'└── ' if is_last else '├── '}{path.name}/")
            children = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
            for i, child in enumerate(children):
                is_last_child = i == len(children) - 1
                extension = "    " if is_last else "│   "
                print_tree(child, prefix + extension, is_last_child)
        else:
            size = path.stat().st_size
            if size > 1024 * 1024:
                size_str = f"({size / (1024 * 1024):.1f} MB)"
            elif size > 1024:
                size_str = f"({size / 1024:.1f} KB)"
            else:
                size_str = f"({size} bytes)"
            print(f"{prefix}{'└── ' if is_last else '├── '}{path.name} {size_str}")
    
    # 顯示主要目錄
    for dir_name in ["output", "images", "article_html"]:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print_tree(dir_path)


if __name__ == "__main__":
    verify_conversion()
    show_file_tree()