#!/usr/bin/env python3
"""
Build script for Vocus Converter GUI application
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Failed!")
        print("Error:", e.stderr)
        return False

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))

def main():
    """Main build process"""
    print("🚀 Vocus Converter Build Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Check if we're in the correct conda environment
    env_name = os.environ.get('CONDA_DEFAULT_ENV', 'unknown')
    if env_name != 'vocus-converter':
        print(f"⚠️  Warning: You're in environment '{env_name}', but should be in 'vocus-converter'")
        print("Please run: conda activate vocus-converter")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Clean previous builds
    print("\n🧹 Cleaning previous builds...")
    clean_build_dirs()
    
    # Build with PyInstaller
    build_cmd = "pyinstaller vocus_converter_gui.spec --clean --noconfirm"
    if not run_command(build_cmd, "Building executable with PyInstaller"):
        print("❌ Build failed!")
        sys.exit(1)
    
    # Check if build was successful
    if sys.platform == 'darwin':  # macOS
        app_path = "dist/VocusConverter.app"
        if os.path.exists(app_path):
            print(f"\n✅ Build successful! macOS app created at: {app_path}")
            print(f"📦 App size: {get_directory_size(app_path):.1f} MB")
        else:
            print("❌ Build completed but app not found!")
            sys.exit(1)
    else:  # Windows/Linux
        exe_path = "dist/VocusConverter.exe" if sys.platform == 'win32' else "dist/VocusConverter"
        if os.path.exists(exe_path):
            print(f"\n✅ Build successful! Executable created at: {exe_path}")
            print(f"📦 Executable size: {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
        else:
            print("❌ Build completed but executable not found!")
            sys.exit(1)
    
    print("\n🎉 Build process completed!")
    print("\n📋 Next steps:")
    print("1. Test the built application")
    print("2. For distribution, compress the app/executable")
    print("3. Create installation instructions for end users")

def get_directory_size(path):
    """Get total size of directory in MB"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size / (1024 * 1024)

if __name__ == "__main__":
    main()