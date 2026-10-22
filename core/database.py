"""
Database Manager - Handles all SQLite operations for student and attendance data
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        "database", "attendance.db")

class DatabaseManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        
        # Students table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
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

        self._migrate_attendance_schema(cur)
        self.has_subject_column = self._attendance_has_subject_column()
        
        self.conn.commit()

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
            # If the database is locked during startup, keep the app usable.
            # Existing data remains available; subject-aware writes will work once the DB is free.
            return

    # ── Student CRUD ──────────────────────────────────────────────────────────

    def add_student(self, name: str, roll_no: str, prn: str, photo_path: str = "") -> int:
        normalized_name = name.strip()
        normalized_roll = roll_no.strip()
        normalized_prn = prn.strip()

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
                "INSERT INTO students (name, roll_no, prn, photo_path) VALUES (?,?,?,?)",
                (normalized_name, normalized_roll, normalized_prn, photo_path)
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
            SELECT s.name, s.roll_no, s.prn,
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
            SELECT a.id, s.name, s.roll_no, s.prn, a.date, a.time, a.status, a.session, {subject_select}
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

    def close(self):
        self.conn.close()
