"""
PDF生成器 - 支援多種PDF引擎的抽象層
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple


class PDFGenerator:
    """PDF生成器基類"""
    
    def generate(self, html_content: str, output_path: str, base_url: Optional[str] = None) -> bool:
        """生成PDF"""
        raise NotImplementedError


class WeasyPrintGenerator(PDFGenerator):
    """WeasyPrint PDF生成器"""
    
    def __init__(self):
        self.available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """檢查WeasyPrint是否可用"""
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            # 嘗試創建一個簡單的PDF來測試
            HTML(string="<html><body>test</body></html>").write_pdf()
            return True
        except Exception:
            return False
            
    def generate(self, html_content: str, output_path: str, base_url: Optional[str] = None) -> bool:
        """使用WeasyPrint生成PDF"""
        if not self.available:
            return False
            
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            # 設定字型配置
            font_config = FontConfiguration()
            
            # 設定CSS樣式
            css = CSS(string='''
                @page {
                    size: A4;
                    margin: 2.5cm;
                }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", 
                                 "Microsoft YaHei", "微軟正黑體", sans-serif;
                    line-height: 1.6;
                    color: #333;
                }
                h1, h2, h3, h4, h5, h6 {
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                }
                img {
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 1em auto;
                }
                pre {
                    background-color: #f5f5f5;
                    padding: 1em;
                    overflow-x: auto;
                }
                code {
                    background-color: #f5f5f5;
                    padding: 0.2em 0.4em;
                    border-radius: 3px;
                }
                blockquote {
                    border-left: 4px solid #ddd;
                    margin-left: 0;
                    padding-left: 1em;
                    color: #666;
                }
            ''', font_config=font_config)
            
            # 生成PDF
            html_doc = HTML(string=html_content)
            html_doc.write_pdf(output_path, stylesheets=[css], font_config=font_config)
            return True
            
        except Exception as e:
            print(f"WeasyPrint PDF生成失敗: {e}")
            return False


class WKHTMLToPDFGenerator(PDFGenerator):
    """wkhtmltopdf PDF生成器"""
    
    def __init__(self):
        self.available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """檢查wkhtmltopdf是否可用"""
        try:
            import pdfkit
            # 檢查wkhtmltopdf是否安裝
            pdfkit.configuration()
            return True
        except Exception:
            return False
            
    def generate(self, html_content: str, output_path: str, base_url: Optional[str] = None) -> bool:
        """使用wkhtmltopdf生成PDF"""
        if not self.available:
            return False
            
        try:
            import pdfkit
            
            options = {
                'page-size': 'A4',
                'margin-top': '25mm',
                'margin-right': '25mm',
                'margin-bottom': '25mm',
                'margin-left': '25mm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # 寫入臨時HTML檔案
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html = f.name
                
            try:
                pdfkit.from_file(temp_html, output_path, options=options)
                return True
            finally:
                # 清理臨時檔案
                if os.path.exists(temp_html):
                    os.unlink(temp_html)
                    
        except Exception as e:
            print(f"wkhtmltopdf PDF生成失敗: {e}")
            return False


class ReportLabGenerator(PDFGenerator):
    """ReportLab PDF生成器（基本支援）"""
    
    def __init__(self):
        self.available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """檢查ReportLab是否可用"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            return True
        except ImportError:
            return False
            
    def generate(self, html_content: str, output_path: str, base_url: Optional[str] = None) -> bool:
        """使用ReportLab生成PDF（簡化版本）"""
        if not self.available:
            return False
            
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from bs4 import BeautifulSoup
            
            # 解析HTML提取純文字
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 創建PDF
            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4
            
            # 設定邊距
            left_margin = 25 * mm
            right_margin = width - 25 * mm
            top_margin = height - 25 * mm
            bottom_margin = 25 * mm
            
            # 當前位置
            x = left_margin
            y = top_margin
            
            # 寫入標題
            title = soup.find('h1')
            if title:
                c.setFont("Helvetica-Bold", 16)
                c.drawString(x, y, title.get_text().strip())
                y -= 30
                
            # 寫入內容（簡化版本）
            c.setFont("Helvetica", 10)
            
            # 提取所有段落
            for p in soup.find_all(['p', 'h2', 'h3']):
                text = p.get_text().strip()
                if text:
                    # 簡單的換行處理
                    lines = text.split('\n')
                    for line in lines:
                        if y < bottom_margin:
                            c.showPage()
                            y = top_margin
                            
                        # 簡單的文字換行（每80個字符）
                        while len(line) > 80:
                            c.drawString(x, y, line[:80])
                            y -= 15
                            line = line[80:]
                            
                        c.drawString(x, y, line)
                        y -= 15
                        
                    y -= 10  # 段落間距
                    
            c.save()
            return True
            
        except Exception as e:
            print(f"ReportLab PDF生成失敗: {e}")
            return False


class PDFGeneratorFactory:
    """PDF生成器工廠"""
    
    @staticmethod
    def get_generator() -> Optional[PDFGenerator]:
        """獲取可用的PDF生成器"""
        # 檢查是否在打包環境中
        is_frozen = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        
        if not is_frozen:
            # 開發環境：優先使用WeasyPrint
            generators = [
                WeasyPrintGenerator(),
                WKHTMLToPDFGenerator(),
                ReportLabGenerator()
            ]
        else:
            # 打包環境：優先使用不依賴系統庫的方案
            generators = [
                ReportLabGenerator(),
                WKHTMLToPDFGenerator(),
                WeasyPrintGenerator()
            ]
            
        for generator in generators:
            if generator.available:
                print(f"使用PDF生成器: {generator.__class__.__name__}")
                return generator
                
        return None


def generate_pdf(html_content: str, output_path: str, base_url: Optional[str] = None) -> Tuple[bool, str]:
    """
    生成PDF的統一介面
    
    Returns:
        (success, error_message)
    """
    generator = PDFGeneratorFactory.get_generator()
    
    if not generator:
        return False, "沒有可用的PDF生成器"
        
    try:
        success = generator.generate(html_content, output_path, base_url)
        if success:
            return True, ""
        else:
            return False, "PDF生成失敗"
    except Exception as e:
        return False, str(e)