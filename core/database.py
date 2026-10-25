"""
Database Manager - Handles all SQLite operations for student and attendance data
"""

import sqlite3
import os
import re
from datetime import datetime

if os.environ.get("VERCEL"):
    import shutil
    DB_PATH = "/tmp/attendance.db"
    orig_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "attendance.db")
    if not os.path.exists(DB_PATH) and os.path.exists(orig_db):
        try:
            shutil.copy(orig_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            "database", "attendance.db")


def clean_name_part(part: str) -> str:
    """Normalize whitespace and title-case words including hyphenated segments."""
    if not part:
        return ""
    words = str(part).strip().split()
    capitalized_words = []
    for word in words:
        sub_parts = word.split("-")
        cap_sub = [p.capitalize() for p in sub_parts if p]
        capitalized_words.append("-".join(cap_sub))
    return " ".join(capitalized_words)


def validate_name_criteria(first_name: str, middle_name: str = "", last_name: str = "") -> dict:
    """
    Validates and standardizes First Name, Middle Name, and Last Name according to criteria:
    - First Name: Required, min 2 alphabetic characters, letters/hyphens/apostrophes only.
    - Middle Name: Optional; if present, letters/hyphens/apostrophes only.
    - Last Name: Required, min 2 alphabetic characters, letters/hyphens/apostrophes only.
    Returns: {"valid": True, "first_name": str, "middle_name": str, "last_name": str, "full_name": str}
    Raises ValueError with descriptive guidance if criteria are violated.
    """
    first = clean_name_part(first_name)
    middle = clean_name_part(middle_name)
    last = clean_name_part(last_name)

    # Name character pattern: allow unicode letters, apostrophes, hyphens, and spaces
    NAME_REGEX = re.compile(r"^[A-Za-zÀ-ÿ\s\'-]+$")

    if not first:
        raise ValueError("First Name is required.")
    first_pure_alpha = re.sub(r"[^A-Za-zÀ-ÿ]", "", first)
    if len(first_pure_alpha) < 2:
        raise ValueError("First Name must contain at least 2 alphabetic letters.")
    if not NAME_REGEX.match(first):
        raise ValueError("First Name can only contain letters, hyphens (-), and apostrophes ('). Numbers and special symbols are not allowed.")

    if middle:
        if not NAME_REGEX.match(middle):
            raise ValueError("Middle Name can only contain letters, hyphens (-), and apostrophes ('). Numbers and special symbols are not allowed.")

    if not last:
        raise ValueError("Last Name (Surname) is required.")
    last_pure_alpha = re.sub(r"[^A-Za-zÀ-ÿ]", "", last)
    if len(last_pure_alpha) < 2:
        raise ValueError("Last Name must contain at least 2 alphabetic letters.")
    if not NAME_REGEX.match(last):
        raise ValueError("Last Name can only contain letters, hyphens (-), and apostrophes ('). Numbers and special symbols are not allowed.")

    if middle:
        full_name = f"{first} {middle} {last}".replace("  ", " ").strip()
    else:
        full_name = f"{first} {last}".strip()

    return {
        "valid": True,
        "first_name": first,
        "middle_name": middle,
        "last_name": last,
        "full_name": full_name
    }


def split_full_name(full_name: str) -> tuple:
    """
    Splits an unparsed full name string into (first_name, middle_name, last_name).
    """
    if not full_name:
        return ("", "", "")
    parts = str(full_name).strip().split()
    if not parts:
        return ("", "", "")
    if len(parts) == 1:
        # Fallback for single word: set both first and last to satisfy criteria
        cleaned = clean_name_part(parts[0])
        return (cleaned, "", cleaned)
    if len(parts) == 2:
        return (clean_name_part(parts[0]), "", clean_name_part(parts[1]))
    # 3 or more parts: first is first, last is last, rest is middle
    return (clean_name_part(parts[0]), clean_name_part(" ".join(parts[1:-1])), clean_name_part(parts[-1]))


