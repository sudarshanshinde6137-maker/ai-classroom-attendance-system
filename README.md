# 🎓 AI Classroom Attendance System
### Automated face-recognition attendance using group photos

---

## 📁 Project Structure

```
attendance_system/
├── main.py                    ← Run this to start the app
├── setup.py                   ← Run this first to install dependencies
├── requirements.txt
├── gui/
│   ├── app.py                 ← Main Tkinter GUI
│   └── webcam_window.py       ← Live webcam attendance window
├── core/
│   ├── database.py            ← SQLite database manager
│   ├── face_engine.py         ← Face recognition engine
│   └── reports.py             ← Excel & PDF report generator
├── student_photos/            ← Auto-created, stores student images
├── database/                  ← Auto-created, stores attendance.db
└── attendance_records/        ← Auto-created, exported reports go here
```

---

## ⚙️ Installation

### Step 1 — Install Python 3.13
Download from: https://www.python.org/downloads/release/python-3130/

> **Important:** On this machine, Python 3.14 fails to build `dlib` without Visual C++ Build Tools. Use Python 3.13 for the smoothest setup.

### Step 2 — Install dependencies

**Option A (Automatic):**
```bash
python setup.py
```

**Option B (Manual):**
```bash
pip install opencv-contrib-python face_recognition numpy pandas Pillow reportlab openpyxl dlib
```

> **Note for Windows:** If `dlib` fails on Python 3.13, install `cmake` first:
> ```bash
> pip install cmake
> pip install dlib
> ```

---

## 🚀 Running the Application

```bash
python main.py
```

---

## 📖 How to Use

### 1. Register Students (Tab: 👤 Register)
- Enter student **Name**, **Roll Number**, and **PRN**
- Upload a clear front-facing photo
- Click **Register Student**
- The face is automatically encoded and stored

### 2. Mark Attendance from Group Photo (Tab: 📸 Mark Attendance)
- Click **Upload Group Photo**
- Select the classroom group photo
- The system detects all faces, matches them with the database
- Attendance is automatically marked and displayed
- Unknown faces are flagged with ⚠️

### 3. Live Webcam Mode (Tab: 📸 → 🎥 Live Webcam)
- Click **Live Webcam Mode**
- The webcam opens in real-time
- Every 2 seconds, faces are scanned and attendance is marked
- Already-marked students are not marked twice (duplicate prevention)

### 4. View Records (Tab: 📋 Records)
- Filter by date using the date input
- View all historical attendance records
- Export filtered records as **Excel** or **PDF**

### 5. Export Reports (Dashboard or Records)
- **Excel**: Color-coded attendance sheet + summary tab
- **PDF**: Formatted report with statistics and color-coded rows

### 6. Dashboard (Tab: 📊 Dashboard)
- See today's summary: Total, Present, Absent, Percentage
- View today's real-time attendance list

### 7. Retrain Model
- Click **🔄 Retrain Model** in the sidebar
- Re-encodes all student photos from scratch
- Useful after adding many new students

---

## 🔧 Settings (Sidebar)
- **Session**: Morning / Afternoon / Evening
- **Recognition Tolerance**: 0.3 (strict) to 0.7 (loose) — default 0.55

---

## 🛠️ Technologies
| Component | Library |
|-----------|---------|
| Face Detection | `face_recognition` (dlib-based) |
| Computer Vision | `OpenCV` |
| GUI | `Tkinter` |
| Database | `SQLite3` |
| Excel Export | `pandas` + `openpyxl` |
| PDF Export | `reportlab` |
| Image Handling | `Pillow` |

---

## 💡 Tips for Best Accuracy
1. Use **clear, well-lit, front-facing photos** for registration
2. Register **multiple angles** by running the registration multiple times
3. For group photos, ensure **good lighting** and **visible faces**
4. Lower tolerance (0.4) = stricter = fewer false positives
5. Higher tolerance (0.65) = lenient = detects more but may misidentify

---

## 📂 Output Files
- **Database**: `database/attendance.db`
- **Encodings**: `database/encodings.pkl`
- **Reports**: `attendance_records/Attendance_YYYY_MM_DD.xlsx/.pdf`
- **Annotated photos**: `attendance_records/annotated_HHMMSS.jpg`

---

*Built with Python for classroom attendance automation.*
