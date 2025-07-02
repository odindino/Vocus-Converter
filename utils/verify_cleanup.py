#!/usr/bin/env python3
"""
驗證HTML清理結果
檢查是否已移除所有UI控制元素
"""

from pathlib import Path
from bs4 import BeautifulSoup
import re


def verify_html_cleanup():
    """驗證HTML清理結果"""
    print("🧹 HTML清理結果驗證")
    print("="*50)
    
    # 檢查Markdown內容
    md_path = Path("output/md/AI 資本支出巨浪來襲，誰是這波行情的核心受益者？.md")
    if md_path.exists():
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        print("📝 Markdown檔案檢查:")
        
        # 檢查是否還有縮放相關的元素
        zoom_patterns = [
            r'zoom.*control',
            r'data-rmiz',
            r'svg.*arrow',
            r'Expand image',
            r'zoomable'
        ]
        
        found_issues = []
        for pattern in zoom_patterns:
            matches = re.findall(pattern, md_content, re.IGNORECASE)
            if matches:
                found_issues.extend(matches)
        
        if found_issues:
            print("  ⚠️  仍發現以下可能的UI元素:")
            for issue in set(found_issues):
                print(f"    - {issue}")
        else:
            print("  ✅ 未發現縮放控制元素")
        
        # 檢查圖片引用
        image_refs = re.findall(r'!\[.*?\]\((.*?)\)', md_content)
        local_images = [ref for ref in image_refs if ref.startswith('../../images/')]
        other_images = [ref for ref in image_refs if not ref.startswith('../../images/')]
        
        print(f"  📊 圖片引用統計:")
        print(f"    - 本地圖片: {len(local_images)}")
        print(f"    - 其他圖片: {len(other_images)}")
        
        if other_images:
            print("  ⚠️  發現非本地圖片引用:")
            for img in other_images:
                print(f"    - {img}")
    
    # 檢查PDF檔案是否乾淨
    pdf_path = Path("output/pdf/AI 資本支出巨浪來襲，誰是這波行情的核心受益者？.pdf")
    if pdf_path.exists():
        print(f"\n📄 PDF檔案檢查:")
        file_size = pdf_path.stat().st_size
        print(f"  檔案大小: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        
        # 簡單的檔案大小分析
        expected_min = 800000  # 800KB (包含圖片的最小預期大小)
        expected_max = 2000000  # 2MB (包含過多UI元素時可能的大小)
        
        if file_size < expected_min:
            print("  ⚠️  檔案可能缺少圖片")
        elif file_size > expected_max:
            print("  ⚠️  檔案可能包含過多非必要元素")
        else:
            print("  ✅ 檔案大小正常")
    
    print("\n🔍 建議檢查:")
    print("1. 請打開生成的PDF檔案")
    print("2. 檢查是否還有大箭頭或其他UI控制元素")
    print("3. 確認圖片顯示正常且無遮擋")
    print("4. 文字內容應該清晰可讀")


def show_markdown_images():
    """顯示Markdown中的圖片引用"""
    md_path = Path("output/md/AI 資本支出巨浪來襲，誰是這波行情的核心受益者？.md")
    if md_path.exists():
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n🖼️  Markdown圖片引用:")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('!['):
                print(f"  第 {i} 行: {line.strip()}")


if __name__ == "__main__":
    verify_html_cleanup()
    show_markdown_images()