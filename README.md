# 🎓 AI Classroom Attendance Studio v2.0
### Comprehensive Face-Recognition Attendance Suite (Desktop GUI & Web Studio)

An intelligent, multi-platform classroom attendance system featuring OpenCV YuNet & SFace deep-learning face recognition, live webcam auto-scanning with audio feedback, classroom group photo processing, academic defaulter analysis, monthly register grid sheets, and bulk roster import.

---

## 🌟 Key Features

1. **Dual Interface**:
   - **Modern Desktop App**: Built with CustomTkinter, real-time charts (Matplotlib), Mediapipe HUD mesh, and pyttsx3 voice AI.
   - **Fast Web Studio**: Built with FastAPI, modern glassmorphic responsive UI, HTML5 camera streaming, canvas overlays, and audio chime.
2. **High-Accuracy Deep Learning Face Recognition**:
   - OpenCV YuNet face detector + SFace recognizer (ONNX models, ~37 MB, auto-downloaded on first run).
   - High precision and compatible with modern Python without requiring C++ build tools.
3. **Classroom Group Photo Attendance**:
   - Mark an entire lecture hall in 1-click by uploading a high-resolution classroom photo.
   - Generates annotated images with bounding boxes and matching confidence scores.
4. **Academic Defaulters Analysis (< 75% Attendance)**:
   - Automatically tracks lecture attendance percentages for every student across subjects.
   - Generates official Defaulters Notice Reports in formatted Excel and printable PDF.
5. **Monthly Attendance Register Matrix**:
   - College-style register sheet (Students as rows, Days 1..31 as columns with P/A status).
   - Exports directly to color-coded Excel spreadsheets.
6. **Bulk Student Roster Import**:
   - Quickly enroll an entire batch by importing CSV or Excel spreadsheets (`Name`, `Roll No`, `PRN`).
7. **Comprehensive Multi-Format Exports**:
   - Daily & historical records exportable to Excel (`.xlsx`), PDF (`.pdf`), and CSV (`.csv`).

---

## 📁 Project Structure

```
attendance_system/
├── main.py                    ← Launches the Desktop GUI application
├── run.bat                    ← 1-click batch launcher for Desktop GUI
├── run_web.bat                ← 1-click batch launcher for Web Studio (FastAPI)
├── setup.py                   ← Dependency installer
├── requirements.txt           ← Python dependencies
├── core/
│   ├── auth.py                ← User authentication & role management
│   ├── database.py            ← SQLite database manager & academic analytics
│   ├── face_engine.py         ← YuNet + SFace ONNX face recognition engine
│   └── reports.py             ← Excel, PDF & CSV report generator
├── gui/
│   ├── app.py                 ← Main CustomTkinter GUI & Web Studio launcher
│   ├── webcam_window.py       ← Live webcam window with Mediapipe HUD
│   ├── login_window.py        ← Login window with role selection
│   └── student_portal.py      ← Student self-service attendance portal
├── web/
│   ├── server.py              ← FastAPI server & async REST endpoints
│   └── static/
│       ├── index.html         ← Modern web application frontend
│       ├── style.css          ← Dark glassmorphic stylesheet
│       └── app.js             ← Async web client with live camera auto-scan
├── student_photos/            ← Stored enrolled student portraits
├── database/                  ← SQLite database & trained face encodings
└── attendance_records/        ← Generated Excel, PDF, and CSV reports
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Desktop Application
Double-click `run.bat` or run:
```bash
python main.py
```

### 3. Launch the Web Studio
Double-click `run_web.bat` or run:
```bash
python web/server.py
```
Then open your browser at: **`http://localhost:8000`**
*(You can also launch the Web Studio directly from inside the Desktop GUI using the "🌐 Web Studio" button in the top bar!)*

---

## 📖 Feature Walkthrough

### 👤 1. Student Enrollment
- **Single Enrollment**: Enter Student Name, Roll Number, and PRN. Upload a clear portrait or take a snapshot with your webcam.
- **Bulk Roster Import**: Upload a `.csv` or `.xlsx` spreadsheet with student details to instantly register an entire class.

### 📸 2. Group Photo Attendance
- Upload a full classroom photo from your mobile or camera.
- The AI locates every student, compares embeddings against enrolled faces, and marks attendance.
- Unknown faces and non-enrolled students are flagged for manual review.

### 🎥 3. Live Webcam Scanner
- **Desktop Mode**: Live preview with Mediapipe facial mesh HUD, confidence meter, and pyttsx3 voice greeting.
- **Web Mode**: In-browser real-time scanner with 1.5s auto-scan loop, canvas bounding boxes, and success chimes.

### ⚠️ 4. Defaulters Report (< 75%)
- Under **Records & Reports**, click **⚠️ Defaulters (< 75%)**.
- The system evaluates total lecture slots held vs attended, flags students in the danger zone, and exports an official notice in Excel or PDF.

### 📅 5. Monthly Register Matrix
- Click **📅 Monthly Matrix** to export a complete day-by-day attendance register sheet for any month and subject.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|-------|--------------|
| **AI / Vision** | OpenCV YuNet (Detector) + SFace (Embeddings) |
| **Desktop GUI** | CustomTkinter, Matplotlib, PIL, pyttsx3, Mediapipe |
| **Web Server** | FastAPI, Uvicorn, Python-Multipart |
| **Web Frontend**| Vanilla HTML5, Modern CSS (Glassmorphism), Vanilla JS (ES6+) |
| **Database** | SQLite3 (Thread-safe, relational schema) |
| **Reporting** | ReportLab (PDF), Pandas, OpenPyXL (Excel) |

---

*AI Classroom Attendance Studio — Automated, Accurate, and Production-Ready.*
