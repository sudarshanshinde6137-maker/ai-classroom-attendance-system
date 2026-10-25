"""
Webcam Window - Real-time face recognition attendance via webcam (CustomTkinter)
Features: PyTTSX3 Voice AI and Mediapipe 3D Face Mesh HUD
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import threading
import time
import concurrent.futures
from datetime import datetime

try:
    import cv2
    from PIL import Image, ImageTk
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

APP_BG = "#07111D"
PANEL_BG = "#0E1626"
PANEL_ALT = "#162337"
ACCENT = "#38BDF8"
ACCENT_2 = "#22C55E"
TEXT_MUTED = "#94A3B8"
WARNING = "#F59E0B"
LIVE = "#10B981"

class WebcamWindow:
    def __init__(self, parent, db, engine, session="Morning", subject="General", tolerance=0.55, on_close=None):
        if not CV2_AVAILABLE:
            messagebox.showerror("Missing Libraries", "OpenCV and Pillow are required for webcam mode.")
            return

        self.db = db
        self.engine = engine
        self.session = session
        self.subject = subject
        self.tolerance = tolerance
        self.on_close = on_close
        self.running = False
        self.cap = None
        self.marked_today = set()  # stores (student_id, subject) tuples
        # HUD live log counters/state
        self.processed_count = 0
        self._last_added_name = None
        # Background recognition executor (single worker)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._recognition_future = None
        self._latest_results = []

        # Initialize TTS Engine Settings
        self.voice_lock = threading.Lock()

        # Mediapipe HUD mesh (optional)
        self.use_mesh = False
        if MP_AVAILABLE:
            try:
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    max_num_faces=5, refine_landmarks=True,
                    min_detection_confidence=0.5, min_tracking_confidence=0.5
                )
                self.mp_drawing = mp.solutions.drawing_utils
                self.mp_drawing_styles = mp.solutions.drawing_styles
            except Exception:
                print("Mediapipe solutions not available, disabling 3D HUD mesh.")

        self.win = ctk.CTkToplevel(parent)
        self.win.title("J.A.R.V.I.S. Biometric Face Scanner • Mediapipe HUD")
        self.win.geometry("1040x680")
        self.win.configure(fg_color=APP_BG)
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        
        self.win.attributes('-topmost', True)
        self.win.after(10, lambda: self.win.attributes('-topmost', False))

        self._build_ui()
        self.start()
        self._speak_async("J.A.R.V.I.S. optical biometric scanner online.")

    def _speak_async(self, text):
        if not TTS_AVAILABLE:
            return
        def _speak():
            with self.voice_lock:
                try:
                    tts = pyttsx3.init()
                    tts.setProperty('rate', 160)
                    voices = tts.getProperty('voices')
                    if len(voices) > 1:
                        tts.setProperty('voice', voices[1].id)
                    tts.say(text)
                    tts.runAndWait()
                except Exception:
                    pass
        threading.Thread(target=_speak, daemon=True).start()

    def _play_chime(self):
        if not SOUND_AVAILABLE:
            return
        def _chime():
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
        threading.Thread(target=_chime, daemon=True).start()

    def _add_to_tree(self, name, timestamp):
        # Avoid inserting the same name repeatedly in immediate succession
        if self._last_added_name == name:
            return

        item_id = self.live_tree.insert("", 0, values=(name, timestamp))
        self._last_added_name = name

        # Keep tree to a reasonable size (latest 25)
        items = self.live_tree.get_children()
        if len(items) > 25:
            for item in items[25:]:
                self.live_tree.delete(item)

        # Update processed counter & label
        try:
            self.processed_count += 1
            self.count_label.configure(text=f"Processed: {self.processed_count}")
        except Exception:
            pass

        # Ensure new item is visible
        try:
            self.live_tree.see(item_id)
        except Exception:
            pass

    def _resolve_student_name(self, student_id, fallback_name="Unknown"):
        """Prefer the database name for a recognized student id."""
        if student_id is None:
            return fallback_name

        try:
            student = self.db.get_student_by_id(student_id)
        except Exception:
            student = None

        if student and student.get("name"):
            name = student["name"].strip()
            if name:
                return name

        return (fallback_name or "Unknown").strip() or "Unknown"

    def _build_ui(self):
        self.win.grid_columnconfigure(0, weight=3)
        self.win.grid_columnconfigure(1, weight=1)
        self.win.grid_rowconfigure(0, weight=1)
        
        # Camera feed
        self.cam_frame = ctk.CTkFrame(self.win, corner_radius=18, fg_color="#050B14", border_width=1, border_color="#1F2B3D")
        self.cam_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        cam_header = ctk.CTkFrame(self.cam_frame, fg_color="transparent")
        cam_header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(cam_header, text="Live Camera Feed", font=("Segoe UI", 18, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(cam_header, text="AI overlay active", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(side="left", padx=(10, 0), pady=(4, 0))

        self.cam_label = ctk.CTkLabel(self.cam_frame, text="Initializing camera...", font=("Consolas", 18), text_color=ACCENT)
        self.cam_label.pack(fill="both", expand=True)

        # Right panel
        self.right_panel = ctk.CTkFrame(self.win, corner_radius=18, fg_color=PANEL_BG, border_width=1, border_color="#223044")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)
        
        ctk.CTkLabel(self.right_panel, text="HUD Live Log", font=("Segoe UI", 18, "bold"), text_color=ACCENT).pack(pady=(14, 8))

        status_strip = ctk.CTkFrame(self.right_panel, fg_color=PANEL_ALT, corner_radius=14, border_width=1, border_color="#223044")
        status_strip.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(status_strip, text="Session", font=("Segoe UI", 10), text_color=TEXT_MUTED).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(status_strip, text=self.session, font=("Segoe UI", 14, "bold"), text_color="white").grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))
        ctk.CTkLabel(status_strip, text="Subject", font=("Segoe UI", 10), text_color=TEXT_MUTED).grid(row=0, column=1, sticky="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(status_strip, text=self.subject, font=("Segoe UI", 12, "bold"), text_color=ACCENT_2, wraplength=170, justify="left").grid(row=1, column=1, sticky="w", padx=12, pady=(0, 10))
        ctk.CTkLabel(status_strip, text="Live", font=("Segoe UI", 10), text_color=TEXT_MUTED).grid(row=0, column=2, sticky="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(status_strip, text="● Active", font=("Segoe UI", 14, "bold"), text_color=LIVE).grid(row=1, column=2, sticky="w", padx=12, pady=(0, 10))
        status_strip.grid_columnconfigure(0, weight=1)
        status_strip.grid_columnconfigure(1, weight=1)
        status_strip.grid_columnconfigure(2, weight=1)

        self.target_status = ctk.CTkLabel(
            self.right_panel,
            text="Target Identified: Waiting...",
            font=("Segoe UI", 14, "bold"),
            text_color=WARNING,
            wraplength=210,
            justify="left",
        )
        self.target_status.pack(pady=(0, 10), padx=10, anchor="w")
        
        # Tree
        style = ttk.Style()
        try:
            style.theme_use("default")
        except Exception:
            pass
        style.configure("Live.Treeview", font=("Segoe UI", 11), rowheight=32, background=PANEL_BG, fieldbackground=PANEL_BG, foreground="white", borderwidth=0)
        style.configure("Live.Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#132033", foreground="white", relief="flat")
        self.live_tree = ttk.Treeview(self.right_panel, columns=("Name", "Time"), show="headings", height=15, style="Live.Treeview")
        self.live_tree.heading("Name", text="Target Identified")
        self.live_tree.heading("Time", text="Timestamp")
        self.live_tree.column("Name", width=146)
        self.live_tree.column("Time", width=90)
        self.live_tree.pack(fill="both", expand=True, padx=12, pady=8)
        
        footer_strip = ctk.CTkFrame(self.right_panel, fg_color=PANEL_ALT, corner_radius=14, border_width=1, border_color="#223044")
        footer_strip.pack(fill="x", padx=12, pady=(8, 10))
        self.count_label = ctk.CTkLabel(footer_strip, text="Processed: 0", font=("Segoe UI", 16, "bold"), text_color=LIVE)
        self.count_label.pack(side="left", padx=12, pady=10)
        ctk.CTkLabel(footer_strip, text="Marked entries appear here in real time.", font=("Segoe UI", 10), text_color=TEXT_MUTED).pack(side="right", padx=12, pady=10)
        
        self.stop_btn = ctk.CTkButton(self.right_panel, text="DISCONNECT", font=("Segoe UI", 14, "bold"), fg_color="#EF4444", hover_color="#B91C1C", command=self.stop)
        self.stop_btn.pack(pady=(4, 14), padx=15, fill="x")

    def start(self):
        self.running = True
        self.cap = self._open_camera()
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Could not connect to the webcam. Please ensure it is plugged in and not used by another application.")
            self.stop()
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
        self._frame_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._frame_thread.start()
        self._update_feed()

    def _open_camera(self):
        for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY):
            cap = cv2.VideoCapture(0, backend)
            if cap.isOpened():
                return cap
        return cv2.VideoCapture(0)

    def _process_loop(self):
        # Non-blocking recognition loop using a background executor.
        while self.running:
            # Small sleep to avoid busy loop; recognition is handled by executor
            time.sleep(0.2)
            if not self.running or not hasattr(self, "_current_frame"): continue

            # If a recognition task is already running, skip submitting a new one
            if self._recognition_future and not self._recognition_future.done():
                continue

            frame = self._current_frame.copy()

            # Submit recognition job to background executor
            try:
                self._recognition_future = self._executor.submit(self.engine.recognize_from_frame, frame, self.tolerance)
            except Exception as e:
                print("Failed to submit recognition job:", e)
                continue

            # Attach a callback to process results when ready
            def _on_done(fut):
                try:
                    results = fut.result()
                except Exception as exc:
                    print("Face Recognition error:", exc)
                    return

                # Schedule UI updates on the main thread
                def handle_results():
                    try:
                        self._latest_results = results
                        self._latest_frame = frame

                        # Show the current target immediately in the HUD.
                        target_name = "Unknown"
                        target_color = "#F59E0B"
                        for r in results:
                            if r.get("recognized"):
                                target_name = self._resolve_student_name(r.get("student_id"), r.get("name", "Unknown"))
                                target_color = "#10B981"
                                break
                        self.target_status.configure(text=f"Target Identified: {target_name}", text_color=target_color)

                        _dashboard_refresh_needed = False
                        for r in results:
                            sid = r.get("student_id")
                            mark_key = (sid, self.subject)
                            if r["recognized"] and mark_key not in self.marked_today:
                                if self.db.mark_attendance(sid, self.session, self.subject):
                                    self.marked_today.add(mark_key)
                                    now = datetime.now().strftime("%H:%M:%S")
                                    name = self._resolve_student_name(sid, r.get("name", "Unknown"))
                                    self._add_to_tree(name, now)
                                    _dashboard_refresh_needed = True
                                    # Trigger effects
                                    self._play_chime()
                                    self._speak_async(f"J.A.R.V.I.S. verified: {name}. Attendance logged.")

                        # Immediately refresh the parent dashboard whenever a new mark is made
                        if _dashboard_refresh_needed and self.on_close:
                            try:
                                self.on_close()
                            except Exception:
                                pass


                    except Exception as e:
                        print("Error handling recognition results:", e)

                try:
                    self.win.after(0, handle_results)
                except Exception:
                    # If window closed, ignore
                    pass

            # Add done callback
            try:
                self._recognition_future.add_done_callback(_on_done)
            except Exception:
                pass

    def _process_visuals(self, frame, results):
        # Draw 3D Mesh and classic bounding boxes
        display = frame.copy()
        
        # 1. Mediapipe HUD Mesh
        if getattr(self, "use_mesh", False):
            rgb_frame = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            mesh_results = self.face_mesh.process(rgb_frame)
            
            if mesh_results.multi_face_landmarks:
                for face_landmarks in mesh_results.multi_face_landmarks:
                    self.mp_drawing.draw_landmarks(
                        image=display,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                    )
                    self.mp_drawing.draw_landmarks(
                        image=display,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                    )

        # 2. Classic Tracking Boxes with Labels
        for r in results:
            t, right, b, l = r["location"]
            # Color scheme: Cyan for recognized, Red for unknown
            color = (255, 128, 0) if r["recognized"] else (50, 50, 255) # BGR: Cyan is (255, 255, 0) wait no, BGR for Cyan is (255, 255, 0)? No, BGR Cyan is (255, 255, 0). (255, 128, 0) is blue-ish cyan
            
            # Draw futuristic corners instead of full box
            cv2.rectangle(display, (l, t), (right, b), color, 1)
            
            # Label
            label = f"[{r['name'].upper()}]"
            cv2.putText(display, label, (l, t - 10), cv2.FONT_HERSHEY_DUPLEX, 0.6, color, 1)

        self._display_frame = display

    def _update_feed(self):
        if not self.running: return

        ret, frame = self.cap.read()
        if ret:
            self._current_frame = frame
            display = frame.copy()

            # Draw the latest recognition overlay on the newest frame.
            latest_results = getattr(self, "_latest_results", None)
            if latest_results:
                for r in latest_results:
                    t, right, b, l = r["location"]
                    color = (255, 128, 0) if r["recognized"] else (50, 50, 255)
                    cv2.rectangle(display, (l, t), (right, b), color, 1)
                    label = f"[{r['name'].upper()}]"
                    cv2.putText(display, label, (l, t - 10), cv2.FONT_HERSHEY_DUPLEX, 0.6, color, 1)

            display = cv2.resize(display, (640, 480), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            photo = ImageTk.PhotoImage(img)
            self.cam_label.configure(image=photo, text="")
            self.cam_label._photo = photo
        self.win.after(33, self._update_feed) # ~30 FPS for smoother live preview

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        try:
            if hasattr(self, "face_mesh"):
                self.face_mesh.close()
        except Exception:
            pass
        try:
            if hasattr(self, "_executor"):
                self._executor.shutdown(wait=False)
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass
        if self.on_close:
            self.on_close()
            
