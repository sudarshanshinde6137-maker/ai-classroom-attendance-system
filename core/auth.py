"""
Auth Manager - User authentication and role management for the Attendance System
Supports Teacher and Student roles with hashed passwords.
"""

import sqlite3
import hashlib
import os
from typing import Optional, Dict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "database", "attendance.db")


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class AuthManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self._create_table()
        self._seed_default_admin()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT NOT NULL UNIQUE,
                password   TEXT NOT NULL,
                role       TEXT NOT NULL DEFAULT 'student',
                student_id INTEGER,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)
        self.conn.commit()

    def _seed_default_admin(self):
        """Create default teacher account if no teacher exists."""
        row = self.conn.execute(
            "SELECT id FROM users WHERE role='teacher' LIMIT 1"
        ).fetchone()
        if not row:
            self.conn.execute(
                "INSERT OR IGNORE INTO users (username, password, role) VALUES (?,?,?)",
                ("admin", _hash("admin123"), "teacher")
            )
            self.conn.commit()

    # ── Auth ──────────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> Optional[Dict]:
        """Returns user dict on success, None on failure."""
        row = self.conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username.strip(), _hash(password))
        ).fetchone()
        return dict(row) if row else None

    def username_exists(self, username: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM users WHERE lower(username)=lower(?)", (username.strip(),)
        ).fetchone()
        return row is not None

    # ── Teacher CRUD ──────────────────────────────────────────────────────────

    def create_teacher(self, username: str, password: str) -> bool:
        try:
            self.conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?,?,?)",
                (username.strip(), _hash(password), "teacher")
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def create_student_login(self, username: str, password: str, student_id: int) -> bool:
        try:
            self.conn.execute(
                "INSERT INTO users (username, password, role, student_id) VALUES (?,?,?,?)",
                (username.strip(), _hash(password), "student", student_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_all_users(self):
        rows = self.conn.execute("""
            SELECT u.id, u.username, u.role, u.created_at,
                   s.name as student_name, s.roll_no
            FROM users u
            LEFT JOIN students s ON u.student_id = s.id
            ORDER BY u.role DESC, u.username
        """).fetchall()
        return [dict(r) for r in rows]

    def change_password(self, user_id: int, new_password: str) -> bool:
        try:
            self.conn.execute(
                "UPDATE users SET password=? WHERE id=?",
                (_hash(new_password), user_id)
            )
            self.conn.commit()
            return True
        except Exception:
            return False

    def delete_user(self, user_id: int) -> bool:
        try:
            self.conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            self.conn.commit()
            return True
        except Exception:
            return False

    def get_student_id_for_user(self, user_id: int) -> Optional[int]:
        row = self.conn.execute(
            "SELECT student_id FROM users WHERE id=?", (user_id,)
        ).fetchone()
        return row["student_id"] if row else None

    def close(self):
        self.conn.close()
