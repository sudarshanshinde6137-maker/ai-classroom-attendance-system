"""
AI-Based Classroom Attendance System
Main entry point - launches the GUI application
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check if all required packages are installed"""
    missing = []
    
    packages = {
        'cv2':          'opencv-contrib-python',
        'numpy':        'numpy',
        'pandas':       'pandas',
        'PIL':          'Pillow',
        'reportlab':    'reportlab',
        'openpyxl':     'openpyxl',
        'customtkinter':'customtkinter',
        'matplotlib':   'matplotlib',
    }
    
    for module, package in packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    return missing

if __name__ == "__main__":
    # Check dependencies first
    missing = check_dependencies()
    
    if missing:
        root = tk.Tk()
        root.withdraw()
        msg = (
            "Missing required packages:\n\n" +
            "\n".join(f"  • {p}" for p in missing) +
            "\n\nPlease run:\n\npip install " + " ".join(missing)
        )
        messagebox.showerror("Missing Dependencies", msg)
        root.destroy()
        print("\n[ERROR] Missing packages. Install with:")
        print(f"  pip install {' '.join(missing)}\n")
        sys.exit(1)
    
    # Bypass login
    from gui.app import AttendanceApp
    dummy_user = {"id": 1, "username": "sudarshan", "role": "teacher", "student_id": None}
    app = AttendanceApp(user=dummy_user)
    app.run()
