#!/usr/bin/env python3
import webview
import os
import sys
from pathlib import Path
from gui.api import API


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def main():
    # Create API instance
    api = API()
    
    # Get absolute path to GUI directory
    gui_dir = get_resource_path('gui')
    index_path = os.path.join(gui_dir, 'index.html')
    
    # Ensure the GUI directory exists
    if not os.path.exists(index_path):
        print(f"Error: Cannot find GUI files at {index_path}")
        print(f"Looking in: {gui_dir}")
        print(f"Files found: {os.listdir(gui_dir) if os.path.exists(gui_dir) else 'Directory not found'}")
        sys.exit(1)
    
    # Create window
    window = webview.create_window(
        'Vocus Article Converter',
        index_path,
        width=900,
        height=800,
        resizable=True,
        js_api=api
    )
    
    # Set window reference in API
    api.set_window(window)
    
    # Start GUI
    webview.start()


if __name__ == '__main__':
    main()