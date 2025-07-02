#!/usr/bin/env python3
"""
批量重新命名PDF和MD檔案，根據檔案內容中的發布日期
將檔名改為：YYYYMMDD_原檔名 格式
"""

import os
import re
from pathlib import Path
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_publish_date_from_md(file_path):
    """從Markdown檔案中提取發布日期"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尋找發布日期模式：**發布日期**: YYYY-MM-DD HH:MM
        date_pattern = r'\*\*發布日期\*\*:\s*(\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}'
        match = re.search(date_pattern, content)
        
        if match:
            return match.group(1)
        
        logger.warning(f"無法在 {file_path} 中找到發布日期")
        return None
        
    except Exception as e:
        logger.error(f"讀取MD檔案 {file_path} 時發生錯誤: {e}")
        return None

def find_corresponding_pdf(md_file_path):
    """根據MD檔案找到對應的PDF檔案"""
    md_path = Path(md_file_path)
    pdf_path = md_path.parent.parent / "pdf" / f"{md_path.stem}.pdf"
    
    if pdf_path.exists():
        return pdf_path
    return None

def format_date_for_filename(date_str):
    """將日期格式從 YYYY-MM-DD 轉換為 YYYYMMDD"""
    if date_str:
        return date_str.replace('-', '')
    return None

def rename_file_with_date(file_path, new_name):
    """重新命名檔案"""
    try:
        old_path = Path(file_path)
        new_path = old_path.parent / new_name
        
        # 檢查新檔名是否已存在
        if new_path.exists():
            logger.warning(f"目標檔案已存在，跳過: {new_path}")
            return False
            
        old_path.rename(new_path)
        logger.info(f"成功重新命名: {old_path.name} -> {new_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"重新命名檔案時發生錯誤: {e}")
        return False

def process_md_files(md_directory_path):
    """處理MD檔案並同時重新命名對應的PDF檔案"""
    md_directory = Path(md_directory_path)
    
    if not md_directory.exists():
        logger.error(f"MD目錄不存在: {md_directory_path}")
        return
    
    md_files = list(md_directory.glob("*.md"))
    logger.info(f"在 {md_directory_path} 中找到 {len(md_files)} 個 .md 檔案")
    
    successful_renames = 0
    failed_renames = 0
    
    for md_file_path in md_files:
        logger.info(f"處理MD檔案: {md_file_path.name}")
        
        # 檢查檔名是否已經是日期格式 (YYYYMMDD_)
        if re.match(r'^\d{8}_', md_file_path.name):
            logger.info(f"MD檔案已經是正確格式，跳過: {md_file_path.name}")
            continue
            
        # 從MD檔案提取發布日期
        publish_date = extract_publish_date_from_md(md_file_path)
        
        if publish_date:
            # 格式化日期
            date_formatted = format_date_for_filename(publish_date)
            
            # 生成新的MD檔名
            new_md_filename = f"{date_formatted}_{md_file_path.name}"
            
            # 重新命名MD檔案
            md_rename_success = rename_file_with_date(md_file_path, new_md_filename)
            
            # 尋找對應的PDF檔案
            pdf_file_path = find_corresponding_pdf(md_file_path)
            pdf_rename_success = True  # 預設為成功，如果沒有PDF就不影響結果
            
            if pdf_file_path:
                logger.info(f"找到對應的PDF檔案: {pdf_file_path.name}")
                
                # 檢查PDF檔名是否已經是日期格式
                if not re.match(r'^\d{8}_', pdf_file_path.name):
                    new_pdf_filename = f"{date_formatted}_{pdf_file_path.name}"
                    pdf_rename_success = rename_file_with_date(pdf_file_path, new_pdf_filename)
                else:
                    logger.info(f"PDF檔案已經是正確格式，跳過: {pdf_file_path.name}")
            else:
                logger.warning(f"未找到對應的PDF檔案: {md_file_path.stem}.pdf")
            
            # 統計結果
            if md_rename_success and pdf_rename_success:
                successful_renames += 1
            else:
                failed_renames += 1
        else:
            logger.warning(f"無法獲取發布日期，跳過檔案: {md_file_path.name}")
            failed_renames += 1
    
    logger.info(f"處理完成 - 成功: {successful_renames}, 失敗: {failed_renames}")

def main():
    """主函數"""
    base_path = Path(__file__).parent / "output"
    
    print("開始批量重新命名檔案...")
    print("格式：YYYYMMDD_原檔名")
    print("將從 Markdown 檔案中讀取發布日期，並同時重新命名對應的 PDF 檔案")
    print("-" * 70)
    
    # 處理MD檔案並同時處理對應的PDF檔案
    print("處理 Markdown 檔案並重新命名對應的 PDF 檔案...")
    md_path = base_path / "md"
    process_md_files(md_path)
    
    print("-" * 70)
    print("批量重新命名完成！")

if __name__ == "__main__":
    main()