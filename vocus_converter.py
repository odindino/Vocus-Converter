#!/usr/bin/env python3
"""
Vocus文章轉換器
將方格子網站的HTML文章轉換為PDF和Markdown格式
"""

import os
import re
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
import html2text

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from utils.pdf_generator import generate_pdf


class VocusArticleConverter:
    """方格子文章轉換器"""
    
    def __init__(self, input_file, output_dir="output", images_dir="images", image_progress_callback=None):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.images_dir = Path(images_dir)
        
        # 確保必要目錄存在
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "pdf").mkdir(exist_ok=True)
        (self.output_dir / "md").mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        
        # 儲存文章資訊
        self.title = ""
        self.author = ""
        self.publish_date = ""
        self.last_modified = ""  # 最後修改時間
        self.content_html = ""
        self.images = []  # 儲存圖片資訊
        
        # 進度回調函數
        self.image_progress_callback = image_progress_callback
        self.total_images = 0
        self.downloaded_images = 0
        
    def parse_html(self):
        """解析HTML檔案，提取文章內容"""
        print(f"正在解析HTML檔案: {self.input_file}")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取標題
        title_meta = soup.find('meta', {'property': 'og:title'})
        if title_meta:
            self.title = title_meta.get('content', '').strip()
        else:
            # 備用方案：從h1標籤提取
            h1_tag = soup.find('h1')
            if h1_tag:
                self.title = h1_tag.get_text().strip()
        
        # 提取發布日期（包含時間）
        pubdate_meta = soup.find('meta', {'name': 'pubdate'})
        if pubdate_meta:
            pubdate_str = pubdate_meta.get('content', '')
            try:
                # 解析ISO格式日期
                dt = datetime.fromisoformat(pubdate_str.replace('Z', '+00:00'))
                self.publish_date = dt.strftime('%Y-%m-%d_%H-%M')  # 包含時間避免衝突
                self.publish_date_display = dt.strftime('%Y-%m-%d %H:%M')  # 用於顯示
            except:
                now = datetime.now()
                self.publish_date = now.strftime('%Y-%m-%d_%H-%M')
                self.publish_date_display = now.strftime('%Y-%m-%d %H:%M')
        else:
            now = datetime.now()
            self.publish_date = now.strftime('%Y-%m-%d_%H-%M')
            self.publish_date_display = now.strftime('%Y-%m-%d %H:%M')
        
        # 提取最後修改時間
        lastmod_meta = soup.find('meta', {'name': 'lastmod'})
        if not lastmod_meta:
            # 也嘗試從article:modified_time提取
            lastmod_meta = soup.find('meta', {'property': 'article:modified_time'})
        
        if lastmod_meta:
            lastmod_str = lastmod_meta.get('content', '')
            try:
                # 解析ISO格式日期
                dt = datetime.fromisoformat(lastmod_str.replace('Z', '+00:00'))
                self.last_modified = dt.strftime('%Y-%m-%d %H:%M')  # 用於顯示
            except:
                self.last_modified = self.publish_date_display  # 如果解析失敗，使用發布時間
        else:
            self.last_modified = self.publish_date_display  # 如果沒有修改時間，使用發布時間
        
        # 提取作者
        author_script = soup.find('script', {'type': 'application/ld+json'})
        if author_script:
            try:
                json_data = json.loads(author_script.string)
                if 'author' in json_data and 'name' in json_data['author']:
                    self.author = json_data['author']['name']
            except:
                pass
        
        # 提取文章內容 - 尋找包含文章內容的區塊
        article_content = soup.find('article', class_=re.compile('editor-content'))
        if not article_content:
            # 備用方案：尋找其他可能的內容容器
            article_content = soup.find('div', class_=re.compile('article.*content'))
            if not article_content:
                article_content = soup.find('main')
        
        if article_content:
            # 處理圖片
            self._process_images(article_content)
            # 清理不需要的UI元素
            self._clean_html_content(article_content)
            # 儲存處理後的HTML內容
            self.content_html = str(article_content)
        else:
            print("警告：無法找到文章內容區塊")
            self.content_html = "<p>無法提取文章內容</p>"
        
        print(f"標題: {self.title}")
        print(f"作者: {self.author}")
        print(f"發布日期: {self.publish_date_display}")
        print(f"最後修改: {self.last_modified}")
        print(f"找到 {len(self.images)} 張圖片")
    
    def _process_images(self, content_soup):
        """處理文章中的圖片"""
        img_tags = content_soup.find_all('img')
        
        # 使用集合來避免重複處理相同的圖片
        processed_urls = set()
        img_index = 0
        
        for img in img_tags:
            # 優先使用data-original-src（原始URL），其次是data-src，最後是src
            original_url = img.get('data-original-src')
            data_src_url = img.get('data-src')
            src_url = img.get('src')
            
            # 選擇最佳的URL
            img_url = None
            if original_url and 'images.vocus.cc' in original_url:
                img_url = original_url
            elif data_src_url:
                img_url = data_src_url
            elif src_url and not src_url.startswith('./'):
                img_url = src_url
            else:
                continue
            
            # 從resize URL中提取原始URL（如果需要）
            if 'resize-image.vocus.cc' in img_url and not original_url:
                match = re.search(r'url=([^&]+)', img_url)
                if match:
                    extracted_url = unquote(match.group(1))
                    if 'images.vocus.cc' in extracted_url:
                        original_url = extracted_url
            
            # 使用原始URL作為唯一標識，避免重複
            unique_url = original_url if original_url else img_url
            if unique_url in processed_urls:
                continue
            
            processed_urls.add(unique_url)
            img_index += 1
            
            # 確定圖片副檔名
            img_ext = self._get_image_extension(original_url if original_url else img_url)
            
            # 生成本地檔名
            img_filename = f"image_{img_index}{img_ext}"
            img_folder = self.images_dir / f"article_{self.publish_date}"
            img_folder.mkdir(exist_ok=True)
            img_path = img_folder / img_filename
            
            # 儲存圖片資訊
            img_info = {
                'url': original_url if original_url else img_url,  # 優先使用原始URL
                'resize_url': data_src_url if data_src_url and 'resize-image.vocus.cc' in data_src_url else None,
                'local_path': img_path,
                'alt': img.get('alt', ''),
                'relative_path': f"../../images/article_{self.publish_date}/{img_filename}"
            }
            self.images.append(img_info)
            
            # 更新img標籤的src屬性為本地路徑
            img['src'] = img_info['relative_path']
            if 'data-src' in img.attrs:
                del img['data-src']
            if 'data-original-src' in img.attrs:
                del img['data-original-src']
    
    def _clean_html_content(self, content_soup):
        """清理HTML內容中不需要的UI元素"""
        
        # 首先標記所有需要保留的圖片
        preserved_imgs = set()
        all_imgs = content_soup.find_all('img')
        for img in all_imgs:
            # 如果img有src屬性且包含我們的相對路徑，則保留
            src = img.get('src', '')
            if '../../images/' in src:
                preserved_imgs.add(img)
        
        # 移除縮放控制元素 (zoom control)
        zoom_controls = content_soup.find_all('div', class_=re.compile('zoom-control'))
        for control in zoom_controls:
            # 確保不移除包含圖片的控制元素
            if not control.find_all('img'):
                control.decompose()
        
        # 移除放大按鈕和相關元素
        zoom_buttons = content_soup.find_all('button', attrs={'aria-label': re.compile('Expand image')})
        for button in zoom_buttons:
            button.decompose()
        
        # 移除rmiz相關的縮放元素，但絕對保留圖片
        rmiz_elements = content_soup.find_all(attrs={'data-rmiz': True})
        for element in rmiz_elements:
            if element.name == 'img':
                # 如果是img標籤，只移除rmiz屬性，絕對保留圖片
                if 'data-rmiz' in element.attrs:
                    del element['data-rmiz']
            else:
                # 如果不是img標籤，檢查是否包含需要保留的圖片
                contained_imgs = element.find_all('img')
                preserved_contained = [img for img in contained_imgs if img in preserved_imgs]
                
                if preserved_contained:
                    # 如果包含需要保留的圖片，將這些圖片移出後再移除容器
                    for img in preserved_contained:
                        element.insert_before(img)
                    element.decompose()
                else:
                    # 如果沒有需要保留的圖片，直接移除
                    element.decompose()
        
        # 移除所有SVG圖標 (這些通常是UI控制元素)
        svgs = content_soup.find_all('svg')
        for svg in svgs:
            svg.decompose()
        
        # 移除ghost元素 (用於縮放的虛擬元素)
        ghost_elements = content_soup.find_all(attrs={'data-rmiz-ghost': True})
        for ghost in ghost_elements:
            ghost.decompose()
        
        # 移除廣告相關內容
        ad_patterns = [
            "為什麼會看到廣告",
            "廣告",
            "advertisement",
            "ads"
        ]
        
        # 查找並移除包含廣告關鍵字的元素
        all_elements = content_soup.find_all(text=True)
        for text_node in all_elements:
            text_content = text_node.strip()
            for pattern in ad_patterns:
                if pattern in text_content:
                    # 找到包含此文字的父元素並移除
                    parent = text_node.parent
                    if parent:
                        # 如果是完全匹配廣告文字的段落，移除整個段落
                        if text_content == pattern or len(text_content) < 20:
                            parent.decompose()
                            break
        
        # 移除其他可能的UI控制元素（但保護圖片）
        ui_selectors = [
            {'class': re.compile('zoom.*control')},
            {'class': re.compile('.*zoom.*')},
            {'data-rmiz-btn-zoom': True},
            {'data-rmiz-btn-zoom-icon': True},
            {'class': re.compile('.*ad.*')},  # 廣告相關class
            {'class': re.compile('.*advertisement.*')}
        ]
        
        for selector in ui_selectors:
            elements = content_soup.find_all(attrs=selector)
            for element in elements:
                # 檢查元素是否包含需要保留的圖片
                if element.name == 'img' and element in preserved_imgs:
                    continue  # 跳過保留的圖片
                
                contained_imgs = element.find_all('img')
                preserved_contained = [img for img in contained_imgs if img in preserved_imgs]
                
                if preserved_contained:
                    # 如果包含需要保留的圖片，將這些圖片移出後再移除容器
                    for img in preserved_contained:
                        element.insert_before(img)
                
                element.decompose()
        
        # 修正編號問題 - 查找並修正錯誤的編號
        self._fix_numbering_issues(content_soup)
        
        # 移除空的div容器（但保留包含圖片的div）
        empty_divs = content_soup.find_all('div')
        for div in empty_divs:
            # 檢查div是否為空（無文字、無圖片、無視頻、無音頻）
            if (not div.get_text(strip=True) and 
                not div.find_all(['img', 'video', 'audio']) and
                not div.find_all(attrs={'src': True})):  # 額外檢查有src屬性的元素
                div.decompose()
        
        print(f"已清理HTML內容中的UI控制元素和廣告內容")
    
    def _fix_numbering_issues(self, content_soup):
        """修正編號問題"""
        # 查找包含特定文字的列表項目並修正編號
        all_elements = content_soup.find_all(['li', 'ol', 'p', 'div', 'span'])
        
        for item in all_elements:
            # 檢查元素內的所有文字內容，包括子元素
            text_content = item.get_text()
            
            # 修正 "Meta 的資本支出從 2024 開始明顯跳升" 的編號
            if "Meta" in text_content and "資本支出" in text_content and "2024" in text_content and "跳升" in text_content:
                # 查找包含錯誤編號的具體文字節點
                if "1." in text_content and "Meta" in text_content:
                    # 直接修改HTML字符串內容
                    original_html = str(item)
                    if "1." in original_html and "Meta" in original_html:
                        corrected_html = original_html.replace("1.", "3.", 1)
                        item.replace_with(BeautifulSoup(corrected_html, 'html.parser'))
                        print("已修正Meta資本支出段落的編號：1 → 3")
                        break
    
    def _get_image_extension(self, url):
        """從URL獲取圖片副檔名"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
            if path.endswith(ext):
                return ext
        
        # 預設為.jpg
        return '.jpg'
    
    def download_images(self):
        """下載所有圖片"""
        print(f"\n開始下載圖片...")
        
        session = requests.Session()
        success_count = 0
        fail_count = 0
        
        self.total_images = len(self.images)
        self.downloaded_images = 0
        
        # 發送初始進度
        if self.image_progress_callback:
            self.image_progress_callback(0, self.total_images)
        
        for idx, img_info in enumerate(self.images):
            # 嘗試多種下載策略
            download_success = False
            
            # 策略1：直接下載原始URL（通常是images.vocus.cc）
            if img_info['url'] and 'images.vocus.cc' in img_info['url']:
                download_success = self._try_download(
                    session, 
                    img_info['url'], 
                    img_info['local_path'],
                    strategy="原始URL"
                )
            
            # 策略2：如果有resize URL，嘗試使用它
            if not download_success and img_info.get('resize_url'):
                download_success = self._try_download(
                    session,
                    img_info['resize_url'],
                    img_info['local_path'],
                    strategy="Resize URL"
                )
            
            # 策略3：嘗試使用不同的請求頭組合
            if not download_success and img_info['url']:
                # 嘗試模擬從網頁直接訪問
                headers_web = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Upgrade-Insecure-Requests': '1'
                }
                download_success = self._try_download(
                    session,
                    img_info['url'],
                    img_info['local_path'],
                    strategy="網頁模式",
                    headers=headers_web
                )
            
            if download_success:
                success_count += 1
                self.downloaded_images += 1
            else:
                fail_count += 1
                print(f"  → 所有策略都失敗了，請手動下載: {img_info['url']}")
                print(f"  → 目標位置: {img_info['local_path']}")
            
            # 更新進度
            if self.image_progress_callback:
                self.image_progress_callback(self.downloaded_images, self.total_images)
        
        print(f"\n下載完成：成功 {success_count} 個，失敗 {fail_count} 個")
    
    def _try_download(self, session, url, save_path, strategy="", headers=None):
        """嘗試下載圖片"""
        if not headers:
            # 預設請求頭（模擬瀏覽器請求圖片）
            headers = {
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
                'Sec-Fetch-Site': 'same-site',
                'Connection': 'keep-alive'
            }
        
        try:
            print(f"  → 嘗試 {strategy}: {url}")
            response = session.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # 檢查內容類型
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type and 'octet-stream' not in content_type:
                print(f"    → 回應不是圖片: {content_type}")
                return False
            
            # 儲存圖片
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 檢查檔案大小
            file_size = save_path.stat().st_size
            if file_size < 100:  # 小於100 bytes可能是錯誤頁面
                save_path.unlink()  # 刪除無效檔案
                print(f"    → 檔案太小，可能是錯誤: {file_size} bytes")
                return False
            
            print(f"    → 成功！儲存至: {save_path} ({file_size:,} bytes)")
            return True
            
        except requests.exceptions.HTTPError as e:
            print(f"    → HTTP錯誤: {e}")
        except requests.exceptions.Timeout:
            print(f"    → 請求超時")
        except Exception as e:
            print(f"    → 錯誤: {str(e)}")
        
        return False
    
    def convert_to_markdown(self):
        """轉換為Markdown格式"""
        print(f"\n轉換為Markdown格式...")
        
        # 設定html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # 不自動換行
        
        # 轉換HTML內容
        markdown_content = h.handle(self.content_html)
        
        # 建立完整的Markdown文件
        full_markdown = f"""# {self.title}

