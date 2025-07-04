import os
import sys
import json
import yaml
import threading
import queue
import webview
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vocus_converter import VocusArticleConverter


class API:
    def __init__(self):
        self.conversion_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.progress_callback = None
        self.progress_queue = queue.Queue()
        self.converter = None
        self.window = None  # Will be set by the main app
        
    def set_window(self, window):
        """Set the webview window reference"""
        self.window = window
        
    def set_progress_callback(self, callback_name):
        """Set the JavaScript callback for progress updates"""
        self.progress_callback = callback_name
        return {'success': True}
        
    def select_files(self):
        """Open file dialog to select HTML files"""
        try:
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=True,
                file_types=('HTML Files (*.html;*.htm)', '*.html;*.htm')
            )
            
            if result:
                # Convert to list of file objects
                files = []
                for filepath in result:
                    files.append({
                        'name': os.path.basename(filepath),
                        'path': filepath
                    })
                return {'success': True, 'files': files}
            else:
                return {'success': True, 'files': []}
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def get_file_paths(self, file_objects):
        """Convert file objects to absolute paths"""
        # In real implementation, this would handle file dialog results
        # For now, return the paths as-is
        return [f['path'] for f in file_objects]
        
    def start_conversion(self, params):
        """Start the conversion process in a background thread"""
        if self.conversion_thread and self.conversion_thread.is_alive():
            return {'success': False, 'error': 'Conversion already in progress'}
            
        self.stop_event.clear()
        self.pause_event.clear()
        
        # Start conversion in background thread
        self.conversion_thread = threading.Thread(
            target=self._run_conversion,
            args=(params,)
        )
        self.conversion_thread.start()
        
        return {'success': True}
        
    def _run_conversion(self, params):
        """Run the actual conversion process"""
        # Extract file paths from file objects
        file_objects = params['files']
        files = []
        for f in file_objects:
            file_path = f['path']
            # If path is relative or just filename, make it absolute
            if not os.path.isabs(file_path):
                # Assume it's in article_html directory
                if not file_path.startswith('article_html/'):
                    file_path = f"article_html/{f['name']}"
                # Convert to absolute path
                file_path = os.path.abspath(file_path)
            files.append(file_path)
            
        convert_pdf = params['convert_pdf']
        convert_md = params['convert_md']
        
        results = []
        total_files = len(files)
        
        for idx, file_path in enumerate(files):
            if self.stop_event.is_set():
                self._send_progress({
                    'type': 'status',
                    'message': '轉換已中止',
                    'level': 'error'
                })
                break
                
            while self.pause_event.is_set():
                if self.stop_event.is_set():
                    break
                threading.Event().wait(0.1)
                
            # Update overall progress
            self._send_progress({
                'type': 'overall',
                'current': idx,
                'total': total_files
            })
            
            # Start converting current file
            filename = os.path.basename(file_path)
            self._send_progress({
                'type': 'status',
                'message': f'開始處理: {filename}',
                'level': 'info'
            })
            
            # Debug: Check if file exists
            if not os.path.exists(file_path):
                self._send_progress({
                    'type': 'status',
                    'message': f'錯誤：檔案不存在: {file_path}',
                    'level': 'error'
                })
                continue
            
            self._send_progress({
                'type': 'status',
                'message': f'檔案存在，路徑: {file_path}',
                'level': 'info'
            })
            
            try:
                # Determine output and images directories
                try:
                    # Check if running as packaged app
                    if hasattr(sys, '_MEIPASS'):
                        # Running as packaged app - use user's Documents folder
                        home_dir = Path.home()
                        base_dir = home_dir / "VocusConverter"
                        output_dir = str(base_dir / "output")
                        images_dir = str(base_dir / "images")
                    else:
                        # Running from source - use current directory
                        output_dir = "output"
                        images_dir = "images"
                except Exception:
                    # Fallback
                    output_dir = "output"
                    images_dir = "images"
                
                # Create converter with progress callback
                converter = VocusArticleConverter(
                    file_path,
                    output_dir=output_dir,
                    images_dir=images_dir,
                    image_progress_callback=self._image_progress_callback
                )
                
                # Store current filename for progress callback
                self.current_filename = filename
                
                # Parse HTML first (this is essential!)
                converter.parse_html()
                
                # Download images if they exist
                if converter.images:
                    converter.download_images()
                
                result = {
                    'filename': filename,
                    'total_images': converter.total_images,
                    'downloaded_images': converter.downloaded_images,
                    'pdf_status': 'skipped',
                    'md_status': 'skipped',
                    'errors': []
                }
                
                # Convert to PDF if requested
                if convert_pdf:
                    try:
                        self._send_progress({
                            'type': 'status',
                            'message': f'開始轉換PDF: {filename}',
                            'level': 'info'
                        })
                        pdf_path = converter.convert_to_pdf()
                        result['pdf_status'] = 'success'
                        self._send_progress({
                            'type': 'status',
                            'message': f'PDF轉換成功: {filename}',
                            'level': 'success'
                        })
                    except Exception as e:
                        result['pdf_status'] = 'failed'
                        error_msg = f'PDF conversion error: {str(e)}'
                        result['errors'].append(error_msg)
                        self._send_progress({
                            'type': 'status',
                            'message': f'PDF轉換失敗: {filename} - PDF引擎不可用',
                            'level': 'warning'
                        })
                        
                # Convert to Markdown if requested
                if convert_md:
                    try:
                        self._send_progress({
                            'type': 'status',
                            'message': f'開始轉換Markdown: {filename}',
                            'level': 'info'
                        })
                        md_path = converter.convert_to_markdown()
                        result['md_status'] = 'success'
                        self._send_progress({
                            'type': 'status',
                            'message': f'Markdown轉換成功: {filename}',
                            'level': 'success'
                        })
                    except Exception as e:
                        result['md_status'] = 'failed'
                        error_msg = f'Markdown conversion error: {str(e)}'
                        result['errors'].append(error_msg)
                        self._send_progress({
                            'type': 'status',
                            'message': f'Markdown轉換失敗: {filename} - {str(e)}',
                            'level': 'error'
                        })
                        
                results.append(result)
                
                # Update status with detailed summary
                success_parts = []
                failed_parts = []
                
                if result['pdf_status'] == 'success':
                    success_parts.append('PDF')
                elif result['pdf_status'] == 'failed':
                    failed_parts.append('PDF')
                    
                if result['md_status'] == 'success':
                    success_parts.append('Markdown')
                elif result['md_status'] == 'failed':
                    failed_parts.append('Markdown')
                
                if result['errors']:
                    if success_parts:
                        self._send_progress({
                            'type': 'status',
                            'message': f'{filename} 部分成功: {", ".join(success_parts)} 成功, {", ".join(failed_parts)} 失敗',
                            'level': 'warning'
                        })
                    else:
                        self._send_progress({
                            'type': 'status',
                            'message': f'{filename} 轉換失敗: {", ".join(failed_parts)}',
                            'level': 'error'
                        })
                else:
                    self._send_progress({
                        'type': 'status',
                        'message': f'{filename} 全部轉換成功: {", ".join(success_parts)}',
                        'level': 'success'
                    })
                    
            except Exception as e:
                results.append({
                    'filename': filename,
                    'total_images': 0,
                    'downloaded_images': 0,
                    'pdf_status': 'failed',
                    'md_status': 'failed',
                    'errors': [str(e)]
                })
                self._send_progress({
                    'type': 'status',
                    'message': f'{filename} 轉換失敗: {str(e)}',
                    'level': 'error'
                })
                
        # Update final progress
        self._send_progress({
            'type': 'overall',
            'current': total_files,
            'total': total_files
        })
        
        # Generate report
        report_path = self._generate_report(results)
        
        # Send completion with report path
        self._send_progress({
            'type': 'complete',
            'report_path': report_path
        })
        
    def _image_progress_callback(self, current, total):
        """Callback for image download progress"""
        self._send_progress({
            'type': 'current',
            'current': current,
            'total': total,
            'filename': getattr(self, 'current_filename', '')
        })
        
    def _send_progress(self, data):
        """Send progress update to JavaScript"""
        if self.progress_callback and self.window:
            # Convert data to JSON string and call JavaScript function
            import json
            js_code = f"window.{self.progress_callback}({json.dumps(data)})"
            self.window.evaluate_js(js_code)
            
    def toggle_pause(self, is_paused):
        """Toggle pause state"""
        if is_paused:
            self.pause_event.set()
        else:
            self.pause_event.clear()
        return {'success': True}
        
    def stop_conversion(self):
        """Stop the conversion process"""
        self.stop_event.set()
        if self.conversion_thread:
            self.conversion_thread.join(timeout=5)
        return {'success': True}
        
    def _generate_report(self, results):
        """Generate conversion report in JSON and YAML formats"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        
        # Use user's home directory for output in packaged app
        try:
            # Check if running as packaged app
            if hasattr(sys, '_MEIPASS'):
                # Running as packaged app - use user's Documents folder
                home_dir = Path.home()
                base_dir = home_dir / "VocusConverter"
            else:
                # Running from source - use current directory
                base_dir = Path.cwd()
            
            report_dir = base_dir / "output" / "report"
            report_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Fallback to current directory
            report_dir = Path("output/report")
            report_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare report data
        report_data = {
            'conversion_time': datetime.now().isoformat(),
            'total_files': len(results),
            'successful_conversions': sum(1 for r in results if not r['errors']),
            'failed_conversions': sum(1 for r in results if r['errors']),
            'results': results
        }
        
        # Save JSON report
        json_path = report_dir / f"Conversion Report_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        # Save YAML report
        yaml_path = report_dir / f"Conversion Report_{timestamp}.yaml"
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(report_data, f, allow_unicode=True, default_flow_style=False)
            
        return str(yaml_path)