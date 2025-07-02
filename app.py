#!/usr/bin/env python3
import webview
import os
import sys
from gui.api import API


def main():
    # Create API instance
    api = API()
    
    # Get absolute path to GUI directory
    gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gui')
    index_path = os.path.join(gui_dir, 'index.html')
    
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