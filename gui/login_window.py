"""
Login Window - Premium glassmorphic login screen for the Attendance System
Supports Teacher and Student roles.
"""

import customtkinter as ctk
from tkinter import messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth import AuthManager

# ── Theme (matches main app) ──────────────────────────────────────────────────
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


class LoginWindow:
    def __init__(self, on_success):
        """
        on_success(user_dict) called with the logged-in user info.
        user_dict keys: id, username, role, student_id
        """
        self.on_success = on_success
        self.auth = AuthManager()
        self._show_pw = False

        self.root = ctk.CTk()
        self.root.title("AI Attendance System — Login")
        self.root.geometry("520x640")
        self.root.resizable(False, False)
        self.root.configure(fg_color=PAGE_BG)
        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.root.update_idletasks()
        w, h = 520, 640
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # ── Outer card ────────────────────────────────────────────────────────
        outer = ctk.CTkFrame(self.root, fg_color=PAGE_BG)
        outer.pack(fill="both", expand=True, padx=40, pady=30)

        # ── Brand header ──────────────────────────────────────────────────────
        brand = ctk.CTkFrame(outer, fg_color="transparent")
        brand.pack(pady=(10, 0))

        ctk.CTkLabel(
            brand, text="🎓",
            font=ctk.CTkFont(size=52)
        ).pack()
        ctk.CTkLabel(
            brand, text="AI Attendance Studio",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="white"
        ).pack(pady=(4, 0))
        ctk.CTkLabel(
            brand, text="Smart Classroom Management System",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED
        ).pack(pady=(2, 0))

        # Accent divider
        ctk.CTkFrame(outer, height=2, fg_color=ACCENT, corner_radius=999).pack(
            fill="x", padx=0, pady=(18, 0)
        )

        # ── Login card ────────────────────────────────────────────────────────
        card = ctk.CTkFrame(
            outer,
            fg_color=PANEL_BG,
            corner_radius=20,
            border_width=1,
            border_color=BORDER
        )
        card.pack(fill="x", pady=18)

        ctk.CTkLabel(
            card, text="Sign In",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=ACCENT
        ).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            card, text="Enter your credentials to continue",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=24, pady=(0, 18))

        # Username
        ctk.CTkLabel(
            card, text="Username",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=24)
        self.username_var = ctk.StringVar()
        self.username_entry = ctk.CTkEntry(
            card,
            textvariable=self.username_var,
            placeholder_text="Enter username",
            height=42,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=PANEL_ALT,
            border_color=BORDER,
            corner_radius=10
        )
        self.username_entry.pack(fill="x", padx=24, pady=(4, 14))
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())

        # Password row
        ctk.CTkLabel(
            card, text="Password",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=24)

        pw_row = ctk.CTkFrame(card, fg_color="transparent")
        pw_row.pack(fill="x", padx=24, pady=(4, 6))

        self.password_var = ctk.StringVar()
        self.password_entry = ctk.CTkEntry(
            pw_row,
            textvariable=self.password_var,
            placeholder_text="Enter password",
            show="●",
            height=42,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=PANEL_ALT,
            border_color=BORDER,
            corner_radius=10
        )
        self.password_entry.pack(side="left", fill="x", expand=True)
        self.password_entry.bind("<Return>", lambda e: self._login())

        self.eye_btn = ctk.CTkButton(
            pw_row, text="👁", width=42, height=42,
            fg_color=PANEL_ALT, hover_color=ACCENT_DK,
            corner_radius=10,
            command=self._toggle_pw
        )
        self.eye_btn.pack(side="left", padx=(6, 0))

        # Status label
        self.status_label = ctk.CTkLabel(
            card, text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=DANGER
        )
        self.status_label.pack(pady=(4, 0))

        # Login button
        self.login_btn = ctk.CTkButton(
            card,
            text="Sign In  →",
            height=46,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=ACCENT_DK,
            hover_color="#0B9FBF",
            corner_radius=12,
            command=self._login
        )
        self.login_btn.pack(fill="x", padx=24, pady=(8, 24))

        # ── Default credentials hint ──────────────────────────────────────────
        hint = ctk.CTkFrame(
            outer,
            fg_color=PANEL_ALT,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )
        hint.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            hint,
            text="🔑  Default Teacher Login",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=WARNING
        ).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(
            hint,
            text="Username: admin     Password: admin123",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # ── Footer ────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            outer,
            text="AI Attendance Studio v2  •  Secure Login",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#334155"
        ).pack(pady=(4, 0))

        self.username_entry.focus()

    def _toggle_pw(self):
        self._show_pw = not self._show_pw
        self.password_entry.configure(show="" if self._show_pw else "●")

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            self.status_label.configure(text="⚠  Please enter username and password.", text_color=WARNING)
            return

        self.login_btn.configure(text="Signing in...", state="disabled")
        self.root.update()

        user = self.auth.login(username, password)
        self.login_btn.configure(text="Sign In  →", state="normal")

        if user:
            self.status_label.configure(text=f"✓  Welcome, {user['username']}!", text_color=SUCCESS)
            self.root.update()
            self.root.after(400, lambda: self._proceed(user))
        else:
            self.status_label.configure(text="✗  Invalid username or password.", text_color=DANGER)
            self.password_var.set("")
            self.password_entry.focus()

    def _proceed(self, user):
        self.auth.close()
        self.root.destroy()
        self.on_success(user)

    def run(self):
        self.root.mainloop()