**作者**: {self.author}  
**發布日期**: {self.publish_date_display}  
**最後修改**: {self.last_modified}

---

{markdown_content}
"""
        
        # 生成帶日期前綴的檔名
        date_prefix = self.publish_date.split('_')[0].replace('-', '')  # 轉換 YYYY-MM-DD 為 YYYYMMDD
        safe_title = self._safe_filename(self.title)
        filename = f"{date_prefix}_{safe_title}.md"
        md_path = self.output_dir / "md" / filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(full_markdown)
        
        print(f"Markdown檔案已儲存至: {md_path}")
        return md_path
    
    def convert_to_pdf(self):
        """轉換為PDF格式"""
        print(f"\n轉換為PDF格式...")
        
        # 處理HTML內容中的圖片路徑，將相對路徑轉換為絕對路徑
        processed_html = self.content_html
        
        # 將圖片的相對路徑轉換為絕對路徑
        import re
        
        def replace_img_path(match):
            img_tag = match.group(0)
            # 尋找src屬性
            src_match = re.search(r'src="([^"]+)"', img_tag)
            if src_match:
                src_path = src_match.group(1)
                if src_path.startswith('../../images/'):
                    # 轉換為絕對路徑
                    abs_path = str(Path.cwd() / src_path[6:])  # 移除 '../../'
                    img_tag = img_tag.replace(src_path, f"file://{abs_path}")
            return img_tag
        
        processed_html = re.sub(r'<img[^>]*>', replace_img_path, processed_html)
        
        # 建立包含樣式的完整HTML
        full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{self.title}</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft JhengHei", "微軟正黑體", sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        h1, h2, h3 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        h1 {{
            font-size: 24pt;
            border-bottom: 2px solid #333;
            padding-bottom: 0.3em;
        }}
        h2 {{
            font-size: 20pt;
        }}
        h3 {{
            font-size: 16pt;
        }}
        p {{
            margin: 1em 0;
            text-align: justify;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1em auto;
            page-break-inside: avoid;
        }}
        .meta-info {{
            color: #666;
            margin-bottom: 2em;
            padding-bottom: 1em;
            border-bottom: 1px solid #ccc;
        }}
        ul, ol {{
            margin: 1em 0;
            padding-left: 2em;
        }}
        li {{
            margin: 0.5em 0;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 1em;
            border-radius: 5px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 1em 0;
            padding-left: 1em;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>{self.title}</h1>
    <div class="meta-info">
        <strong>作者:</strong> {self.author}<br>
        <strong>發布日期:</strong> {self.publish_date_display}<br>
        <strong>最後修改:</strong> {self.last_modified}
    </div>
    {processed_html}
</body>
</html>
"""
        
        # 設定字體配置
        font_config = FontConfiguration()
        
        # 生成帶日期前綴的檔名
        date_prefix = self.publish_date.split('_')[0].replace('-', '')  # 轉換 YYYY-MM-DD 為 YYYYMMDD
        safe_title = self._safe_filename(self.title)
        filename = f"{date_prefix}_{safe_title}.pdf"
        pdf_path = self.output_dir / "pdf" / filename
        
        # 使用新的PDF生成器
        success, error_message = generate_pdf(full_html, str(pdf_path))
        
        if success:
            print(f"PDF檔案已儲存至: {pdf_path}")
        else:
            if WEASYPRINT_AVAILABLE:
                # 如果WeasyPrint可用但失敗，嘗試使用原始方法
                try:
                    html_doc = HTML(string=full_html)
                    html_doc.write_pdf(pdf_path, font_config=font_config)
                    print(f"PDF檔案已儲存至: {pdf_path}")
                except Exception as e:
                    print(f"PDF轉換失敗: {error_message}")
                    raise
            else:
                print(f"PDF轉換失敗: {error_message}")
                raise Exception(error_message)
        
        return pdf_path
    
    def _safe_filename(self, filename):
        """生成安全的檔案名稱"""
        # 移除或替換不安全的字元
        safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制長度
        if len(safe) > 100:
            safe = safe[:100]
        return safe.strip()
    
    def check_already_converted(self):
        """檢查文章是否已經被轉換過"""
        # 先解析HTML獲取標題（但不進行完整處理）
        with open(self.input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取標題
        title_meta = soup.find('meta', {'property': 'og:title'})
        if title_meta:
            title = title_meta.get('content', '').strip()
        else:
            h1_tag = soup.find('h1')
            if h1_tag:
                title = h1_tag.get_text().strip()
            else:
                return False, "無法提取標題"
        
        # 生成安全的檔案名稱
        safe_title = self._safe_filename(title)
        
        # 檢查PDF和Markdown檔案是否存在
        pdf_path = self.output_dir / "pdf" / f"{safe_title}.pdf"
        md_path = self.output_dir / "md" / f"{safe_title}.md"
        
        pdf_exists = pdf_path.exists()
        md_exists = md_path.exists()
        
        if pdf_exists and md_exists:
            # 檢查檔案修改時間是否比HTML檔案新
            html_mtime = self.input_file.stat().st_mtime
            pdf_mtime = pdf_path.stat().st_mtime
            md_mtime = md_path.stat().st_mtime
            
            if pdf_mtime > html_mtime and md_mtime > html_mtime:
                return True, f"已存在且較新: {safe_title}"
            else:
                return True, f"已存在但較舊: {safe_title}"
        elif pdf_exists or md_exists:
            return True, f"部分已存在: {safe_title}"
        else:
            return False, f"未轉換: {safe_title}"
    
    def convert(self):
        """執行完整的轉換流程"""
        print("="*50)
        print("開始轉換方格子文章")
        print("="*50)
        
        # 1. 解析HTML
        self.parse_html()
        
        # 2. 下載圖片
        if self.images:
            self.download_images()
            
            # 3. 生成並保存圖片URL列表
            self._save_image_urls()
        
        # 4. HTML檔案由使用者自行管理，不需要移動
        
        # 5. 轉換為Markdown
        self.convert_to_markdown()
        
        # 6. 轉換為PDF
        self.convert_to_pdf()
        
        print("\n轉換完成！")
        print("="*50)
    
    def _save_image_urls(self):
        """保存圖片URL列表到對應的圖片資料夾"""
        img_folder = self.images_dir / f"article_{self.publish_date}"
        urls_file = img_folder / "image_urls.txt"
        
        content = f"圖片URL列表 - 來自: {self.input_file.name}\n"
        content += f"文章標題: {self.title}\n"
        content += f"發布日期: {self.publish_date_display}\n"
        content += "="*50 + "\n\n"
        
        for i, img_info in enumerate(self.images, 1):
            content += f"圖片 {i}:\n"
            content += f"  原始URL: {img_info['url']}\n"
            if img_info.get('resize_url'):
                content += f"  Resize URL: {img_info['resize_url']}\n"
            content += f"  本地路徑: {img_info['local_path']}\n"
            content += f"  Alt文字: {img_info['alt']}\n"
            content += "\n"
        
        with open(urls_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"圖片URL列表已儲存至: {urls_file}")
    


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='將方格子HTML文章轉換為PDF和Markdown格式')
    parser.add_argument('input_file', help='輸入的HTML檔案路徑')
    parser.add_argument('--output-dir', '-o', default='output', help='輸出目錄 (預設: output)')
    parser.add_argument('--images-dir', '-i', default='images', help='圖片儲存目錄 (預設: images)')
    
    args = parser.parse_args()
    
    # 檢查輸入檔案是否存在
    if not os.path.exists(args.input_file):
        print(f"錯誤：找不到輸入檔案 {args.input_file}")
        return
    
    # 建立轉換器並執行
    converter = VocusArticleConverter(
        input_file=args.input_file,
        output_dir=args.output_dir,
        images_dir=args.images_dir
    )
    
    converter.convert()


if __name__ == "__main__":
    main()