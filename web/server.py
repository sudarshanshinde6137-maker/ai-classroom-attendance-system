"""
FastAPI Localhost Server for AI Classroom Attendance System
High-performance, async-ready web interface with real-time face recognition.
"""

import os
import sys
import base64
import shutil
from datetime import datetime
from typing import Optional, List
import numpy as np
import cv2

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.database import DatabaseManager
from core.face_engine import FaceEngine
from core.reports import export_excel, export_pdf, export_csv

PHOTOS_DIR = os.path.join(PROJECT_ROOT, "student_photos")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "attendance_records")
STATIC_DIR = os.path.join(PROJECT_ROOT, "web", "static")

os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

SUBJECTS = [
    "Mathematics",
    "Python Programming Lab",
    "Java Programming Lab",
    "Principles of Communication Lab",
    "M&M Lab",
]
SESSIONS = ["Morning", "Afternoon", "Evening"]

app = FastAPI(title="AI Classroom Attendance System", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
db = DatabaseManager()
engine = FaceEngine()

# Ensure encodings are up to date
def ensure_encodings():
    if engine.trained_count == 0:
        students = [
            s for s in db.get_all_students()
            if s.get("photo_path") and os.path.exists(s["photo_path"])
        ]
        if students:
            engine.retrain_all(students)

ensure_encodings()

# Serve static files and student photos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/student_photos", StaticFiles(directory=PHOTOS_DIR), name="student_photos")


class FrameScanRequest(BaseModel):
    image_base64: str
    session: str = "Morning"
    subject: str = "Mathematics"
    tolerance: float = 0.55


class ManualMarkRequest(BaseModel):
    student_id: int
    date: str
    session: str = "Morning"
    subject: str = "Mathematics"
    status: str = "Present"  # "Present" or "Absent"


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>AI Attendance System Web Server Running</h1>")


@app.get("/api/meta")
async def get_meta():
    return {
        "subjects": SUBJECTS,
        "sessions": SESSIONS,
        "default_subject": SUBJECTS[0],
        "default_session": SESSIONS[0],
        "today": datetime.now().strftime("%Y-%m-%d"),
        "now_time": datetime.now().strftime("%H:%M:%S"),
        "trained_faces": engine.trained_count,
    }


@app.get("/api/dashboard")
async def get_dashboard(
    date: Optional[str] = None,
    session: Optional[str] = "Morning",
    subject: Optional[str] = "Mathematics"
):
    selected_date = date or datetime.now().strftime("%Y-%m-%d")
    selected_session = session or "Morning"
    selected_subject = subject or SUBJECTS[0]

    all_students = db.get_all_students()
    total_students = len(all_students)

    # Get records for this date/session/subject
    records = db.get_attendance_by_date(selected_date, session=selected_session, subject=selected_subject)
    
    # Map attendance by student_id or roll_no
    present_roll_map = {r["roll_no"]: r for r in records if r["status"] == "Present"}
    present_count = len(present_roll_map)
    absent_count = max(0, total_students - present_count)
    pct = round((present_count / total_students * 100), 1) if total_students > 0 else 0.0

    # Build rich student list with photo urls and status
    student_list = []
    for s in all_students:
        roll = s["roll_no"]
        is_pres = roll in present_roll_map
        att_row = present_roll_map.get(roll, {})
        photo_filename = os.path.basename(s["photo_path"]) if s.get("photo_path") else ""
        photo_url = f"/student_photos/{photo_filename}" if photo_filename and os.path.exists(os.path.join(PHOTOS_DIR, photo_filename)) else ""

        student_list.append({
            "id": s["id"],
            "name": s["name"],
            "roll_no": s["roll_no"],
            "prn": s["prn"],
            "photo_url": photo_url,
            "status": "Present" if is_pres else "Absent",
            "time": att_row.get("time", "--"),
            "session": selected_session,
            "subject": selected_subject,
        })

    # Subject breakdown for today
    subject_summary = db.get_subject_summary(selected_date, subjects=SUBJECTS)

    return {
        "date": selected_date,
        "session": selected_session,
        "subject": selected_subject,
        "summary": {
            "total": total_students,
            "present": present_count,
            "absent": absent_count,
            "percentage": pct,
        },
        "students": student_list,
        "subject_summary": subject_summary,
        "trained_faces": engine.trained_count,
    }


@app.post("/api/attendance/scan-frame")
async def scan_frame(payload: FrameScanRequest):
    """
    Real-time face recognition from webcam base64 frame.
    Detects faces, marks attendance in DB, and returns locations & status.
    """
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        
        img_bytes = base64.b64decode(raw_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image frame data")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Frame decode error: {e}")

    # Recognize faces using FaceEngine
    results = engine.recognize_from_frame(frame, tolerance=payload.tolerance)
    
    recognized_events = []
    today = datetime.now().strftime("%Y-%m-%d")

    for r in results:
        sid = r["student_id"]
        conf = r["confidence"]
        name = r["name"]
        loc = r["location"]  # (top, right, bottom, left)

        student_info = db.get_student_by_id(sid) if sid else None
        roll_no = student_info["roll_no"] if student_info else ""
        prn = student_info["prn"] if student_info else ""

        marked_now = False
        already_marked = False

        if sid:
            # Check if already present today for this session & subject
            # Attempt to mark
            success = db.mark_attendance(sid, session=payload.session, subject=payload.subject)
            if success:
                marked_now = True
            else:
                already_marked = True

        recognized_events.append({
            "student_id": sid,
            "name": name,
            "roll_no": roll_no,
            "prn": prn,
            "confidence": conf,
            "recognized": sid is not None,
            "marked_now": marked_now,
            "already_marked": already_marked,
            "location": loc,
        })

    return {
        "status": "ok",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "faces_detected": len(results),
        "results": recognized_events,
    }


@app.post("/api/attendance/upload-group-photo")
async def upload_group_photo(
    file: UploadFile = File(...),
    session: str = Form("Morning"),
    subject: str = Form("Mathematics"),
    tolerance: float = Form(0.55),
):
    """
    Process classroom group photo, mark attendance for all detected faces,
    and return annotated image with bounding boxes.
    """
    temp_dir = os.path.join(PROJECT_ROOT, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"group_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Recognize faces
        detections = engine.recognize_faces(temp_path, tolerance=tolerance)

        annotated_students = []
        newly_marked = []
        already_marked = []
        unknown_faces = 0

        for d in detections:
            sid = d["student_id"]
            name = d["name"]
            conf = d["confidence"]

            if sid:
                s_info = db.get_student_by_id(sid)
                roll = s_info["roll_no"] if s_info else ""
                prn = s_info["prn"] if s_info else ""

                marked = db.mark_attendance(sid, session=session, subject=subject)
                item = {
                    "student_id": sid,
                    "name": name,
                    "roll_no": roll,
                    "prn": prn,
                    "confidence": conf,
                    "location": d["location"],
                }
                if marked:
                    newly_marked.append(item)
                else:
                    already_marked.append(item)
                annotated_students.append(item)
            else:
                unknown_faces += 1

        # Draw annotated image
        annotated_cv = engine.annotate_image(temp_path, detections)
        _, encoded_img = cv2.imencode(".jpg", annotated_cv)
        annotated_b64 = base64.b64encode(encoded_img).decode("utf-8")
        annotated_data_url = f"data:image/jpeg;base64,{annotated_b64}"

        return {
            "total_faces": len(detections),
            "newly_marked": newly_marked,
            "already_marked": already_marked,
            "unknown_count": unknown_faces,
            "annotated_image": annotated_data_url,
        }
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@app.post("/api/attendance/manual")
async def manual_mark(payload: ManualMarkRequest):
    """Manually toggle or set attendance for a student."""
    if payload.status == "Present":
        db.mark_attendance(payload.student_id, session=payload.session, subject=payload.subject)
    else:
        db.remove_attendance(payload.student_id, payload.date, session=payload.session, subject=payload.subject)

    return {"status": "ok", "student_id": payload.student_id, "new_status": payload.status}


@app.get("/api/records")
async def get_records(
    date: Optional[str] = None,
    session: Optional[str] = None,
    subject: Optional[str] = None,
    search: Optional[str] = None,
):
    """Retrieve historical attendance records with filtering."""
    if date:
        raw_records = db.get_attendance_by_date(date, session=session if session != "All" else None, subject=subject if subject != "All" else None)
    else:
        raw_records = db.get_all_attendance()

    # Filter by search string if provided
    if search:
        s_lower = search.strip().lower()
        raw_records = [
            r for r in raw_records
            if s_lower in str(r.get("name", "")).lower()
            or s_lower in str(r.get("roll_no", "")).lower()
            or s_lower in str(r.get("prn", "")).lower()
        ]

    return {"records": raw_records, "count": len(raw_records)}


@app.get("/api/export")
async def export_attendance(
    format: str = Query("excel", regex="^(excel|pdf|csv)$"),
    date: Optional[str] = None,
    session: Optional[str] = None,
    subject: Optional[str] = None,
):
    """Generate and download attendance reports (Excel, PDF, or CSV)."""
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    records = db.get_attendance_by_date(
        target_date,
        session=session if session and session != "All" else None,
        subject=subject if subject and subject != "All" else None
    )
    summary = db.get_summary(target_date)

    if format == "excel":
        file_path = export_excel(records, target_date, summary)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif format == "pdf":
        file_path = export_pdf(records, target_date, summary)
        media_type = "application/pdf"
    else:
        file_path = export_csv(records, target_date)
        media_type = "text/csv"

    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/students")
async def get_students():
    """List all enrolled students."""
    students = db.get_all_students()
    for s in students:
        p_name = os.path.basename(s["photo_path"]) if s.get("photo_path") else ""
        s["photo_url"] = f"/student_photos/{p_name}" if p_name and os.path.exists(os.path.join(PHOTOS_DIR, p_name)) else ""
    return {"students": students, "total": len(students)}


@app.post("/api/students")
async def register_student(
    name: str = Form(...),
    roll_no: str = Form(...),
    prn: str = Form(...),
    photo: UploadFile = File(...),
):
    """Register a new student with photo and train their face encoding."""
    clean_name = name.strip()
    clean_roll = roll_no.strip()
    clean_prn = prn.strip()

    if not clean_name or not clean_roll or not clean_prn:
        raise HTTPException(status_code=400, detail="Name, Roll No, and PRN are required")

    ext = os.path.splitext(photo.filename)[1] or ".jpg"
    filename = f"{clean_roll}_{clean_prn}{ext}".replace(" ", "_")
    photo_path = os.path.join(PHOTOS_DIR, filename)

    try:
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        # Insert student in DB
        student_id = db.add_student(clean_name, clean_roll, clean_prn, photo_path)

        # Train face encoding
        encoded = engine.encode_student(student_id, clean_name, photo_path)
        
        return {
            "status": "success",
            "student_id": student_id,
            "name": clean_name,
            "roll_no": clean_roll,
            "prn": clean_prn,
            "face_encoded": encoded,
            "trained_faces": engine.trained_count,
        }
    except ValueError as ve:
        if os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        if os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")


@app.delete("/api/students/{student_id}")
async def delete_student(student_id: int):
    """Delete a student and their attendance records."""
    s = db.get_student_by_id(student_id)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    photo_path = s.get("photo_path")
    if photo_path and os.path.exists(photo_path):
        try:
            os.remove(photo_path)
        except Exception:
            pass

    db.delete_student(student_id)
    engine._remove_student_encoding(student_id)
    engine._save_encodings()

    return {"status": "ok", "deleted_id": student_id, "trained_faces": engine.trained_count}


@app.post("/api/retrain")
async def retrain_model():
    """Retrain face encodings for all enrolled students."""
    students = [
        s for s in db.get_all_students()
        if s.get("photo_path") and os.path.exists(s["photo_path"])
    ]
    if not students:
        return {"status": "ok", "trained": 0, "failed": 0, "message": "No photos found"}

    success, failed = engine.retrain_all(students)
    return {
        "status": "ok",
        "trained": success,
        "failed": failed,
        "total_active_encodings": engine.trained_count,
    }
