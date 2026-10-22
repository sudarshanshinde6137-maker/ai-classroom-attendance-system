"""
Setup Script - Installs all required dependencies automatically
Run this first: python setup.py
"""

import subprocess
import sys
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])

def main():
    print("=" * 55)
    print("  AI Classroom Attendance System - Setup")
    print("=" * 55)

    packages = [
        ("opencv-contrib-python", "cv2"),
        ("face_recognition", "face_recognition"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("Pillow", "PIL"),
        ("reportlab", "reportlab"),
        ("openpyxl", "openpyxl"),
        ("dlib", "dlib"),
    ]

    for package, module in packages:
        try:
            __import__(module)
            print(f"  [OK] {package} - already installed")
        except ImportError:
            print(f"  [...] Installing {package}...", end=" ", flush=True)
            try:
                install(package)
                print("Done")
            except subprocess.CalledProcessError:
                print(f"[FAILED] - try manually: pip install {package}")

    # Create required directories
    dirs = ["student_photos", "database", "attendance_records", "reports"]
    for d in dirs:
        path = os.path.join(os.path.dirname(__file__), d)
        os.makedirs(path, exist_ok=True)
    print("\n  [OK] Project directories created.")

    print("\n" + "=" * 55)
    print("  Setup complete! Run the app with:")
    print("    python main.py")
    print("=" * 55)

if __name__ == "__main__":
    main()
