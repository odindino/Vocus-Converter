#!/usr/bin/env python3
"""
進階圖片下載器
針對Vocus網站圖片的專用下載工具，包含多種反防盜鏈策略
"""

import os
import time
import random
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
import re
from bs4 import BeautifulSoup


class AdvancedImageDownloader:
    """進階圖片下載器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.downloaded_urls = set()
        self.success_count = 0
        self.fail_count = 0
        
        # 設定多組不同的請求頭
        self.header_sets = [
            # Chrome瀏覽器
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://vocus.cc/',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-site'
            },
            # Safari瀏覽器
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'Accept': 'image/png,image/svg+xml,image/*;q=0.8,video/*;q=0.8,*/*;q=0.5',
                'Accept-Language': 'zh-tw',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://vocus.cc/',
                'Connection': 'keep-alive'
            },
            # Firefox瀏覽器
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Accept': 'image/avif,image/webp,*/*',
                'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://vocus.cc/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-site'
            }
        ]
    
    def download_with_strategies(self, url, save_path, max_retries=3):
        """使用多種策略下載圖片"""
        strategies = [
            self._strategy_direct,
            self._strategy_with_delay,
            self._strategy_multiple_headers,
            self._strategy_chunked_download,
            self._strategy_curl_simulation
        ]
        
        for i, strategy in enumerate(strategies, 1):
            print(f"  → 嘗試策略 {i}/{len(strategies)}: {strategy.__name__}")
            
            for attempt in range(max_retries):
                try:
                    if strategy(url, save_path):
                        print(f"    → 成功！")
                        return True
                except Exception as e:
                    print(f"    → 嘗試 {attempt+1}/{max_retries} 失敗: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(1, 3))  # 隨機延遲
        
        return False
    
    def _strategy_direct(self, url, save_path):
        """策略1：直接下載"""
        headers = random.choice(self.header_sets)
        response = self.session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return self._save_image(response, save_path)
    
    def _strategy_with_delay(self, url, save_path):
        """策略2：延遲下載（模擬人類行為）"""
        time.sleep(random.uniform(0.5, 2.0))
        headers = random.choice(self.header_sets)
        response = self.session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return self._save_image(response, save_path)
    
    def _strategy_multiple_headers(self, url, save_path):
        """策略3：嘗試多組請求頭"""
        for headers in self.header_sets:
            try:
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                if self._save_image(response, save_path):
                    return True
            except:
                continue
        return False
    
    def _strategy_chunked_download(self, url, save_path):
        """策略4：分塊下載"""
        headers = random.choice(self.header_sets)
        response = self.session.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                time.sleep(0.01)  # 小延遲模擬慢速下載
        
        return self._validate_image(save_path)
    
    def _strategy_curl_simulation(self, url, save_path):
        """策略5：模擬curl請求"""
        headers = {
            'User-Agent': 'curl/7.68.0',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }
        response = self.session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return self._save_image(response, save_path)
    
    def _save_image(self, response, save_path):
        """儲存圖片並驗證"""
        # 檢查內容類型
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type and 'octet-stream' not in content_type:
            print(f"      警告：內容類型可能不正確: {content_type}")
        
        # 儲存檔案
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return self._validate_image(save_path)
    
    def _validate_image(self, save_path):
        """驗證圖片檔案"""
        if not save_path.exists():
            return False
        
        file_size = save_path.stat().st_size
        if file_size < 100:
            save_path.unlink()
            print(f"      檔案太小，刪除: {file_size} bytes")
            return False
        
        # 檢查檔案頭
        with open(save_path, 'rb') as f:
            header = f.read(20)
        
        # 常見圖片格式的檔案頭
        image_signatures = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF87a',  # GIF87a
            b'GIF89a',  # GIF89a
            b'RIFF',  # WebP (部分)
            b'\x00\x00\x01\x00',  # ICO
        ]
        
        is_valid_image = any(header.startswith(sig) for sig in image_signatures)
        if not is_valid_image:
            print(f"      警告：檔案格式可能有問題，但保留檔案")
        
        print(f"      檔案大小: {file_size:,} bytes")
        return True
    
    def batch_download_from_html(self, html_file, output_dir="images"):
        """從HTML檔案批次下載圖片"""
        print(f"開始從HTML檔案提取並下載圖片: {html_file}")
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取發布日期
        publish_date = self._extract_publish_date(soup)
        
        # 建立輸出目錄
        output_path = Path(output_dir) / f"article_{publish_date}"
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 提取所有圖片URL
        image_urls = self._extract_image_urls(soup)
        print(f"找到 {len(image_urls)} 個唯一圖片URL")
        
        # 下載圖片
        for i, url in enumerate(image_urls, 1):
            if url in self.downloaded_urls:
                continue
            
            print(f"\n[{i}/{len(image_urls)}] 下載: {url}")
            
            # 確定副檔名
            ext = self._get_extension_from_url(url)
            save_path = output_path / f"image_{i}{ext}"
            
            if self.download_with_strategies(url, save_path):
                self.success_count += 1
                self.downloaded_urls.add(url)
            else:
                self.fail_count += 1
                print(f"  → 下載失敗")
        
        print(f"\n下載完成：成功 {self.success_count} 個，失敗 {self.fail_count} 個")
    
    def _extract_publish_date(self, soup):
        """提取發布日期"""
        from datetime import datetime
        
        pubdate_meta = soup.find('meta', {'name': 'pubdate'})
        if pubdate_meta:
            pubdate_str = pubdate_meta.get('content', '')
            try:
                dt = datetime.fromisoformat(pubdate_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except:
                pass
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_image_urls(self, soup):
        """提取所有圖片URL"""
        urls = set()
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            # 多個屬性可能包含URL
            for attr in ['data-original-src', 'data-src', 'src']:
                url = img.get(attr)
                if url and 'images.vocus.cc' in url:
                    urls.add(url)
                elif url and 'resize-image.vocus.cc' in url:
                    # 從resize URL中提取原始URL
                    match = re.search(r'url=([^&]+)', url)
                    if match:
                        original_url = unquote(match.group(1))
                        if 'images.vocus.cc' in original_url:
                            urls.add(original_url)
        
        return sorted(urls)  # 排序以保證一致性
    
    def _get_extension_from_url(self, url):
        """從URL獲取副檔名"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
            if path.endswith(ext):
                return ext
        
        return '.jpg'  # 預設


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='進階Vocus圖片下載器')
    parser.add_argument('html_file', help='HTML檔案路徑')
    parser.add_argument('--output-dir', '-o', default='images', help='輸出目錄')
    
    args = parser.parse_args()
    
    downloader = AdvancedImageDownloader()
    downloader.batch_download_from_html(args.html_file, args.output_dir)


if __name__ == "__main__":
    main()