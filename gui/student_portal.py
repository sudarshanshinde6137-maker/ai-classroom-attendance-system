"""
Student Portal - Read-only view for logged-in students showing their own attendance
"""

import customtkinter as ctk
from tkinter import ttk
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import DatabaseManager

PAGE_BG   = "#08111E"
PANEL_BG  = "#0F172A"
PANEL_ALT = "#162238"
BORDER    = "#26364A"
ACCENT    = "#22D3EE"
ACCENT_DK = "#0F4C5C"
TEXT_MUTED = "#94A3B8"
SUCCESS   = "#22C55E"
DANGER    = "#F87171"
WARNING   = "#FBBF24"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class StudentPortal:
    def __init__(self, user: dict):
        self.user = user
        self.db = DatabaseManager()
        self.student_id = user.get("student_id")

        self.root = ctk.CTk()
        self.root.title(f"My Attendance — {user['username']}")
        self.root.geometry("900x650")
        self.root.minsize(750, 550)
        self.root.configure(fg_color=PAGE_BG)
        self._center()
        self._build_ui()
        self._load_data()
        self._auto_refresh()

    def _center(self):
        self.root.update_idletasks()
        w, h = 900, 650
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # ── Top bar ───────────────────────────────────────────────────────────
        topbar = ctk.CTkFrame(self.root, height=70, corner_radius=0, fg_color=PANEL_BG,
                               border_width=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(left, text="🎓  My Attendance Portal",
                     font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
                     text_color="white").pack(anchor="w")
        ctk.CTkLabel(left, text=f"Logged in as: {self.user['username']}",
                     font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color=TEXT_MUTED).pack(anchor="w")

        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.pack(side="right", padx=20)
        self.clock_label = ctk.CTkLabel(right, text="",
                                         font=ctk.CTkFont(family="Segoe UI", size=12),
                                         text_color=TEXT_MUTED)
        self.clock_label.pack()
        self._update_clock()

        ctk.CTkButton(right, text="Logout", width=80, height=32,
                      fg_color=DANGER, hover_color="#B91C1C",
                      font=ctk.CTkFont(size=12),
                      command=self._logout).pack(pady=(4, 0))

        # ── Main scroll area ──────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self.root, fg_color=PAGE_BG,
                                         scrollbar_button_color=BORDER)
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # Student info card
        info_card = ctk.CTkFrame(scroll, fg_color=PANEL_BG, corner_radius=16,
                                  border_width=1, border_color=BORDER)
        info_card.pack(fill="x", pady=(0, 14))

        student = self.db.get_student_by_id(self.student_id) if self.student_id else None
        if student:
            ic_row = ctk.CTkFrame(info_card, fg_color="transparent")
            ic_row.pack(fill="x", padx=20, pady=16)
            ctk.CTkLabel(ic_row, text="👤", font=ctk.CTkFont(size=36)).pack(side="left", padx=(0, 14))
            ic_text = ctk.CTkFrame(ic_row, fg_color="transparent")
            ic_text.pack(side="left")
            ctk.CTkLabel(ic_text, text=student["name"],
                         font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
                         text_color="white").pack(anchor="w")
            ctk.CTkLabel(ic_text,
                         text=f"Roll: {student['roll_no']}   •   PRN: {student['prn']}",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=TEXT_MUTED).pack(anchor="w")
        else:
            ctk.CTkLabel(info_card, text="⚠  Student profile not linked to this account.",
                         text_color=WARNING).pack(padx=20, pady=16)

        # Stats row
        stats_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 14))

        self.stat_total  = ctk.StringVar(value="0")
        self.stat_pres   = ctk.StringVar(value="0")
        self.stat_abs    = ctk.StringVar(value="0")
        self.stat_pct    = ctk.StringVar(value="0%")

        for title, var, color in [
            ("Total Classes", self.stat_total,  ACCENT),
            ("Present",       self.stat_pres,   SUCCESS),
            ("Absent",        self.stat_abs,    DANGER),
            ("Attendance %",  self.stat_pct,    WARNING),
        ]:
            c = ctk.CTkFrame(stats_row, fg_color=PANEL_BG, corner_radius=14,
                              border_width=1, border_color=BORDER)
            c.pack(side="left", expand=True, fill="x", padx=5)
            ctk.CTkFrame(c, height=4, corner_radius=999, fg_color=color).pack(fill="x", padx=12, pady=(10, 6))
            ctk.CTkLabel(c, text=title, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=12)
            ctk.CTkLabel(c, textvariable=var,
                         font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
                         text_color="white").pack(anchor="w", padx=12, pady=(0, 10))

        # Subject filter label
        subj_hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        subj_hdr.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(subj_hdr, text="Attendance Records",
                     font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                     text_color="white").pack(side="left")
        ctk.CTkButton(subj_hdr, text="🔄 Refresh", width=90, height=30,
                      fg_color=ACCENT_DK, hover_color="#0B9FBF",
                      command=self._load_data).pack(side="right")

        # Records table
        style = ttk.Style()
        try:
            style.theme_use("default")
        except Exception:
            pass
        style.configure("SP.Treeview", background=PANEL_BG, foreground="white",
                         fieldbackground=PANEL_BG, borderwidth=0, rowheight=32,
                         font=("Segoe UI", 11))
        style.configure("SP.Treeview.Heading", background="#132033", foreground="white",
                         relief="flat", font=("Segoe UI", 11, "bold"))
        style.map("SP.Treeview", background=[("selected", ACCENT_DK)],
                  foreground=[("selected", "white")])

        self.tree = ttk.Treeview(scroll,
                                  columns=("Date", "Subject", "Session", "Time", "Status"),
                                  show="headings", height=14, style="SP.Treeview")
        for col, w in (("Date", 110), ("Subject", 220), ("Session", 100),
                        ("Time", 90), ("Status", 90)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True)

    def _load_data(self):
        if not self.student_id:
            return

        # Get ALL attendance for this student
        rows = self.db.conn.execute("""
            SELECT date, subject, session, time, status
            FROM attendance
            WHERE student_id = ?
            ORDER BY date DESC, subject
        """, (self.student_id,)).fetchall()

        self.tree.delete(*self.tree.get_children())
        present = 0
        for r in rows:
            status = r[4] or "Present"
            tag = "pres" if status == "Present" else "abs"
            self.tree.insert("", "end",
                              values=(r[0], r[1] or "General", r[2] or "-", r[3] or "-", status),
                              tags=(tag,))
            if status == "Present":
                present += 1

        total = len(rows)
        absent = total - present
        pct = round(present / total * 100, 1) if total else 0

        self.stat_total.set(str(total))
        self.stat_pres.set(str(present))
        self.stat_abs.set(str(absent))
        self.stat_pct.set(f"{pct:.1f}%")

        # Color rows
        self.tree.tag_configure("pres", foreground="#86EFAC")
        self.tree.tag_configure("abs",  foreground="#FCA5A5")

    def _auto_refresh(self):
        try:
            self._load_data()
        except Exception:
            pass
        self.root.after(10000, self._auto_refresh)

    def _update_clock(self):
        self.clock_label.configure(text=datetime.now().strftime("%a, %b %d  %H:%M:%S"))
        self.root.after(1000, self._update_clock)

    def _logout(self):
        self.db.close()
        self.root.destroy()
        # Re-launch login
        from gui.login_window import LoginWindow
        from gui.student_portal import StudentPortal

        def on_login(user):
            if user["role"] == "teacher":
                from gui.app import AttendanceApp
                app = AttendanceApp(user=user)
                app.run()
            else:
                portal = StudentPortal(user)
                portal.run()

        lw = LoginWindow(on_success=on_login)
        lw.run()

    def run(self):
        self.root.mainloop()