def validate_contact_criteria(phone: str = "", email: str = "") -> dict:
    """
    Validates and standardizes student contact details (phone and email).
    """
    clean_phone = str(phone).strip() if phone else ""
    clean_email = str(email).strip() if email else ""

    if clean_phone:
        phone_digits = re.sub(r"[^\d]", "", clean_phone)
        if len(phone_digits) < 7 or len(phone_digits) > 15:
            raise ValueError(f"Invalid phone number '{phone}'. Phone must contain between 7 and 15 digits.")
        if not re.match(r"^[\+]?[0-9\s\-\(\)]+$", clean_phone):
            raise ValueError(f"Phone number '{phone}' contains invalid characters. Only digits, +, -, and spaces are allowed.")

    if clean_email:
        email_pattern = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$")
        if not email_pattern.match(clean_email):
            raise ValueError(f"Invalid email address '{email}'. Please enter a valid format (e.g. student@college.edu).")

    return {
        "phone": clean_phone,
        "email": clean_email
    }


class DatabaseManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        
        # Students table with First Name, Middle Name, Last Name and Contact Fields
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                first_name  TEXT DEFAULT '',
                middle_name TEXT DEFAULT '',
                last_name   TEXT DEFAULT '',
                phone       TEXT DEFAULT '',
                email       TEXT DEFAULT '',
                roll_no     TEXT NOT NULL UNIQUE,
                prn         TEXT NOT NULL UNIQUE,
                photo_path  TEXT,
                registered_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        
        # Attendance table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                date        TEXT NOT NULL,
                time        TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'Present',
                session     TEXT,
                subject     TEXT NOT NULL DEFAULT 'General',
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(student_id, date, session, subject)
            )
        """)

        self._migrate_students_schema(cur)
        self._migrate_attendance_schema(cur)
        self.has_subject_column = self._attendance_has_subject_column()
        
        self.conn.commit()

    def _migrate_students_schema(self, cur):
        """Ensure all required name and contact fields exist, and backfill existing students."""
        try:
            cur.execute("PRAGMA table_info(students)")
            existing_cols = [row[1] for row in cur.fetchall()]
            if not existing_cols:
                return

            columns_to_add = [
                ("first_name", "TEXT DEFAULT ''"),
                ("middle_name", "TEXT DEFAULT ''"),
                ("last_name", "TEXT DEFAULT ''"),
                ("phone", "TEXT DEFAULT ''"),
                ("email", "TEXT DEFAULT ''"),
            ]
            for col_name, col_def in columns_to_add:
                if col_name not in existing_cols:
                    cur.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_def}")

            # Backfill existing students whose first_name or last_name is empty
            cur.execute("SELECT id, name, first_name, last_name FROM students WHERE first_name = '' OR first_name IS NULL")
            rows = cur.fetchall()
            for r in rows:
                sid, raw_name = r[0], r[1] or ""
                f, m, l = split_full_name(raw_name)
                cur.execute(
                    "UPDATE students SET first_name=?, middle_name=?, last_name=? WHERE id=?",
                    (f, m, l, sid)
                )
        except sqlite3.OperationalError as e:
            print(f"[DB] students migration notice: {e}")

    def _attendance_has_subject_column(self):
        cur = self.conn.cursor()
        try:
            cur.execute("PRAGMA table_info(attendance)")
            return any(row[1] == "subject" for row in cur.fetchall())
        except sqlite3.OperationalError:
            return False

    def _migrate_attendance_schema(self, cur):
        try:
            cur.execute("PRAGMA table_info(attendance)")
            columns = [row[1] for row in cur.fetchall()]
            if not columns:
                return

            if "subject" not in columns:
                cur.execute("ALTER TABLE attendance ADD COLUMN subject TEXT NOT NULL DEFAULT 'General'")
        except sqlite3.OperationalError:
            return

    # ── Student CRUD ──────────────────────────────────────────────────────────

    def add_student(
        self,
        name: str = "",
        roll_no: str = "",
        prn: str = "",
        photo_path: str = "",
        first_name: str = "",
        middle_name: str = "",
        last_name: str = "",
        phone: str = "",
        email: str = ""
    ) -> int:
        """
        Register a student applying structured name criteria (First Name, Middle Name, Last Name)
        and contact details (Phone, Email).
        """
        normalized_roll = str(roll_no).strip()
        normalized_prn = str(prn).strip()

        if not normalized_roll or not normalized_prn:
            raise ValueError("Roll Number and PRN are required.")

        # Apply structured name criteria
        if first_name or last_name:
            validated_name = validate_name_criteria(first_name, middle_name, last_name)
        elif name:
            f, m, l = split_full_name(name)
            validated_name = validate_name_criteria(f, m, l)
        else:
            raise ValueError("Student name criteria required: First Name and Last Name must be provided.")

        clean_first = validated_name["first_name"]
        clean_middle = validated_name["middle_name"]
        clean_last = validated_name["last_name"]
        normalized_name = validated_name["full_name"]

        # Validate contact criteria
        validated_contact = validate_contact_criteria(phone, email)
        clean_phone = validated_contact["phone"]
        clean_email = validated_contact["email"]

        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT id FROM students WHERE lower(name)=lower(?) OR roll_no=? OR prn=?",
                (normalized_name, normalized_roll, normalized_prn)
            )
            existing = cur.fetchone()
            if existing:
                raise ValueError("This student is already registered. Use a different Roll No, PRN, or update the existing record.")

            cur.execute(
                """INSERT INTO students 
                   (name, first_name, middle_name, last_name, phone, email, roll_no, prn, photo_path) 
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (normalized_name, clean_first, clean_middle, clean_last, clean_phone, clean_email, normalized_roll, normalized_prn, photo_path)
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Student with this Roll No or PRN already exists: {e}")

    def get_all_students(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM students ORDER BY roll_no")
        return [dict(row) for row in cur.fetchall()]

    def get_student_by_id(self, student_id: int):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM students WHERE id=?", (student_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_student_by_roll(self, roll_no: str):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM students WHERE roll_no=?", (roll_no,))
        row = cur.fetchone()
        return dict(row) if row else None

    def update_student_photo(self, student_id: int, photo_path: str):
        self.conn.execute(
            "UPDATE students SET photo_path=? WHERE id=?", (photo_path, student_id)
        )
        self.conn.commit()

    def update_student(
        self,
        student_id: int,
        name: str = "",
        roll_no: str = "",
        prn: str = "",
        first_name: str = "",
        middle_name: str = "",
        last_name: str = "",
        phone: str = "",
        email: str = ""
    ) -> dict:
        """Update existing student info with name criteria and contact validation."""
        student = self.get_student_by_id(student_id)
        if not student:
            raise ValueError(f"Student with ID {student_id} not found.")

        normalized_roll = str(roll_no).strip() if roll_no else student["roll_no"]
        normalized_prn = str(prn).strip() if prn else student["prn"]

        if not normalized_roll or not normalized_prn:
            raise ValueError("Roll Number and PRN cannot be empty.")

        # Check unique constraint against other students
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id FROM students WHERE (roll_no=? OR prn=?) AND id != ?",
            (normalized_roll, normalized_prn, student_id)
        )
        if cur.fetchone():
            raise ValueError("Another student already has this Roll Number or PRN.")

        # Handle names
        if first_name or last_name:
            validated_name = validate_name_criteria(first_name, middle_name, last_name)
        elif name:
            f, m, l = split_full_name(name)
            validated_name = validate_name_criteria(f, m, l)
        else:
            validated_name = {
                "first_name": student.get("first_name", ""),
                "middle_name": student.get("middle_name", ""),
                "last_name": student.get("last_name", ""),
                "full_name": student.get("name", "")
            }

        # Contact validation
        p = phone if phone is not None else student.get("phone", "")
        e = email if email is not None else student.get("email", "")
        validated_contact = validate_contact_criteria(p, e)

        cur.execute("""
            UPDATE students
            SET name=?, first_name=?, middle_name=?, last_name=?,
                phone=?, email=?, roll_no=?, prn=?
            WHERE id=?
        """, (
            validated_name["full_name"],
            validated_name["first_name"],
            validated_name["middle_name"],
            validated_name["last_name"],
            validated_contact["phone"],
            validated_contact["email"],
            normalized_roll,
            normalized_prn,
            student_id
        ))
        self.conn.commit()
        return self.get_student_by_id(student_id)

    def get_student_by_identifier(self, query: str):
        """Lookup student by exact Roll No, PRN, or case-insensitive match."""
        if not query:
            return None
        q = query.strip()
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM students
            WHERE lower(roll_no)=lower(?) OR lower(prn)=lower(?) OR lower(name)=lower(?)
            LIMIT 1
        """, (q, q, q))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_student_detail_stats(self, student_id: int) -> dict:
        """Get comprehensive individual attendance profile for a student."""
        student = self.get_student_by_id(student_id)
        if not student:
            return None

        cur = self.conn.cursor()
        # Total distinct lecture slots held across all subjects
        cur.execute("SELECT COUNT(DISTINCT date || '_' || session || '_' || COALESCE(subject,'General')) FROM attendance")
        total_held = cur.fetchone()[0] or 0

        # Total distinct lectures attended by this student
        cur.execute("""
            SELECT COUNT(DISTINCT date || '_' || session || '_' || COALESCE(subject,'General'))
            FROM attendance
            WHERE student_id=?
        """, (student_id,))
        attended = cur.fetchone()[0] or 0
        absent = max(0, total_held - attended)
        overall_pct = round((attended / total_held * 100), 1) if total_held > 0 else 0.0

        # Subject-wise statistics for this student
        subject_col = "COALESCE(subject, 'General')" if self.has_subject_column else "'General'"
        cur.execute(f"SELECT DISTINCT {subject_col} FROM attendance")
        all_subjects = [r[0] for r in cur.fetchall()] or ["General"]

        subject_breakdown = []
        for subj in all_subjects:
            cur.execute(
                f"SELECT COUNT(DISTINCT date || '_' || session) FROM attendance WHERE {subject_col}=?",
                (subj,)
            )
            subj_held = cur.fetchone()[0] or 0

            cur.execute(
                f"SELECT COUNT(DISTINCT date || '_' || session) FROM attendance WHERE student_id=? AND {subject_col}=?",
                (student_id, subj)
            )
            subj_attended = cur.fetchone()[0] or 0
            subj_pct = round((subj_attended / subj_held * 100), 1) if subj_held > 0 else 0.0

            subject_breakdown.append({
                "subject": subj,
                "held": subj_held,
                "attended": subj_attended,
                "percentage": subj_pct
            })

        # Recent 30 attendance records for this student
        cur.execute(f"""
            SELECT date, time, session, {subject_col} as subject, status
            FROM attendance
            WHERE student_id=?
            ORDER BY date DESC, time DESC
            LIMIT 30
        """, (student_id,))
        recent_logs = [dict(r) for r in cur.fetchall()]

        return {
            "student": student,
            "total_held": total_held,
            "attended": attended,
            "absent": absent,
            "overall_percentage": overall_pct,
            "is_defaulter": overall_pct < 75.0 if total_held > 0 else False,
            "risk_level": "Critical" if (total_held > 0 and overall_pct < 65.0) else ("Warning" if (total_held > 0 and overall_pct < 75.0) else "Good"),
            "subject_breakdown": subject_breakdown,
            "recent_logs": recent_logs
        }

    def get_system_stats(self) -> dict:
        """Returns database storage and operational statistics."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM students")
        total_students = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM attendance")
        total_attendance_logs = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(DISTINCT date) FROM attendance")
        total_days = cur.fetchone()[0] or 0

        db_size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        db_size_kb = round(db_size_bytes / 1024, 1)

        return {
            "total_students": total_students,
            "total_attendance_logs": total_attendance_logs,
            "total_days_active": total_days,
            "db_size_kb": db_size_kb,
            "db_path": DB_PATH
        }

    def delete_student(self, student_id: int):
        self.conn.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
        self.conn.execute("DELETE FROM students WHERE id=?", (student_id,))
        self.conn.commit()

    # ── Attendance ────────────────────────────────────────────────────────────

    def mark_attendance(self, student_id: int, session: str = "Morning", subject: str = "General") -> bool:
        """Mark a student present. Returns False if already marked today."""
        today = datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.now().strftime("%H:%M:%S")
        try:
            if self.has_subject_column:
                self.conn.execute(
                    """INSERT INTO attendance (student_id, date, time, status, session, subject)
                       VALUES (?,?,?,'Present',?,?)""",
                    (student_id, today, now_time, session, subject)
                )
            else:
                self.conn.execute(
                    """INSERT INTO attendance (student_id, date, time, status, session)
                       VALUES (?,?,?,'Present',?)""",
                    (student_id, today, now_time, session)
                )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Already marked for this student+date+session+subject
        except Exception as e:
            print(f"[DB] mark_attendance error for student_id={student_id}, subject={subject!r}: {e}")
            return False

    def remove_attendance(self, student_id: int, date: str, session: str = "Morning", subject: str = "General") -> bool:
        """Remove a student's attendance record for a date/session/subject."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "DELETE FROM attendance WHERE student_id=? AND date=? AND session=? AND subject=?",
                (student_id, date, session, subject)
            )
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            print(f"[DB] remove_attendance error: {e}")
            return False

    def get_attendance_by_date(self, date: str, session: str = None, subject: str = None):
        cur = self.conn.cursor()
        subject_col = "COALESCE(a.subject,'General') as subject" if self.has_subject_column else "'General' as subject"

        where_parts = ["a.date = ?"]
        params = [date]

        if session:
            where_parts.append("a.session = ?")
            params.append(session)
        if subject and self.has_subject_column:
            where_parts.append("a.subject = ?")
            params.append(subject)

        where_clause = " AND ".join(where_parts)

        cur.execute(f"""
            SELECT s.id as student_id, s.name, s.first_name, s.middle_name, s.last_name, s.phone, s.email, s.roll_no, s.prn,
                   COALESCE(a.time,'--') AS time,
                   CASE WHEN a.id IS NOT NULL THEN 'Present' ELSE 'Absent' END AS status,
                   COALESCE(a.session,'--') AS session,
                   {subject_col}
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id AND {where_clause}
            ORDER BY s.roll_no
        """, tuple(params))
        return [dict(row) for row in cur.fetchall()]

    def get_all_attendance(self):
        cur = self.conn.cursor()
        subject_select = "COALESCE(a.subject,'General') as subject" if self.has_subject_column else "'General' as subject"
        cur.execute(f"""
            SELECT a.id, s.name, s.first_name, s.middle_name, s.last_name, s.phone, s.email, s.roll_no, s.prn, a.date, a.time, a.status, a.session, {subject_select}
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            ORDER BY a.date DESC, s.roll_no
        """)
        return [dict(row) for row in cur.fetchall()]

    def get_summary(self, date: str):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM students", )
        total = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date=?", (date,)
        )
        present = cur.fetchone()[0]
        return {"total": total, "present": present, "absent": total - present, "date": date}

    def get_subject_summary(self, date: str, subjects=None):
        if not self.has_subject_column:
            total = self.conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            return [{
                "subject": subject,
                "present": 0,
                "total": total,
                "percentage": 0.0,
            } for subject in (subjects or [])]

        total = self.conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        subject_list = subjects or []
        results = []

        if subject_list:
            for subject in subject_list:
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date=? AND subject=?",
                    (date, subject)
                )
                present = cur.fetchone()[0]
                percentage = (present / total * 100) if total else 0
                results.append({
                    "subject": subject,
                    "present": present,
                    "total": total,
                    "percentage": round(percentage, 1)
                })
            return results

        cur = self.conn.cursor()
        cur.execute(
            "SELECT subject, COUNT(DISTINCT student_id) as present FROM attendance WHERE date=? GROUP BY subject ORDER BY subject",
            (date,)
        )
        for row in cur.fetchall():
            present = row["present"]
            results.append({
                "subject": row["subject"] or "General",
                "present": present,
                "total": total,
                "percentage": round((present / total * 100), 1) if total else 0
            })
        return results

    def is_present_today(self, student_id: int, session: str = None) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        cur = self.conn.cursor()
        if session:
            cur.execute(
                "SELECT 1 FROM attendance WHERE student_id=? AND date=? AND session=?",
                (student_id, today, session)
            )
        else:
            cur.execute(
                "SELECT 1 FROM attendance WHERE student_id=? AND date=?",
                (student_id, today)
            )
        return cur.fetchone() is not None

    # ── Academic Analytics & Defaulters ────────────────────────────────────────

    def bulk_import_students(self, students_list: list) -> dict:
        """Bulk import students from a list of dicts. Skips duplicates and enforces name criteria & contact validation."""
        imported = 0
        skipped = 0
        errors = []
        cur = self.conn.cursor()

        for idx, item in enumerate(students_list, 1):
            raw_first = str(item.get("first_name") or item.get("First Name") or item.get("firstname", "")).strip()
            raw_middle = str(item.get("middle_name") or item.get("Middle Name") or item.get("middlename", "")).strip()
            raw_last = str(item.get("last_name") or item.get("Last Name") or item.get("lastname") or item.get("Surname", "")).strip()
            raw_name = str(item.get("name") or item.get("Name") or item.get("Full Name", "")).strip()
            raw_phone = str(item.get("phone") or item.get("Phone") or item.get("Mobile") or item.get("Contact", "")).strip()
            raw_email = str(item.get("email") or item.get("Email") or item.get("Email Address", "")).strip()
            roll_no = str(item.get("roll_no") or item.get("Roll No") or item.get("roll", "")).strip()
            prn = str(item.get("prn") or item.get("PRN", "")).strip()
            photo_path = str(item.get("photo_path") or "").strip()

            if not roll_no or not prn:
                errors.append(f"Row {idx}: Missing roll_no or prn")
                continue

            try:
                if raw_first or raw_last:
                    val = validate_name_criteria(raw_first, raw_middle, raw_last)
                elif raw_name:
                    f, m, l = split_full_name(raw_name)
                    val = validate_name_criteria(f, m, l)
                else:
                    errors.append(f"Row {idx} ({roll_no}): Missing student name (First Name and Last Name required)")
                    continue
                first_name = val["first_name"]
                middle_name = val["middle_name"]
                last_name = val["last_name"]
                name = val["full_name"]
            except ValueError as ve:
                errors.append(f"Row {idx} ({roll_no}): Name criteria error: {ve}")
                continue

            try:
                con = validate_contact_criteria(raw_phone, raw_email)
                phone, email = con["phone"], con["email"]
            except ValueError as ve:
                errors.append(f"Row {idx} ({roll_no}): Contact validation error: {ve}")
                continue

            # Check if student exists
            cur.execute("SELECT id FROM students WHERE roll_no=? OR prn=?", (roll_no, prn))
            if cur.fetchone():
                skipped += 1
                continue

            try:
                cur.execute(
                    """INSERT INTO students 
                       (name, first_name, middle_name, last_name, phone, email, roll_no, prn, photo_path) 
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (name, first_name, middle_name, last_name, phone, email, roll_no, prn, photo_path)
                )
                imported += 1
            except Exception as e:
                errors.append(f"Row {idx} ({roll_no}): {e}")

        self.conn.commit()
        return {"imported": imported, "skipped": skipped, "errors": errors}

    def get_student_attendance_stats(self, subject: str = None) -> list:
        """Calculate overall attendance percentage and stats per student."""
        cur = self.conn.cursor()
        students = self.get_all_students()

        where_clause = ""
        params = []
        if subject and subject != "All" and self.has_subject_column:
            where_clause = "WHERE subject = ?"
            params = [subject]

        # Total distinct lecture slots held
        cur.execute(
            f"SELECT COUNT(DISTINCT date || '_' || session || '_' || COALESCE(subject,'General')) FROM attendance {where_clause}",
            tuple(params)
        )
        total_held = cur.fetchone()[0] or 0

        stats = []
        for s in students:
            sid = s["id"]
            if subject and subject != "All" and self.has_subject_column:
                cur.execute(
                    "SELECT COUNT(DISTINCT date || '_' || session || '_' || COALESCE(subject,'General')) FROM attendance WHERE student_id=? AND subject=?",
                    (sid, subject)
                )
            else:
                cur.execute(
                    "SELECT COUNT(DISTINCT date || '_' || session || '_' || COALESCE(subject,'General')) FROM attendance WHERE student_id=?",
                    (sid,)
                )
            attended = cur.fetchone()[0] or 0
            absent = max(0, total_held - attended)
            pct = round((attended / total_held * 100), 1) if total_held > 0 else 0.0

            stats.append({
                "student_id": sid,
                "name": s["name"],
                "first_name": s.get("first_name", ""),
                "middle_name": s.get("middle_name", ""),
                "last_name": s.get("last_name", ""),
                "phone": s.get("phone", ""),
                "email": s.get("email", ""),
                "roll_no": s["roll_no"],
                "prn": s["prn"],
                "photo_path": s.get("photo_path", ""),
                "total_held": total_held,
                "attended": attended,
                "absent": absent,
                "percentage": pct,
                "is_defaulter": pct < 75.0 if total_held > 0 else False
            })

        return stats

    def get_defaulters(self, threshold: float = 75.0, subject: str = None) -> list:
        """Return list of students with attendance percentage strictly below threshold."""
        all_stats = self.get_student_attendance_stats(subject=subject)
        defaulters = [
            s for s in all_stats
            if s["total_held"] > 0 and s["percentage"] < threshold
        ]
        return sorted(defaulters, key=lambda x: x["percentage"])

    def get_monthly_matrix(self, year: int, month: int, subject: str = None) -> dict:
        """
        Generate a monthly attendance register grid (days 1..31).
        Returns days with classes held, student records, and attendance status per day.
        """
        cur = self.conn.cursor()
        month_pattern = f"{year:04d}-{month:02d}-%"

        where_parts = ["date LIKE ?"]
        params = [month_pattern]

        if subject and subject != "All" and self.has_subject_column:
            where_parts.append("subject = ?")
            params.append(subject)

        where_sql = " AND ".join(where_parts)

        # Find distinct lecture dates in this month
        cur.execute(f"SELECT DISTINCT date FROM attendance WHERE {where_sql} ORDER BY date", tuple(params))
        held_dates = [r[0] for r in cur.fetchall()]
        held_days = [int(d.split("-")[2]) for d in held_dates]

        students = self.get_all_students()
        matrix_rows = []

        for s in students:
            sid = s["id"]
            # Find dates this student attended in this month
            s_params = [sid, month_pattern]
            s_where = ["student_id = ?", "date LIKE ?"]
            if subject and subject != "All" and self.has_subject_column:
                s_where.append("subject = ?")
                s_params.append(subject)

            cur.execute(f"SELECT DISTINCT date FROM attendance WHERE {' AND '.join(s_where)}", tuple(s_params))
            student_attended_dates = set(r[0] for r in cur.fetchall())

            day_status = {}
            attended_count = 0
            for d_str, day_num in zip(held_dates, held_days):
                if d_str in student_attended_dates:
                    day_status[day_num] = "P"
                    attended_count += 1
                else:
                    day_status[day_num] = "A"

            total_days = len(held_dates)
            pct = round((attended_count / total_days * 100), 1) if total_days > 0 else 0.0

            matrix_rows.append({
                "student_id": sid,
                "name": s["name"],
                "first_name": s.get("first_name", ""),
                "middle_name": s.get("middle_name", ""),
                "last_name": s.get("last_name", ""),
                "phone": s.get("phone", ""),
                "email": s.get("email", ""),
                "roll_no": s["roll_no"],
                "prn": s["prn"],
                "days": day_status,
                "attended": attended_count,
                "total_held": total_days,
                "percentage": pct
            })

        return {
            "year": year,
            "month": month,
            "subject": subject or "All",
            "held_dates": held_dates,
            "held_days": held_days,
            "total_held": len(held_dates),
            "rows": matrix_rows
        }

    def get_predictive_defaulters(self, threshold: float = 75.0, total_semester_classes: int = 40, subject: str = None) -> list:
        """
        AI Predictive Attendance Forecaster.
        Projects end-of-semester attendance % based on student attendance velocity,
        calculates safe skips remaining, and recovery path (consecutive lectures needed).
        """
        import math
        all_stats = self.get_student_attendance_stats(subject=subject)
        forecasts = []

        for s in all_stats:
            held = s["total_held"]
            attended = s["attended"]
            curr_pct = s["percentage"]

            # If no classes have been held yet, baseline is 100%
            if held == 0:
                current_rate = 1.0
                remaining = total_semester_classes
            else:
                current_rate = attended / held
                remaining = max(0, total_semester_classes - held)

            # Projected end-of-semester attendance
            projected_attended = min(total_semester_classes, attended + round(remaining * current_rate))
            proj_pct = round((projected_attended / total_semester_classes * 100), 1) if total_semester_classes > 0 else 0.0

            # Safe skips: how many future classes student can skip while staying >= threshold
            min_needed_total = math.ceil(total_semester_classes * (threshold / 100.0))
            future_needed = max(0, min_needed_total - attended)
            safe_skips = max(0, remaining - future_needed) if remaining >= future_needed else 0

            # Recovery requirement: consecutive lectures needed right now to escape the defaulters list
            consecutive_needed = 0
            t_ratio = threshold / 100.0
            if held > 0 and (attended / held) < t_ratio:
                if t_ratio < 1.0:
                    numerator = (t_ratio * held) - attended
                    denominator = 1.0 - t_ratio
                    consecutive_needed = max(0, math.ceil(numerator / denominator))
                else:
                    consecutive_needed = remaining

            # Categorize risk trajectory
            if proj_pct >= 80.0 and curr_pct >= threshold:
                risk = "Low Risk"
                recommendation = f"Safe buffer: Can afford {safe_skips} excused absence(s)."
            elif proj_pct >= threshold:
                risk = "Moderate Risk"
                recommendation = f"Borderline: Needs to attend at least {future_needed} of remaining {remaining} lectures."
            else:
                risk = "High Risk Defaulter"
                recommendation = f"Critical: Must attend next {consecutive_needed} consecutive lecture(s) immediately."

            forecasts.append({
                "student_id": s["student_id"],
                "name": s["name"],
                "roll_no": s["roll_no"],
                "prn": s["prn"],
                "phone": s.get("phone", ""),
                "email": s.get("email", ""),
                "classes_held": held,
                "classes_attended": attended,
                "current_percentage": curr_pct,
                "total_semester_classes": total_semester_classes,
                "remaining_classes": remaining,
                "projected_percentage": proj_pct,
                "safe_skips_allowed": safe_skips,
                "consecutive_needed": consecutive_needed,
                "risk_level": risk,
                "ai_recommendation": recommendation
            })

        return sorted(forecasts, key=lambda x: (x["projected_percentage"], x["current_percentage"]))

    def close(self):
        self.conn.close()
