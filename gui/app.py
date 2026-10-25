"""
Main GUI Application - CustomTkinter-based interface for the Attendance System
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import shutil
from datetime import datetime, timedelta
import sys
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Internal imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import DatabaseManager
from core.face_engine import FaceEngine
from core.reports import (export_excel, export_pdf, export_csv,
                          export_defaulters_report, export_monthly_matrix)
from core.notifications import generate_absentee_messages
from core.auth import AuthManager

# Matplotlib for Dashboard
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

PHOTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "student_photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

# ── CustomTkinter Setup ───────────────────────────────────────────────────────
ctk.set_appearance_mode("Dark")  # System, Dark, Light
ctk.set_default_color_theme("blue")

# Accent color choices for a cleaner, modern look
ACCENT = "#8B5CF6"       # Vibrant purple accent for a more premium look
ACCENT_DARK = "#6D28D9"
PAGE_BG = "#030712"      # Deep, modern dark background
PANEL_BG = "#111827"
PANEL_ALT = "#1F2937"
BORDER = "#374151"
TEXT_MUTED = "#9CA3AF"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
SUBJECTS = [
    "Mathematics",
    "Python Programming Lab",
    "Java Programming Lab",
    "Principles of Communication Lab",
    "M&M Lab",
]

class AttendanceApp:
    def __init__(self, user: dict = None):
        self.root = ctk.CTk()
        self.root.title("AI Classroom Attendance Studio v2")
        self.root.geometry("1280x800")
        self.root.minsize(1100, 720)
        self.root.configure(fg_color=PAGE_BG)

        self._user = user or {"username": "Teacher", "role": "teacher", "id": None}
        self.db = DatabaseManager()
        self.auth = AuthManager()
        self.engine = FaceEngine()
        self.current_session = ctk.StringVar(value="Morning")
        self.current_subject = ctk.StringVar(value=SUBJECTS[0])
        self.tolerance = ctk.DoubleVar(value=0.55)
        self._selected_photo = ""
        self._photo_ctk_image = None

        self._setup_fonts()
        self._build_ui()
        self._ensure_face_engine_ready()
        self._current_tab = "dash"
        self._load_dashboard()
        self._auto_refresh()  # start 5-second auto-refresh loop

    def _ensure_face_engine_ready(self):
        """Rebuild face encodings from saved student photos when needed."""
        if getattr(self.engine, "trained_count", 0) > 0:
            return

        students = [
            student for student in self.db.get_all_students()
            if student.get("photo_path") and os.path.exists(student["photo_path"])
        ]

        if not students:
            if hasattr(self, "footer_label"):
                self.footer_label.configure(text="No student photos found for live recognition")
            return

        try:
            success, failed = self.engine.retrain_all(students)
            if hasattr(self, "footer_label"):
                self.footer_label.configure(
                    text=f"Face encodings ready: {success} trained, {failed} skipped"
                )
        except Exception as e:
            if hasattr(self, "footer_label"):
                self.footer_label.configure(text=f"Live recognition setup failed: {e}")

    def _setup_fonts(self):
        self.h1 = ctk.CTkFont(family="Segoe UI", size=26, weight="bold")
        self.h2 = ctk.CTkFont(family="Segoe UI", size=19, weight="bold")
        self.body = ctk.CTkFont(family="Segoe UI", size=13)
        self.small = ctk.CTkFont(family="Segoe UI", size=11)

    def _build_ui(self):
        # ── Sidebar (restyled)
        self.sidebar_frame = ctk.CTkFrame(self.root, width=250, corner_radius=0, fg_color="#0A1A2A")
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        ctk.CTkFrame(self.sidebar_frame, height=6, corner_radius=0, fg_color=ACCENT).pack(fill="x")

        # Title
        # App logo/title area
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=ACCENT_DARK, corner_radius=0)
        logo_frame.pack(fill="x", pady=(18, 12), padx=12)
        ctk.CTkLabel(logo_frame, text="🎓", font=ctk.CTkFont(size=28)).pack(side="left", padx=(6, 10))
        title_stack = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_stack.pack(side="left")
        ctk.CTkLabel(title_stack, text="AI Attendance", font=ctk.CTkFont(size=18, weight="bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(title_stack, text="Smart classroom management", font=ctk.CTkFont(size=11), text_color="#C7F9FF").pack(anchor="w")

        # Nav Buttons
        self.nav_btns = []
        nav_items = [
            ("📊  Dashboard",     "dash"),
            ("👤  Register",      "reg"),
            ("📸  Mark Attend.",  "mark"),
            ("📋  Records",       "rec"),
            ("👥  Students",      "stu"),
            ("📈  Analytics",     "analytics"),
            ("🔐  Users",         "users"),
        ]
        
        for text, tab_id in nav_items:
            btn = ctk.CTkButton(self.sidebar_frame, text=text, font=self.body,
                                anchor="w", fg_color="transparent", text_color=("white"),
                                hover_color="#12324A",
                                corner_radius=12,
                                height=44,
                                command=lambda t=tab_id: self._select_tab(t))
            btn.pack(fill="x", padx=12, pady=6)
            self.nav_btns.append((tab_id, btn))

        # Session & Settings
        ctk.CTkLabel(self.sidebar_frame, text="Session", font=self.small, text_color=TEXT_MUTED).pack(pady=(30, 0), anchor="w", padx=20)
        self.session_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Morning", "Afternoon", "Evening"],
                              variable=self.current_session, font=self.body, fg_color=PANEL_BG, button_color=ACCENT_DARK, button_hover_color="#123C4C")
        self.session_menu.pack(padx=20, pady=(5, 10), fill="x")

        ctk.CTkLabel(self.sidebar_frame, text="Default Subject", font=self.small, text_color=TEXT_MUTED).pack(pady=(10, 0), anchor="w", padx=20)
        self.subject_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=SUBJECTS,
            variable=self.current_subject,
            font=self.body,
            fg_color=PANEL_BG,
            button_color=ACCENT_DARK,
            button_hover_color="#123C4C",
        )
        self.subject_menu.pack(padx=20, pady=(5, 10), fill="x")

        ctk.CTkLabel(self.sidebar_frame, text="Tolerance (Strict ⇌ Loose)", font=self.small, text_color=TEXT_MUTED).pack(pady=(15, 0), anchor="w", padx=20)
        self.tol_slider = ctk.CTkSlider(self.sidebar_frame, from_=0.3, to=0.7, variable=self.tolerance, progress_color=ACCENT, button_color=ACCENT)
        self.tol_slider.pack(padx=20, pady=(5, 10), fill="x")

        # Bottom items
        ctk.CTkLabel(self.sidebar_frame, text="").pack(fill="y", expand=True) # spacer
        
        self.theme_switch = ctk.CTkSwitch(self.sidebar_frame, text="Dark Mode", command=self._toggle_theme, font=self.small, progress_color=ACCENT, button_color=ACCENT)
        self.theme_switch.pack(pady=10, padx=20, anchor="w")
        self.theme_switch.select()

        # Small helper card for extra polish and guidance
        tips_card = ctk.CTkFrame(self.sidebar_frame, corner_radius=14, fg_color=PANEL_BG, border_width=1, border_color=BORDER)
        tips_card.pack(fill="x", padx=16, pady=(8, 14))
        ctk.CTkLabel(tips_card, text="Quick Tips", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="white").pack(anchor="w", padx=12, pady=(12, 4))
        ctk.CTkLabel(tips_card, text="• Register a clear front photo\n• Use webcam in good light\n• Check records after marking", font=self.small, text_color=TEXT_MUTED, justify="left").pack(anchor="w", padx=12, pady=(0, 12))

        # ── Main Content Area with top bar
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=18, fg_color=PAGE_BG)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=(18, 20), pady=18)

        # Top bar
        topbar = ctk.CTkFrame(self.main_frame, height=78, corner_radius=18, fg_color=PANEL_BG, border_width=1, border_color=BORDER)
        topbar.pack(fill="x", pady=(0,12), padx=6)
        left_block = ctk.CTkFrame(topbar, fg_color="transparent")
        left_block.pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(left_block, text="AI Classroom Attendance Studio", font=self.h2, text_color="white").pack(anchor="w")
        ctk.CTkLabel(left_block, text="Track attendance faster with a polished, modern interface.", font=self.small, text_color=TEXT_MUTED).pack(anchor="w")

        right_block = ctk.CTkFrame(topbar, fg_color="transparent")
        right_block.pack(side="right", padx=16)

        # Logout button
        ctk.CTkButton(
            right_block, text="Logout", width=76, height=30,
            fg_color=DANGER, hover_color="#B91C1C",
            font=self.small, corner_radius=8,
            command=self._logout
        ).pack(side="right", padx=(6, 0), pady=18)

        # Web Studio button
        ctk.CTkButton(
            right_block, text="🌐 Web Studio", width=108, height=30,
            fg_color=ACCENT_DARK, hover_color="#7C3AED",
            font=self.small, corner_radius=8,
            command=self._launch_web_studio
        ).pack(side="right", padx=(6, 4), pady=18)

        # Logged-in user chip
        user_chip = ctk.CTkFrame(right_block, corner_radius=999, fg_color="#0F2E1A",
                                  border_width=1, border_color="#14532D")
        user_chip.pack(side="right", padx=(8, 4), pady=12)
        role_icon = "🎓" if self._user.get("role") == "teacher" else "👨‍🎓"
        ctk.CTkLabel(user_chip, text=role_icon, font=self.body).pack(side="left", padx=(10, 4), pady=8)
        ctk.CTkLabel(user_chip, text=self._user.get("username", "User"),
                     font=self.body, text_color="white").pack(side="left", padx=(0, 10), pady=8)

        session_chip = ctk.CTkFrame(right_block, corner_radius=999, fg_color=PANEL_ALT, border_width=1, border_color=BORDER)
        session_chip.pack(side="right", padx=(8, 0), pady=12)
        ctk.CTkLabel(session_chip, text="Session", font=self.small, text_color=TEXT_MUTED).pack(side="left", padx=(12, 6), pady=8)
        ctk.CTkLabel(session_chip, textvariable=self.current_session, font=self.body, text_color="white").pack(side="left", padx=(0, 12), pady=8)

        status_chip = ctk.CTkFrame(right_block, corner_radius=999, fg_color="#0F2E2D", border_width=1, border_color="#14532D")
        status_chip.pack(side="right", pady=12)
        ctk.CTkLabel(status_chip, text="●", font=self.body, text_color=SUCCESS).pack(side="left", padx=(12, 4), pady=8)
        ctk.CTkLabel(status_chip, text="Live", font=self.body, text_color="white").pack(side="left", padx=(0, 12), pady=8)

        # Footer strip (pinned at bottom of main_frame)
        self.footer = ctk.CTkFrame(self.main_frame, height=36, corner_radius=0, fg_color=PANEL_BG, border_width=0)
        self.footer.pack(side="bottom", fill="x", padx=0, pady=0)
        self.footer_label = ctk.CTkLabel(self.footer, text="Ready for live attendance", font=self.small, text_color=TEXT_MUTED)
        self.footer_label.pack(side="left", padx=14, pady=6)
        self.footer_time = ctk.CTkLabel(self.footer, text="", font=self.small, text_color=TEXT_MUTED)
        self.footer_time.pack(side="right", padx=14, pady=6)
        self._update_footer_clock()

        # Scrollable content container
        self.scroll_area = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=ACCENT_DARK,
            corner_radius=0,
        )
        self.scroll_area.pack(fill="both", expand=True, padx=0, pady=0)

        # Content frames (children of scroll_area now)
        self.frames = {
            "dash":      ctk.CTkFrame(self.scroll_area, fg_color="transparent"),
            "reg":       ctk.CTkFrame(self.scroll_area, fg_color="transparent"),
            "mark":      ctk.CTkFrame(self.scroll_area, fg_color="transparent"),
            "rec":       ctk.CTkFrame(self.scroll_area, fg_color="transparent"),
            "stu":       ctk.CTkFrame(self.scroll_area, fg_color="transparent"),
            "analytics": ctk.CTkFrame(self.scroll_area, fg_color="transparent"),
            "users":     ctk.CTkFrame(self.scroll_area, fg_color="transparent"),
        }

        self._build_dashboard(self.frames["dash"])
        self._build_register(self.frames["reg"])
        self._build_mark_attendance(self.frames["mark"])
        self._build_records(self.frames["rec"])
        self._build_students(self.frames["stu"])
        self._build_analytics(self.frames["analytics"])
        self._build_users(self.frames["users"])

        self._select_tab("dash")

    def _select_tab(self, tab_id):
        self._current_tab = tab_id
        for tid, btn in self.nav_btns:
            if tid == tab_id:
                btn.configure(fg_color="#0B9FBF", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="white")
        for tid, f in self.frames.items():
            if tid == tab_id:
                f.pack(fill="both", expand=True)
                if tid == "dash":      self._load_dashboard()
                if tid == "stu":       self._load_students()
                if tid == "rec":       self._load_records()
                if tid == "analytics": self._load_analytics()
                if tid == "users":     self._load_users()
            else:
                f.pack_forget()

    def _auto_refresh(self):
        """Auto-refresh the active tab every 5 seconds."""
        try:
            tab = getattr(self, "_current_tab", "dash")
            if tab == "dash":
                self._load_dashboard()
            elif tab == "rec":
                self._load_records()
            elif tab == "analytics":
                self._load_analytics()
        except Exception:
            pass
        self.root.after(5000, self._auto_refresh)

    def _toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    # ── Dashboard ─────────────────────────────────────────────────────────────
    def _build_dashboard(self, f):
        header = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=BORDER)
        header.pack(fill="x", pady=(0, 18), padx=6)

        header_left = ctk.CTkFrame(header, fg_color="transparent")
        header_left.pack(side="left", padx=18, pady=16)
        ctk.CTkLabel(header_left, text="Dashboard Overview", font=self.h1, text_color=ACCENT).pack(anchor="w")
        ctk.CTkLabel(header_left, text="A quick snapshot of attendance activity and trends.", font=self.body, text_color=TEXT_MUTED).pack(anchor="w", pady=(2,0))

        header_right = ctk.CTkFrame(header, fg_color="transparent")
        header_right.pack(side="right", padx=18, pady=16)
        self.dt_label = ctk.CTkLabel(header_right, text="", font=self.body, text_color=TEXT_MUTED)
        self.dt_label.pack(anchor="e")
        self._update_clock()

        # Hero / insights strip
        self.dashboard_insights = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=18, border_width=1, border_color=BORDER)
        self.dashboard_insights.pack(fill="x", padx=6, pady=(0, 16))

        insights_left = ctk.CTkFrame(self.dashboard_insights, fg_color="transparent")
        insights_left.pack(side="left", fill="both", expand=True, padx=18, pady=16)
        ctk.CTkLabel(insights_left, text="Ready to take attendance fast.", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(insights_left, text="Use webcam mode for live recognition or upload a classroom photo when you need a quick batch check.",
                font=self.body, text_color=TEXT_MUTED, wraplength=520, justify="left").pack(anchor="w", pady=(4, 0))

        insights_right = ctk.CTkFrame(self.dashboard_insights, fg_color="transparent")
        insights_right.pack(side="right", padx=18, pady=16)
        self.session_card = ctk.CTkFrame(insights_right, corner_radius=14, fg_color=PANEL_ALT, border_width=1, border_color=BORDER)
        self.session_card.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(self.session_card, text="Current session", font=self.small, text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(self.session_card, textvariable=self.current_session, font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="white").pack(anchor="w", padx=12, pady=(0, 10))

        self.tolerance_card = ctk.CTkFrame(insights_right, corner_radius=14, fg_color=PANEL_ALT, border_width=1, border_color=BORDER)
        self.tolerance_card.pack(fill="x")
        ctk.CTkLabel(self.tolerance_card, text="Face tolerance", font=self.small, text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(self.tolerance_card, text=f"{self.tolerance.get():.2f}", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="white").pack(anchor="w", padx=12, pady=(0, 10))

        self.subject_summary = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=18, border_width=1, border_color=BORDER)
        self.subject_summary.pack(fill="x", padx=6, pady=(0, 16))
        ctk.CTkLabel(self.subject_summary, text="Subject-wise Attendance", font=self.h2, text_color="white").pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(self.subject_summary, text="Daily percentage view for each default subject.", font=self.small, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 12))
        self.subject_cards_frame = ctk.CTkFrame(self.subject_summary, fg_color="transparent")
        self.subject_cards_frame.pack(fill="x", padx=12, pady=(0, 14))
        self.subject_stat_vars = {}
        self.subject_cards = {}
        for idx, subject in enumerate(SUBJECTS):
            var = ctk.StringVar(value="0%")
            self.subject_stat_vars[subject] = var
            card = ctk.CTkFrame(self.subject_cards_frame, corner_radius=14, fg_color=PANEL_ALT, border_width=1, border_color=BORDER)
            card.grid(row=idx // 5, column=idx % 5, padx=6, pady=6, sticky="nsew")
            ctk.CTkLabel(card, text=subject, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="white", wraplength=120, justify="left").pack(anchor="w", padx=10, pady=(10, 2))
            ctk.CTkLabel(card, textvariable=var, font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"), text_color=ACCENT).pack(anchor="w", padx=12, pady=(0, 2))
            ctk.CTkLabel(card, text="present today", font=self.small, text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(0, 10))
            self.subject_cards[subject] = card
        for column in range(5):
            self.subject_cards_frame.grid_columnconfigure(column, weight=1)

        self.subject_table_frame = ctk.CTkFrame(self.subject_summary, fg_color="transparent")
        self.subject_table_frame.pack(fill="x", padx=12, pady=(0, 14))
        self.subject_table = ttk.Treeview(
            self.subject_table_frame,
            columns=("Subject", "Present", "Total", "Percentage"),
            show="headings",
            height=5,
        )
        for col, width in (("Subject", 210), ("Present", 90), ("Total", 90), ("Percentage", 110)):
            self.subject_table.heading(col, text=col)
            self.subject_table.column(col, width=width, anchor="center")
        self.subject_table.pack(fill="x", expand=True)

        # Quick actions panel
        quick_actions = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=18, border_width=1, border_color=BORDER)
        quick_actions.pack(fill="x", padx=6, pady=(0, 16))
        ctk.CTkLabel(quick_actions, text="Quick Actions", font=self.h2, text_color="white").pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(quick_actions, text="Jump straight into the most common tasks.", font=self.small, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 12))

        action_row = ctk.CTkFrame(quick_actions, fg_color="transparent")
        action_row.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(action_row, text="Register Student", fg_color=ACCENT_DARK, hover_color="#5B21B6", command=lambda: self._select_tab("reg")).pack(side="left", padx=(0, 10), expand=True, fill="x")
        ctk.CTkButton(action_row, text="Open Webcam", fg_color="#2563EB", hover_color="#1D4ED8", command=self._start_webcam).pack(side="left", padx=10, expand=True, fill="x")
        ctk.CTkButton(action_row, text="View Records", fg_color=PANEL_ALT, hover_color="#374151", command=lambda: self._select_tab("rec")).pack(side="left", padx=10, expand=True, fill="x")
        ctk.CTkButton(action_row, text="Generate Reports", fg_color="#059669", hover_color="#047857", command=lambda: self._select_tab("rec")).pack(side="left", padx=(10, 0), expand=True, fill="x")

        # Stats Row
        stats_frame = ctk.CTkFrame(f, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10, padx=6)
        
        self.stat_vars = {
            "total": ctk.StringVar(value="0"),
            "present": ctk.StringVar(value="0"),
            "absent": ctk.StringVar(value="0"),
            "pct": ctk.StringVar(value="0%")
        }

        self._stat_card(stats_frame, "Total", self.stat_vars["total"], ACCENT).pack(side="left", expand=True, fill="x", padx=5)
        self._stat_card(stats_frame, "Present", self.stat_vars["present"], SUCCESS).pack(side="left", expand=True, fill="x", padx=5)
        self._stat_card(stats_frame, "Absent", self.stat_vars["absent"], DANGER).pack(side="left", expand=True, fill="x", padx=5)
        self._stat_card(stats_frame, "Accuracy", self.stat_vars["pct"], WARNING).pack(side="left", expand=True, fill="x", padx=5)

        # Plot & Table Split
        split = ctk.CTkFrame(f, fg_color="transparent")
        split.pack(fill="both", expand=True, pady=15, padx=6)

        # Plot Region
        plot_frame = ctk.CTkFrame(split, corner_radius=18, fg_color=PANEL_BG, border_width=1, border_color=BORDER)
        plot_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(plot_frame, text="Attendance Trend (7 Days)", font=self.h2, text_color="white").pack(pady=(14, 4))
        ctk.CTkLabel(plot_frame, text="Weekly activity overview", font=self.small, text_color=TEXT_MUTED).pack(pady=(0, 8))
        
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.fig.patch.set_facecolor(PANEL_BG)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(PANEL_BG)
        self.ax.tick_params(colors='white')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)

        # Table Region
        table_frame = ctk.CTkFrame(split, width=320, corner_radius=18, fg_color=PANEL_BG, border_width=1, border_color=BORDER)
        table_frame.pack(side="right", fill="both")
        table_frame.pack_propagate(False)
        ctk.CTkLabel(table_frame, text="Today's Log", font=self.h2, text_color="white").pack(pady=(14, 2))
        ctk.CTkLabel(table_frame, text="Most recent attendance entries", font=self.small, text_color=TEXT_MUTED).pack(pady=(0, 8))
        
        # Using standard ttk treeview, styled for CTK
        self._style_treeview()
        
        self.dash_tree = ttk.Treeview(table_frame, columns=("Name", "Time", "Status"), show="headings", height=8)
        self.dash_tree.heading("Name", text="Name")
        self.dash_tree.heading("Time", text="Time")
        self.dash_tree.heading("Status", text="Status")
        self.dash_tree.column("Name", width=132)
        self.dash_tree.column("Time", width=72)
        self.dash_tree.column("Status", width=84)
        self.dash_tree.pack(fill="both", expand=True, padx=12, pady=12)

    def _stat_card(self, parent, title, var, color):
        card = ctk.CTkFrame(parent, corner_radius=18, fg_color=PANEL_BG, border_width=1, border_color=BORDER)
        accent_bar = ctk.CTkFrame(card, height=5, corner_radius=999, fg_color=color)
        accent_bar.pack(fill="x", padx=14, pady=(12, 8))
        ctk.CTkLabel(card, text=title, font=self.body, text_color=TEXT_MUTED).pack(anchor="w", padx=14)
        ctk.CTkLabel(card, textvariable=var, font=("Segoe UI", 28, "bold"), text_color="white").pack(anchor="w", padx=14, pady=(0, 12))
        return card

    def _load_dashboard(self):
        today = datetime.now().strftime("%Y-%m-%d")
        summary = self.db.get_summary(today)
        records = self.db.get_attendance_by_date(today)

        self.stat_vars["total"].set(str(summary["total"]))
        self.stat_vars["present"].set(str(summary["present"]))
        self.stat_vars["absent"].set(str(summary["absent"]))
        pct = (summary["present"] / summary["total"] * 100) if summary["total"] > 0 else 0
        self.stat_vars["pct"].set(f"{pct:.0f}%")

        subject_summary = self.db.get_subject_summary(today, SUBJECTS)
        for row in subject_summary:
            subject = row["subject"]
            if subject in self.subject_stat_vars:
                self.subject_stat_vars[subject].set(f"{row['percentage']:.1f}%")

        self.subject_table.delete(*self.subject_table.get_children())
        for row in subject_summary:
            self.subject_table.insert(
                "",
                "end",
                values=(row["subject"], row["present"], row["total"], f"{row['percentage']:.1f}%")
            )

        self.dash_tree.delete(*self.dash_tree.get_children())
        for r in records[:15]: # Show latest 15
            self.dash_tree.insert("", "end", values=(r["name"], r["time"], f"{r['status']} | {r.get('subject', 'General')}"))
            
        self._update_plot()

    def _update_plot(self):
        self.ax.clear()
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        # Use actual numbers or mock if none to show chart
        present = [12, 15, 14, 16, 15, 10, int(self.stat_vars["present"].get())]
        
        is_dark = self.theme_switch.get() == 1
        text_col = 'white' if is_dark else 'black'
        bg_col = '#2B2B2B' if is_dark else '#EBEBEB'
        
        self.fig.patch.set_facecolor(bg_col)
        self.ax.set_facecolor(bg_col)
        self.ax.tick_params(colors=text_col)
        
        self.ax.bar(days, present, color="#3B82F6", alpha=0.8)
        self.ax.set_ylabel('Present Count', color=text_col)
        self.canvas.draw()

    # ── Register ──────────────────────────────────────────────────────────────
    def _build_register(self, f):
        header = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=18, border_width=1, border_color=BORDER)
        header.pack(fill="x", padx=6, pady=(0, 16))
        ctk.CTkLabel(header, text="Register Student", font=self.h1, text_color=ACCENT).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(header, text="Add a student profile and train their face in a few simple steps.", font=self.body, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 16))
        
        card = ctk.CTkFrame(f, corner_radius=18, fg_color=PANEL_BG, border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=6, pady=10)
        
        self.reg_vars = {"name": ctk.StringVar(), "roll": ctk.StringVar(), "prn": ctk.StringVar()}
        
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(grid, text="Full Name", font=self.body, text_color=TEXT_MUTED).grid(row=0, column=0, sticky="w", pady=10, padx=10)
        ctk.CTkEntry(grid, textvariable=self.reg_vars["name"], width=250, placeholder_text="John Doe").grid(row=0, column=1)

        ctk.CTkLabel(grid, text="Roll / ID", font=self.body, text_color=TEXT_MUTED).grid(row=1, column=0, sticky="w", pady=10, padx=10)
        ctk.CTkEntry(grid, textvariable=self.reg_vars["roll"], width=250).grid(row=1, column=1)

        ctk.CTkLabel(grid, text="PRN", font=self.body, text_color=TEXT_MUTED).grid(row=2, column=0, sticky="w", pady=10, padx=10)
        ctk.CTkEntry(grid, textvariable=self.reg_vars["prn"], width=250).grid(row=2, column=1)
        
        ctk.CTkLabel(grid, text="Photo", font=self.body, text_color=TEXT_MUTED).grid(row=3, column=0, sticky="w", pady=10, padx=10)

        photo_col = ctk.CTkFrame(grid, fg_color="transparent")
        photo_col.grid(row=3, column=1, sticky="w")
        btn_row = ctk.CTkFrame(photo_col, fg_color="transparent")
        btn_row.pack(anchor="w")
        self.photo_label = ctk.CTkLabel(btn_row, text="No photo selected", text_color="gray")
        self.photo_label.pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="📁 Browse", width=100, fg_color=PANEL_ALT,
                      hover_color="#223149", command=self._browse_photo).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="📷 Capture", width=100, fg_color="#1D4ED8",
                      hover_color="#1E40AF", command=self._capture_photo_for_reg).pack(side="left")
        # Photo preview
        self.photo_preview = ctk.CTkLabel(photo_col, text="", width=140, height=140,
                                          fg_color=PANEL_ALT, corner_radius=10,
                                          text_color=TEXT_MUTED)
        self.photo_preview.pack(anchor="w", pady=(8, 0))
        self.photo_preview.configure(text="No image")

        actions = ctk.CTkFrame(f, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=20)
        ctk.CTkButton(actions, text="✅  Register Student", fg_color=SUCCESS, hover_color="#059669",
                      height=40, font=self.body, command=self._register_student).pack(side="left", padx=5)
        self.reg_status = ctk.CTkLabel(actions, text="", text_color=TEXT_MUTED)
        self.reg_status.pack(side="left", padx=20)

    def _browse_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp"), ("All files", "*.*")])
        if path:
            self.photo_label.configure(text=os.path.basename(path))
            self._selected_photo = path
            self._show_photo_preview(path)

    def _show_photo_preview(self, path):
        if not PIL_AVAILABLE:
            return
        try:
            img = Image.open(path)
            img.thumbnail((140, 140), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            self._photo_ctk_image = ctk_img  # keep reference
            self.photo_preview.configure(image=ctk_img, text="")
        except Exception as e:
            self.photo_preview.configure(text=f"Preview error: {e}")

    def _capture_photo_for_reg(self):
        """Open webcam briefly to snap a photo for registration in the background."""
        self.reg_status.configure(text="Opening camera & capturing...", text_color=WARNING)
        
        def capture_task():
            try:
                import cv2
                import time
                
                cap = None
                for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY):
                    cap = cv2.VideoCapture(0, backend)
                    if cap.isOpened():
                        break
                
                if cap is None or not cap.isOpened():
                    cap = cv2.VideoCapture(0)

                if not cap.isOpened():
                    self.root.after(0, lambda: messagebox.showerror("Camera", "Could not open webcam."))
                    self.root.after(0, lambda: self.reg_status.configure(text="Capture failed", text_color="#EF4444"))
                    return
                
                # Warm up the camera to adjust exposure/focus
                for _ in range(10):
                    cap.read()
                    time.sleep(0.05)
                    
                ret, frame = cap.read()
                cap.release()
                
                if not ret:
                    self.root.after(0, lambda: messagebox.showerror("Camera", "Failed to capture frame."))
                    self.root.after(0, lambda: self.reg_status.configure(text="Capture failed", text_color="#EF4444"))
                    return
                    
                snap_path = os.path.join(PHOTOS_DIR, f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                cv2.imwrite(snap_path, frame)
                
                def update_ui():
                    self.photo_label.configure(text=os.path.basename(snap_path))
                    self._selected_photo = snap_path
                    self._show_photo_preview(snap_path)
                    self.reg_status.configure(text="Photo captured from webcam!", text_color="#10B981") # SUCCESS color
                
                self.root.after(0, update_ui)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Capture Error", str(e)))
                self.root.after(0, lambda: self.reg_status.configure(text="Capture error", text_color="#EF4444"))

        import threading
        threading.Thread(target=capture_task, daemon=True).start()

    def _register_student(self):
        name = self.reg_vars["name"].get()
        roll = self.reg_vars["roll"].get()
        prn = self.reg_vars["prn"].get()
        photo = getattr(self, "_selected_photo", "")

        if not all([name, roll, prn, photo]):
            self.reg_status.configure(text="Missing required fields!", text_color="#EF4444")
            return

        ext = os.path.splitext(photo)[1]
        dest_path = os.path.join(PHOTOS_DIR, f"{roll}_{prn}{ext}".replace(" ", "_"))
        shutil.copy2(photo, dest_path)

        try:
            self.reg_status.configure(text="Encoding face...", text_color="#F59E0B")
            self.root.update()
            
            sid = self.db.add_student(name, roll, prn, dest_path)
            if self.engine.encode_student(sid, name, dest_path):
                self.reg_status.configure(text=f"Success! {name} registered.", text_color="#10B981")
                for v in self.reg_vars.values(): v.set("")
                self.photo_label.configure(text="No photo selected")
                self._selected_photo = ""
            else:
                self.reg_status.configure(text="Face not found. Try another photo.", text_color="#EF4444")
        except Exception as e:
            self.reg_status.configure(text=f"Error: {e}", text_color="#EF4444")

    # ── Mark Attendance ───────────────────────────────────────────────────────
    def _build_mark_attendance(self, f):
        header = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=18, border_width=1, border_color=BORDER)
        header.pack(fill="x", padx=6, pady=(0, 16))
        ctk.CTkLabel(header, text="Mark Attendance", font=self.h1, text_color=ACCENT).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(header, text="Use live webcam or a group photo to capture attendance instantly.", font=self.body, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 16))

        subject_bar = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=BORDER)
        subject_bar.pack(fill="x", padx=6, pady=(0, 16))
        ctk.CTkLabel(subject_bar, text="Subject", font=self.small, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(12, 0))
        ctk.CTkOptionMenu(subject_bar, values=SUBJECTS, variable=self.current_subject, font=self.body, fg_color=PANEL_ALT, button_color=ACCENT_DARK, button_hover_color="#123C4C").pack(anchor="w", padx=18, pady=(6, 14))
        
        controls = ctk.CTkFrame(f, fg_color="transparent")
        controls.pack(fill="x", pady=10, padx=6)
        
        ctk.CTkButton(controls, text="📸 Live Webcam Mode", font=self.h2, height=62, corner_radius=14,
                      fg_color="#2563EB", hover_color="#1D4ED8", command=self._start_webcam).pack(side="left", padx=10, expand=True, fill="x")
        ctk.CTkButton(controls, text="📁 Upload Group Photo", font=self.h2, height=62, corner_radius=14,
                      fg_color=SUCCESS, hover_color="#059669", command=self._upload_photo).pack(side="left", padx=10, expand=True, fill="x")

        self.mark_res = ctk.CTkLabel(f, text="Select an option above to mark attendance.", font=self.body, text_color=TEXT_MUTED)
        self.mark_res.pack(pady=40)

    def _start_webcam(self):
        try:
            self._ensure_face_engine_ready()
            if getattr(self.engine, "trained_count", 0) == 0:
                messagebox.showerror(
                    "Webcam Error",
                    "No trained face encodings are available. Register students with photos first."
                )
                return

            from gui.webcam_window import WebcamWindow
            WebcamWindow(
                self.root, self.db, self.engine,
                self.current_session.get(),
                self.current_subject.get(),
                self.tolerance.get(),
                on_close=self._load_dashboard
            )
        except Exception as e:
            messagebox.showerror("Webcam Error", f"Could not start webcam:\n{e}")

    def _upload_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")])
        if not path: return
        self.mark_res.configure(text="Processing photo...", text_color="#F59E0B")
        self.root.update()
        
        try:
            results = self.engine.recognize_faces(path, self.tolerance.get())
            marked = 0
            for r in results:
                if r["recognized"]:
                    if self.db.mark_attendance(r["student_id"], self.current_session.get(), self.current_subject.get()):
                        marked += 1
            self.mark_res.configure(text=f"Done! Marked {marked} students present from photo.", text_color="#10B981")
            self._load_dashboard()
        except Exception as e:
             self.mark_res.configure(text=f"Error: {e}", text_color="#EF4444")

    # ── Records & Students ────────────────────────────────────────────────────
    def _build_records(self, f):
        header = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=18, border_width=1, border_color=BORDER)
        header.pack(fill="x", padx=6, pady=(0, 16))
        ctk.CTkLabel(header, text="Attendance Records", font=self.h1, text_color=ACCENT).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(header, text="A searchable view of all recorded attendance entries.", font=self.body, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 16))

        action_bar = ctk.CTkFrame(f, fg_color="transparent")
        action_bar.pack(fill="x", padx=6, pady=(0, 10))
        ctk.CTkButton(action_bar, text="📊 Export Excel", fg_color=ACCENT_DARK, hover_color="#123C4C", command=self._export_excel).pack(side="left", padx=(0, 6))
        ctk.CTkButton(action_bar, text="📄 Export PDF",   fg_color="#2563EB",  hover_color="#1D4ED8", command=self._export_pdf).pack(side="left", padx=6)
        ctk.CTkButton(action_bar, text="📁 Export CSV",   fg_color=PANEL_ALT,  hover_color="#223149", command=self._export_csv).pack(side="left", padx=6)
        ctk.CTkButton(action_bar, text="⚠️ Defaulters (<75%)", fg_color=DANGER, hover_color="#B91C1C", command=self._export_defaulters).pack(side="left", padx=6)
        ctk.CTkButton(action_bar, text="📅 Monthly Matrix", fg_color="#4F46E5", hover_color="#4338CA", command=self._export_monthly_matrix).pack(side="left", padx=6)
        ctk.CTkButton(action_bar, text="📢 Notify Absentees", fg_color="#10B981", hover_color="#059669", command=self._notify_absentees_dialog).pack(side="left", padx=6)
        ctk.CTkButton(action_bar, text="📧 Email",        fg_color="#F59E0B",  hover_color="#D97706", command=self._email_records).pack(side="left", padx=6)
        ctk.CTkButton(action_bar, text="🔄 Refresh",      fg_color="#0F4C5C",  hover_color="#0B9FBF", command=self._load_records).pack(side="right", padx=6)

        # Search bar
        search_bar = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=12, border_width=1, border_color=BORDER)
        search_bar.pack(fill="x", padx=6, pady=(0, 10))
        ctk.CTkLabel(search_bar, text="🔍", font=self.body).pack(side="left", padx=(12, 4), pady=8)
        self.rec_search_var = ctk.StringVar()
        self.rec_search_var.trace_add("write", lambda *_: self._filter_records())
        ctk.CTkEntry(search_bar, textvariable=self.rec_search_var, placeholder_text="Search by name, roll or subject…",
                     fg_color="transparent", border_width=0, font=self.body).pack(side="left", fill="x", expand=True, padx=4, pady=8)

        self._style_treeview()
        self.rec_tree = ttk.Treeview(f, columns=("Name", "Roll", "Date", "Status", "Session", "Subject"), show="headings")
        for col, w in (("Name",200),("Roll",100),("Date",100),("Status",80),("Session",90),("Subject",200)):
            self.rec_tree.heading(col, text=col)
            self.rec_tree.column(col, width=w)
        self.rec_tree.pack(fill="both", expand=True, padx=6, pady=6)
        self._all_records = []  # cache for search filtering

    def _load_records(self):
        self._all_records = self.db.get_all_attendance()
        # Arrange records by subject (ascending). Keep newest entries first within each subject.
        try:
            # First sort by date/time descending so newest come first (stable sort)
            self._all_records.sort(key=lambda r: (r.get("date", ""), r.get("time", "")), reverse=True)
            # Then sort by subject ascending while preserving the date ordering within each subject
            self._all_records.sort(key=lambda r: (r.get("subject", "General") or "").lower())
        except Exception:
            pass
        self._render_records(self._all_records)

    def _render_records(self, records):
        self.rec_tree.delete(*self.rec_tree.get_children())
        for r in records:
            self.rec_tree.insert("", "end", values=(r["name"], r["roll_no"], r["date"], r["status"], r["session"], r.get("subject", "General")))

    def _filter_records(self):
        q = self.rec_search_var.get().strip().lower()
        if not q:
            self._render_records(self._all_records)
            return
        filtered = [r for r in self._all_records
                    if q in r["name"].lower() or q in r["roll_no"].lower()
                    or q in r.get("subject","").lower()]
        self._render_records(filtered)

    def _export_records(self, export_func):
        today = datetime.now().strftime("%Y-%m-%d")
        records = self.db.get_attendance_by_date(today)
        summary = self.db.get_summary(today)
        try:
            if export_func is export_csv:
                path = export_func(records, today)
            else:
                path = export_func(records, today, summary)
            self.footer_label.configure(text=f"Exported report: {os.path.basename(path)}")
            messagebox.showinfo("Export complete", f"Saved to:\n{path}\n\nThe file will now open automatically.")
            try:
                os.startfile(path)
            except Exception:
                pass # ignore if no default app is set
        except Exception as e:
            messagebox.showerror("Export error", str(e))


    def _export_excel(self):
        self._export_records(export_excel)

    def _export_pdf(self):
        self._export_records(export_pdf)

    def _export_csv(self):
        self._export_records(export_csv)

    def _email_records(self):
        import urllib.parse
        import webbrowser
        today = datetime.now().strftime("%Y-%m-%d")
        summary = self.db.get_summary(today)
        records = self.db.get_attendance_by_date(today)
        
        body = f"Attendance Report for {today}\n"
        body += f"Total: {summary['total']} | Present: {summary['present']} | Absent: {summary['absent']}\n\n"
        body += "Records:\n"
        for r in records:
            body += f"- {r['name']} ({r['roll_no']}): {r['status']} ({r.get('subject', 'General')})\n"
            
        subject = urllib.parse.quote(f"Classroom Attendance Report - {today}")
        body_encoded = urllib.parse.quote(body)
        
        try:
            webbrowser.open(f"mailto:?subject={subject}&body={body_encoded}")
            self.footer_label.configure(text="Opened email client with report")
        except Exception as e:
            messagebox.showerror("Email Error", f"Could not open email client:\n{e}")

    def _notify_absentees_dialog(self):
        """Popup window to view absent students and dispatch WhatsApp/SMS/Email notices."""
        import webbrowser
        today = datetime.now().strftime("%Y-%m-%d")
        session = self.current_session.get()
        subject = self.current_subject.get()

        records = self.db.get_attendance_by_date(today, session=session, subject=subject)
        absent_students = [r for r in records if r["status"] == "Absent"]

        if not absent_students:
            messagebox.showinfo("Attendance 100%", f"🎉 Outstanding! All students are present for {subject} ({session} session).")
            return

        notices = generate_absentee_messages(absent_students, date=today, subject=subject, session=session)

        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"📢 Notify Absentees — {len(notices)} Absent")
        dialog.geometry("620x540")
        dialog.configure(fg_color=PAGE_BG)
        dialog.attributes("-topmost", True)

        hdr = ctk.CTkFrame(dialog, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(hdr, text=f"📢 Absentee Parent Alerts ({len(notices)} students)", font=self.h2, text_color=ACCENT).pack(anchor="w")
        ctk.CTkLabel(hdr, text=f"Session: {session} • Subject: {subject} • Date: {today}", font=self.small, text_color=TEXT_MUTED).pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent", scrollbar_button_color=BORDER, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        for n in notices:
            card = ctk.CTkFrame(scroll, fg_color=PANEL_BG, corner_radius=12, border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=6)

            c_top = ctk.CTkFrame(card, fg_color="transparent")
            c_top.pack(fill="x", padx=14, pady=(10, 4))
            ctk.CTkLabel(c_top, text=f"{n['name']} (Roll: {n['roll_no']})", font=ctk.CTkFont(size=13, weight="bold"), text_color="white").pack(side="left")
            ctk.CTkLabel(c_top, text="ABSENT", font=ctk.CTkFont(size=11, weight="bold"), text_color=DANGER).pack(side="right")

            preview = ctk.CTkLabel(card, text=n["sms_text"], font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, justify="left", wraplength=540)
            preview.pack(anchor="w", padx=14, pady=2)

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=14, pady=(6, 10))

            def _open_wa(url=n["whatsapp_url"]):
                webbrowser.open(url)

            def _copy(text=n["sms_text"]):
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.footer_label.configure(text="Copied absentee notification message")
                messagebox.showinfo("Copied", "SMS / WhatsApp message copied to clipboard!")

            ctk.CTkButton(btn_row, text="💬 Send WhatsApp", width=130, height=28, fg_color="#25D366", hover_color="#128C7E", font=self.small, command=_open_wa).pack(side="left", padx=(0, 8))
            ctk.CTkButton(btn_row, text="📋 Copy Message", width=120, height=28, fg_color=PANEL_ALT, hover_color="#223149", font=self.small, command=_copy).pack(side="left")

    def _export_defaulters(self):
        """Export Defaulter List (< 75%) to Excel."""
        try:
            defaulters = self.db.get_defaulters(threshold=75.0)
            if not defaulters:
                messagebox.showinfo("Defaulters Notice", "Great news! No students currently fall below the 75% attendance threshold.")
                return
            path = export_defaulters_report(defaulters, threshold=75.0, format="excel")
            self.footer_label.configure(text=f"Exported Defaulters: {os.path.basename(path)}")
            messagebox.showinfo("Defaulters Exported", f"Found {len(defaulters)} students below 75% attendance.\nSaved to:\n{path}")
            try:
                os.startfile(path)
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Defaulters Export Error", str(e))

    def _export_monthly_matrix(self):
        """Export Monthly Register Grid (days 1..31 vs students) to Excel."""
        try:
            now = datetime.now()
            matrix = self.db.get_monthly_matrix(year=now.year, month=now.month, subject=self.current_subject.get())
            path = export_monthly_matrix(matrix)
            self.footer_label.configure(text=f"Exported Monthly Matrix: {os.path.basename(path)}")
            messagebox.showinfo("Monthly Matrix Exported", f"Saved monthly register matrix for {now.strftime('%B %Y')} to:\n{path}")
            try:
                os.startfile(path)
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Matrix Export Error", str(e))

    def _bulk_import_students(self):
        """Prompt teacher to select CSV or Excel file for bulk student import."""
        import pandas as pd
        file_path = filedialog.askopenfilename(
            title="Select Student Roster (CSV or Excel)",
            filetypes=[("Excel / CSV", "*.csv *.xlsx *.xls")]
        )
        if not file_path:
            return

        try:
            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            records = df.to_dict(orient="records")
            res = self.db.bulk_import_students(records)
            self._load_students()
            self._load_dashboard()

            msg = f"Bulk Import Complete!\n\n• Enrolled: {res['imported']}\n• Skipped (duplicates): {res['skipped']}"
            if res["errors"]:
                msg += f"\n• Errors ({len(res['errors'])}):\n  " + "\n  ".join(res["errors"][:5])
            messagebox.showinfo("Bulk Import", msg)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import file:\n{e}")

    def _launch_web_studio(self):
        """Start FastAPI server in daemon thread if needed and open browser."""
        import webbrowser
        import urllib.request
        import threading

        def _task():
            is_running = False
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/api/meta", timeout=1) as resp:
                    if resp.status == 200:
                        is_running = True
            except Exception:
                is_running = False

            if not is_running:
                try:
                    import uvicorn
                    from web.server import app as fastapi_app

                    def _serve():
                        config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")
                        server = uvicorn.Server(config)
                        server.run()

                    t = threading.Thread(target=_serve, daemon=True)
                    t.start()
                    import time
                    time.sleep(1.2)
                except Exception as e:
                    print(f"[WebStudio] Server start error: {e}")

            webbrowser.open("http://127.0.0.1:8000")
            self.root.after(0, lambda: self.footer_label.configure(text="Opened Web Studio: http://localhost:8000"))

        threading.Thread(target=_task, daemon=True).start()

    def _build_students(self, f):
        header = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=18, border_width=1, border_color=BORDER)
        header.pack(fill="x", padx=6, pady=(0, 16))
        ctk.CTkLabel(header, text="Student Directory", font=self.h1, text_color=ACCENT).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(header, text="Manage enrolled students and remove entries when needed.", font=self.body, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 16))
        
        self._style_treeview()
        self.stu_tree = ttk.Treeview(f, columns=("ID", "Name", "Roll", "PRN"), show="headings")
        for col in ("ID", "Name", "Roll", "PRN"): 
            self.stu_tree.heading(col, text=col)
            
        self.stu_tree.pack(fill="both", expand=True, padx=6, pady=10)
        
        controls = ctk.CTkFrame(f, fg_color="transparent")
        controls.pack(fill="x", pady=10)
        ctk.CTkButton(controls, text="🗑 Delete Selected", fg_color=DANGER, hover_color="#B91C1C", 
                      command=self._delete_student).pack(side="left", padx=(0, 10))
        ctk.CTkButton(controls, text="📥 Bulk Import (CSV/Excel)", fg_color="#059669", hover_color="#047857",
                      command=self._bulk_import_students).pack(side="left", padx=10)
        ctk.CTkButton(controls, text="⚠️ Defaulter List (<75%)", fg_color=WARNING, hover_color="#D97706",
                      command=self._export_defaulters).pack(side="left", padx=10)

    def _load_students(self):
        self.stu_tree.delete(*self.stu_tree.get_children())
        for s in self.db.get_all_students():
            self.stu_tree.insert("", "end", values=(s["id"], s["name"], s["roll_no"], s["prn"]))

    # ── Analytics ─────────────────────────────────────────────────────────────
    def _build_analytics(self, f):
        hdr = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=BORDER)
        hdr.pack(fill="x", padx=6, pady=(0, 16))
        ctk.CTkLabel(hdr, text="📈  Analytics", font=self.h1, text_color=ACCENT).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(hdr, text="Attendance trends and subject-wise performance.", font=self.body, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 14))

        charts_row = ctk.CTkFrame(f, fg_color="transparent")
        charts_row.pack(fill="both", expand=True, padx=6)

        # Bar chart – 7-day trend
        left_card = ctk.CTkFrame(charts_row, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=BORDER)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(left_card, text="7-Day Attendance Trend", font=self.h2, text_color="white").pack(pady=(14, 2))
        ctk.CTkLabel(left_card, text="Daily present count for last 7 days", font=self.small, text_color=TEXT_MUTED).pack(pady=(0, 8))
        self.analytics_fig = Figure(figsize=(5, 3.2), dpi=96)
        self.analytics_fig.patch.set_facecolor(PANEL_BG)
        self.analytics_ax = self.analytics_fig.add_subplot(111)
        self.analytics_ax.set_facecolor(PANEL_BG)
        self.analytics_canvas = FigureCanvasTkAgg(self.analytics_fig, master=left_card)
        self.analytics_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Subject pie
        right_card = ctk.CTkFrame(charts_row, width=340, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=BORDER)
        right_card.pack(side="right", fill="both")
        right_card.pack_propagate(False)
        ctk.CTkLabel(right_card, text="Subject Distribution", font=self.h2, text_color="white").pack(pady=(14, 2))
        ctk.CTkLabel(right_card, text="Attendance share per subject today", font=self.small, text_color=TEXT_MUTED).pack(pady=(0, 8))
        self.pie_fig = Figure(figsize=(3.2, 3.2), dpi=96)
        self.pie_fig.patch.set_facecolor(PANEL_BG)
        self.pie_ax = self.pie_fig.add_subplot(111)
        self.pie_ax.set_facecolor(PANEL_BG)
        self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, master=right_card)
        self.pie_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Summary table
        tbl_card = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=BORDER)
        tbl_card.pack(fill="x", padx=6, pady=(16, 0))
        ctk.CTkLabel(tbl_card, text="Subject Summary", font=self.h2, text_color="white").pack(anchor="w", padx=18, pady=(14, 6))
        self.analytics_tree = ttk.Treeview(tbl_card, columns=("Subject","Present","Total","Pct"), show="headings", height=5)
        for col, w in (("Subject",280),("Present",100),("Total",100),("Pct",100)):
            self.analytics_tree.heading(col, text=col)
            self.analytics_tree.column(col, width=w, anchor="center")
        self.analytics_tree.pack(fill="x", padx=12, pady=(0, 14))

    def _load_analytics(self):
        today = datetime.now().strftime("%Y-%m-%d")
        # 7-day bar chart
        days, counts = [], []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            s = self.db.get_summary(d)
            days.append((datetime.now() - timedelta(days=i)).strftime("%a"))
            counts.append(s["present"])
        self.analytics_ax.clear()
        self.analytics_ax.set_facecolor(PANEL_BG)
        bars = self.analytics_ax.bar(days, counts, color=ACCENT, alpha=0.85, width=0.6)
        self.analytics_ax.tick_params(colors="white")
        self.analytics_ax.set_ylabel("Present", color="white")
        self.analytics_ax.spines[:].set_color(BORDER)
        for bar, val in zip(bars, counts):
            self.analytics_ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                                    str(val), ha="center", va="bottom", color="white", fontsize=9)
        self.analytics_canvas.draw()
        # Pie chart
        subj_data = self.db.get_subject_summary(today, SUBJECTS)
        labels = [r["subject"][:14] for r in subj_data if r["present"] > 0]
        sizes  = [r["present"]     for r in subj_data if r["present"] > 0]
        colors = ["#6366F1","#22D3EE","#10B981","#F59E0B","#EF4444"]
        self.pie_ax.clear()
        self.pie_ax.set_facecolor(PANEL_BG)
        if sizes:
            self.pie_ax.pie(sizes, labels=labels, colors=colors[:len(sizes)],
                             autopct="%1.0f%%", textprops={"color":"white","fontsize":8})
        else:
            self.pie_ax.text(0.5, 0.5, "No data today", ha="center", va="center", color="white", transform=self.pie_ax.transAxes)
        self.pie_canvas.draw()
        # Summary table
        self.analytics_tree.delete(*self.analytics_tree.get_children())
        for r in subj_data:
            self.analytics_tree.insert("", "end", values=(r["subject"], r["present"], r["total"], f"{r['percentage']:.1f}%"))

    def _delete_student(self):
        sel = self.stu_tree.selection()
        if not sel: return
        item = self.stu_tree.item(sel[0])["values"]
        sid = item[0]
        if messagebox.askyesno("Confirm", f"Delete student {item[1]}?"):
            self.db.delete_student(sid)
            self._load_students()
            self._load_dashboard()

    def _update_clock(self):
        self.dt_label.configure(text=datetime.now().strftime("%a, %b %d   %H:%M:%S"))
        self.root.after(1000, self._update_clock)

    def _update_footer_clock(self):
        self.footer_time.configure(text=datetime.now().strftime("%I:%M %p"))
        self.root.after(1000, self._update_footer_clock)

    def _style_treeview(self):
        style = ttk.Style()
        try:
            style.theme_use("default")
        except Exception:
            pass
        style.configure(
            "Treeview",
            background=PANEL_BG,
            foreground="white",
            fieldbackground=PANEL_BG,
            borderwidth=0,
            rowheight=34,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Treeview.Heading",
            background="#132033",
            foreground="white",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
        )
        style.map("Treeview", background=[("selected", ACCENT_DARK)], foreground=[("selected", "white")])

    def run(self):
        self.root.mainloop()
        self.db.close()
        try:
            self.auth.close()
        except Exception:
            pass

    # ── Users Management (Teacher only) ───────────────────────────────────────

    def _build_users(self, f):
        hdr = ctk.CTkFrame(f, fg_color=PANEL_BG, corner_radius=18, border_width=1, border_color=BORDER)
        hdr.pack(fill="x", padx=6, pady=(0, 16))
        ctk.CTkLabel(hdr, text="User Management", font=self.h1, text_color=ACCENT).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(hdr, text="Create and manage teacher & student login accounts.", font=self.body, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 16))

        # Action bar
        action_bar = ctk.CTkFrame(f, fg_color="transparent")
        action_bar.pack(fill="x", padx=6, pady=(0, 10))
        ctk.CTkButton(action_bar, text="➕ Add Teacher Account", fg_color=ACCENT_DARK, hover_color="#0B9FBF",
                      command=lambda: self._create_user_dialog("teacher")).pack(side="left", padx=(0, 10))
        ctk.CTkButton(action_bar, text="➕ Add Student Account", fg_color=SUCCESS, hover_color="#059669",
                      command=lambda: self._create_user_dialog("student")).pack(side="left", padx=0)
        ctk.CTkButton(action_bar, text="🔄 Refresh", fg_color=PANEL_ALT, hover_color="#223149",
                      command=self._load_users).pack(side="right")

        # Info card
        info = ctk.CTkFrame(f, fg_color=PANEL_ALT, corner_radius=12, border_width=1, border_color=BORDER)
        info.pack(fill="x", padx=6, pady=(0, 12))
        ctk.CTkLabel(info, text="🔑  Default Teacher:  admin  /  admin123   — Change it after first login!",
                     font=ctk.CTkFont(family="Consolas", size=12), text_color=WARNING).pack(padx=16, pady=10)

        # Users table
        self._style_treeview()
        self.users_tree = ttk.Treeview(f,
            columns=("ID", "Username", "Role", "Linked Student", "Created"),
            show="headings", height=14)
        for col, w in (("ID", 50), ("Username", 160), ("Role", 90),
                        ("Linked Student", 200), ("Created", 160)):
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=w, anchor="center")
        self.users_tree.pack(fill="both", expand=True, padx=6, pady=6)

        del_bar = ctk.CTkFrame(f, fg_color="transparent")
        del_bar.pack(fill="x", padx=6, pady=6)
        ctk.CTkButton(del_bar, text="🗑 Delete Selected User", fg_color=DANGER, hover_color="#B91C1C",
                      command=self._delete_user).pack(side="left")
        self.users_status = ctk.CTkLabel(del_bar, text="", font=self.small, text_color=TEXT_MUTED)
        self.users_status.pack(side="left", padx=16)

    def _load_users(self):
        if not hasattr(self, "users_tree"):
            return
        self.users_tree.delete(*self.users_tree.get_children())
        for u in self.auth.get_all_users():
            role_label = "👨‍🏫 Teacher" if u["role"] == "teacher" else "👨‍🎓 Student"
            linked = f"{u.get('student_name', '')} ({u.get('roll_no', '')})" if u.get("student_name") else "—"
            self.users_tree.insert("", "end",
                values=(u["id"], u["username"], role_label, linked, u["created_at"]))

    def _create_user_dialog(self, role: str):
        """Popup dialog to create a new user account."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Create {'Teacher' if role == 'teacher' else 'Student'} Account")
        dialog.geometry("420x420")
        dialog.configure(fg_color=PAGE_BG)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog,
            text=f"{'👨‍🏫 New Teacher' if role == 'teacher' else '👨‍🎓 New Student'} Account",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=ACCENT).pack(pady=(20, 4))
        ctk.CTkLabel(dialog, text="Fill in the login credentials below.",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(pady=(0, 16))

        card = ctk.CTkFrame(dialog, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=24)

        uname_var = ctk.StringVar()
        pw_var    = ctk.StringVar()

        ctk.CTkLabel(card, text="Username", font=self.small, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(14, 0))
        ctk.CTkEntry(card, textvariable=uname_var, placeholder_text="e.g. john_doe",
                     height=38, fg_color=PANEL_ALT, border_color=BORDER, corner_radius=8).pack(fill="x", padx=16, pady=(4, 10))

        ctk.CTkLabel(card, text="Password", font=self.small, text_color=TEXT_MUTED).pack(anchor="w", padx=16)
        ctk.CTkEntry(card, textvariable=pw_var, show="●", placeholder_text="Min 4 characters",
                     height=38, fg_color=PANEL_ALT, border_color=BORDER, corner_radius=8).pack(fill="x", padx=16, pady=(4, 10))

        # Student picker (only for student role)
        sid_var = ctk.IntVar(value=0)
        if role == "student":
            ctk.CTkLabel(card, text="Link to Student", font=self.small, text_color=TEXT_MUTED).pack(anchor="w", padx=16)
            students = self.db.get_all_students()
            options  = [f"{s['roll_no']} – {s['name']}" for s in students]
            ids      = [s["id"] for s in students]
            if options:
                sel_var = ctk.StringVar(value=options[0])
                sid_var.set(ids[0])
                def _on_pick(choice):
                    idx = options.index(choice)
                    sid_var.set(ids[idx])
                ctk.CTkOptionMenu(card, values=options, variable=sel_var,
                                   fg_color=PANEL_ALT, button_color=ACCENT_DARK,
                                   command=_on_pick).pack(fill="x", padx=16, pady=(4, 14))
            else:
                ctk.CTkLabel(card, text="No students registered yet.", text_color=WARNING).pack(padx=16, pady=10)

        status_lbl = ctk.CTkLabel(dialog, text="", font=self.small, text_color=DANGER)
        status_lbl.pack(pady=(10, 0))

        def _create():
            uname = uname_var.get().strip()
            pw    = pw_var.get().strip()
            if len(uname) < 3:
                status_lbl.configure(text="Username must be at least 3 characters.", text_color=DANGER)
                return
            if len(pw) < 4:
                status_lbl.configure(text="Password must be at least 4 characters.", text_color=DANGER)
                return
            if self.auth.username_exists(uname):
                status_lbl.configure(text="Username already taken. Choose another.", text_color=DANGER)
                return
            if role == "teacher":
                ok = self.auth.create_teacher(uname, pw)
            else:
                ok = self.auth.create_student_login(uname, pw, sid_var.get())
            if ok:
                status_lbl.configure(text=f"Account '{uname}' created!", text_color=SUCCESS)
                self._load_users()
                dialog.after(900, dialog.destroy)
            else:
                status_lbl.configure(text="Failed to create account.", text_color=DANGER)

        ctk.CTkButton(dialog, text="Create Account", height=42,
                      fg_color=ACCENT_DARK, hover_color="#0B9FBF",
                      font=self.body, command=_create).pack(fill="x", padx=24, pady=16)

    def _delete_user(self):
        sel = self.users_tree.selection()
        if not sel:
            return
        item = self.users_tree.item(sel[0])["values"]
        uid, uname = item[0], item[1]
        
        # Prevent deleting the currently logged-in user
        if uname == self._user.get("username"):
            messagebox.showwarning("Protected", "You cannot delete the account you are currently logged into.\nPlease create a new account, login with it, and then delete this one.")
            return
            
        # Prevent deleting the last teacher
        teachers = [u for u in self.auth.get_all_users() if u["role"] == "teacher"]
        if len(teachers) <= 1 and any(t["id"] == uid for t in teachers):
            messagebox.showwarning("Protected", "You cannot delete the last teacher account. Create another teacher account first.")
            return

        if messagebox.askyesno("Confirm", f"Delete user '{uname}'?"):
            self.auth.delete_user(uid)
            self._load_users()
            if hasattr(self, "users_status"):
                self.users_status.configure(text=f"User '{uname}' deleted.", text_color=WARNING)

    # ── Logout ────────────────────────────────────────────────────────────────

    def _logout(self):
        if not messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            return
        self.db.close()
        try:
            self.auth.close()
        except Exception:
            pass
        self.root.destroy()

        # Re-launch login screen
        from gui.login_window import LoginWindow
        from gui.student_portal import StudentPortal

        def _on_login(user):
            if user["role"] == "teacher":
                app = AttendanceApp(user=user)
                app.run()
            else:
                portal = StudentPortal(user)
                portal.run()

        lw = LoginWindow(on_success=_on_login)
        lw.run()

