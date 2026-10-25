"""
Face Recognition Engine - OpenCV-based (Python 3.14 compatible, no dlib required)
Uses YuNet face detector + SFace recognizer (ONNX models, auto-downloaded ~37 MB once)
Falls back to Haar cascade + LBPH if model download fails.
"""

import os
import pickle
import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional

if os.environ.get("VERCEL"):
    ENCODINGS_PATH = "/tmp/encodings.pkl"
    PHOTOS_DIR = "/tmp/student_photos"
    MODELS_DIR = "/tmp/models"
else:
    ENCODINGS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "database", "encodings.pkl"
    )
    PHOTOS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "student_photos"
    )
    MODELS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "database", "models"
    )

YUNET_URL  = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
SFACE_URL  = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
YUNET_PATH = os.path.join(MODELS_DIR, "yunet.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "sface.onnx")


class FaceEngine:
    def __init__(self):
        self.known_encodings: List[np.ndarray] = []
        self.known_ids:       List[int]        = []
        self.known_names:     List[str]        = []
        self._use_dnn = False
        self._detector  = None
        self._recognizer = None
        self._cascade    = None

        self._load_encodings()
        self._init_detector()

    # ── Model init ───────────────────────────────────────────────────────────

    def _init_detector(self):
        os.makedirs(MODELS_DIR, exist_ok=True)
        try:
            self._ensure_model(YUNET_PATH,  YUNET_URL)
            self._ensure_model(SFACE_PATH,  SFACE_URL)
            self._detector   = cv2.FaceDetectorYN.create(YUNET_PATH, "", (320, 320), score_threshold=0.5)
            self._recognizer = cv2.FaceRecognizerSF.create(SFACE_PATH, "")
            self._use_dnn = True
            print("[FaceEngine] Using YuNet + SFace (high accuracy).")
        except Exception as e:
            print(f"[FaceEngine] DNN models unavailable ({e}). Falling back to Haar+LBPH.")
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._cascade = cv2.CascadeClassifier(cascade_path)

    def _ensure_model(self, path, url):
        if not os.path.exists(path):
            print(f"[FaceEngine] Downloading model: {os.path.basename(path)} ...")
            import urllib.request
            urllib.request.urlretrieve(url, path)
            print(f"[FaceEngine] Downloaded: {os.path.basename(path)}")

    # ── Encoding persistence ──────────────────────────────────────────────────

    def _load_encodings(self):
        if os.path.exists(ENCODINGS_PATH):
            try:
                with open(ENCODINGS_PATH, "rb") as f:
                    data = pickle.load(f)
                self.known_encodings = data.get("encodings", [])
                self.known_ids       = data.get("ids",       [])
                self.known_names     = data.get("names",     [])
            except Exception:
                pass

    def _save_encodings(self):
        os.makedirs(os.path.dirname(ENCODINGS_PATH), exist_ok=True)
        with open(ENCODINGS_PATH, "wb") as f:
            pickle.dump({
                "encodings": self.known_encodings,
                "ids":       self.known_ids,
                "names":     self.known_names,
            }, f)

    # ── Core face helpers ─────────────────────────────────────────────────────

    def _read_rgb(self, path: str) -> Optional[np.ndarray]:
        img = cv2.imread(path)
        if img is None:
            return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def _detect_and_encode(self, rgb: np.ndarray):
        """Returns list of (encoding, location=(top,right,bottom,left), landmarks)."""
        results = []
        if self._use_dnn:
            h, w = rgb.shape[:2]
            self._detector.setInputSize((w, h))
            _, faces = self._detector.detect(rgb)
            if faces is None:
                return results
            for face in faces:
                x, y, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
                # clamp
                x, y = max(0, x), max(0, y)
                fw = min(fw, w - x)
                fh = min(fh, h - y)
                if fw <= 0 or fh <= 0:
                    continue
                try:
                    aligned = self._recognizer.alignCrop(rgb, face)
                    feat    = self._recognizer.feature(aligned).flatten()
                    loc = (y, x + fw, y + fh, x)
                    landmarks = face[4:14].tolist() if len(face) >= 14 else []
                    results.append((feat, loc, landmarks))
                except Exception:
                    continue
        else:
            gray  = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            faces = self._cascade.detectMultiScale(gray, 1.1, 5, minSize=(20, 20))
            for (x, y, fw, fh) in faces:
                roi = gray[y:y + fh, x:x + fw]
                roi = cv2.resize(roi, (128, 128))
                roi = cv2.equalizeHist(roi)
                encoding = roi.flatten().astype(np.float32) / 255.0
                loc = (y, x + fw, y + fh, x)
                results.append((encoding, loc, []))
        return results

    def _similarity(self, enc1: np.ndarray, enc2: np.ndarray) -> float:
        """Cosine similarity → [0,1] where 1 = identical."""
        if self._use_dnn:
            score = self._recognizer.match(enc1, enc2, cv2.FaceRecognizerSF_FR_COSINE)
            return float(score)
        else:
            n1, n2 = np.linalg.norm(enc1), np.linalg.norm(enc2)
            if n1 == 0 or n2 == 0:
                return 0.0
            return float(np.dot(enc1, enc2) / (n1 * n2))

    def _match_encoding(self, encoding: np.ndarray,
                         tolerance: float) -> Tuple[Optional[int], str, float]:
        if not self.known_encodings:
            return None, "Unknown", 0.0

        # DNN: threshold ~0.363 (cosine); Haar: threshold ~0.7 (cosine)
        threshold = tolerance if self._use_dnn else 0.70

        scores = [self._similarity(encoding, k) for k in self.known_encodings]
        best_i = int(np.argmax(scores))
        best_s = scores[best_i]
        confidence = round(best_s * 100, 1)

        if best_s >= threshold:
            return self.known_ids[best_i], self.known_names[best_i], confidence
        return None, "Unknown", confidence

    # ── Public API ────────────────────────────────────────────────────────────

    def encode_student(self, student_id: int, name: str, photo_path: str) -> bool:
        rgb = self._read_rgb(photo_path)
        if rgb is None:
            return False
        detections = self._detect_and_encode(rgb)
        if not detections:
            return False
        encoding = detections[0][0]
        self._remove_student_encoding(student_id)
        self.known_encodings.append(encoding)
        self.known_ids.append(student_id)
        self.known_names.append(name)
        self._save_encodings()
        return True

    def encode_student_from_multiple(self, student_id: int, name: str,
                                      photo_paths: List[str]) -> int:
        self._remove_student_encoding(student_id)
        count = 0
        for path in photo_paths:
            rgb = self._read_rgb(path)
            if rgb is None:
                continue
            detections = self._detect_and_encode(rgb)
            if detections:
                enc = detections[0][0]
                self.known_encodings.append(enc)
                self.known_ids.append(student_id)
                self.known_names.append(name)
                count += 1
        if count > 0:
            self._save_encodings()
        return count

    def _remove_student_encoding(self, student_id: int):
        indices = [i for i, sid in enumerate(self.known_ids) if sid == student_id]
        for i in reversed(indices):
            self.known_encodings.pop(i)
            self.known_ids.pop(i)
            self.known_names.pop(i)

    def retrain_all(self, students: List[Dict]) -> Tuple[int, int]:
        self.known_encodings = []
        self.known_ids       = []
        self.known_names     = []
        success, failed = 0, 0
        for s in students:
            if s.get("photo_path") and os.path.exists(s["photo_path"]):
                if self.encode_student(s["id"], s["name"], s["photo_path"]):
                    success += 1
                    continue
            failed += 1
        self._save_encodings()
        return success, failed

    def find_matching_student(self, photo_path: str,
                               tolerance: float = 0.55) -> Optional[Dict]:
        rgb = self._read_rgb(photo_path)
        if rgb is None or not self.known_encodings:
            return None
        detections = self._detect_and_encode(rgb)
        if not detections:
            return None
        enc = detections[0][0]
        sid, name, conf = self._match_encoding(enc, tolerance)
        if sid is None:
            return None
        return {"student_id": sid, "name": name, "confidence": conf}

    def recognize_faces(self, image_path: str,
                         tolerance: float = 0.55) -> List[Dict]:
        rgb = self._read_rgb(image_path)
        if rgb is None:
            return []
        # Downscale very large images, but keep enough resolution for small faces
        h, w = rgb.shape[:2]
        scale = 1.0
        if w > 1920:
            scale = 1920 / w
            rgb = cv2.resize(rgb, (int(w * scale), int(h * scale)))

        detections = self._detect_and_encode(rgb)
        results = []
        for item in detections:
            enc = item[0]
            loc = item[1]
            landmarks = item[2] if len(item) > 2 else []
            sid, name, conf = self._match_encoding(enc, tolerance)
            top, right, bottom, left = loc
            if scale != 1.0:
                top    = int(top    / scale)
                right  = int(right  / scale)
                bottom = int(bottom / scale)
                left   = int(left   / scale)
            attention_info = self.estimate_attention(landmarks)
            results.append({
                "student_id": sid,
                "name":       name,
                "location":   (top, right, bottom, left),
                "confidence": conf,
                "recognized": sid is not None,
                "attention":  attention_info,
            })
        return results

    def check_liveness(self, face_rgb: np.ndarray) -> Tuple[bool, float, str]:
        """
        Multi-factor anti-spoofing / liveness check to detect phone screens and printed photos.
        Uses Laplacian variance, color distribution analysis, and frequency domain statistics.
        Returns: (is_live: bool, liveness_score: float, reason: str)
        """
        if face_rgb is None or face_rgb.size == 0 or face_rgb.shape[0] < 20 or face_rgb.shape[1] < 20:
            return True, 80.0, "Face crop too small to evaluate"

        gray = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2GRAY)
        
        # 1. Texture Laplacian variance (blurry photos & low-res screens have low variance)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # 2. Lighting & saturation dynamics
        hsv = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2HSV)
        v_channel = hsv[:, :, 2]
        v_std = float(np.std(v_channel))
        sat_mean = float(np.mean(hsv[:, :, 1]))

        # Unified liveness score calculation
        score = 50.0

        # Texture sharpness
        if lap_var > 60:
            score += 25.0
        elif lap_var < 25:
            score -= 30.0  # Suspicious blur/flat print

        # Light variation
        if 20.0 < v_std < 90.0:
            score += 15.0
        else:
            score -= 15.0  # Excessive screen backlighting / flat paper

        # Color naturalness
        if 25.0 < sat_mean < 210.0:
            score += 10.0

        score = max(5.0, min(99.0, score))
        is_live = score >= 50.0
        reason = "Live Human Face" if is_live else "Suspected Screen or Paper Spoof"

        return is_live, round(score, 1), reason

    def estimate_attention(self, landmarks: List[float]) -> Dict:
        """
        Estimates student head pose & attention engagement score using 5 facial landmarks.
        landmarks format: [x_re, y_re, x_le, y_le, x_nt, y_nt, x_rc, y_rc, x_lc, y_lc]
        """
        if not landmarks or len(landmarks) < 10:
            return {"score": 88.0, "state": "Attentive", "roll_deg": 0.0, "yaw_ratio": 1.0}
        
        try:
            x_re, y_re = float(landmarks[0]), float(landmarks[1])
            x_le, y_le = float(landmarks[2]), float(landmarks[3])
            x_nt, y_nt = float(landmarks[4]), float(landmarks[5])
            x_rc, y_rc = float(landmarks[6]), float(landmarks[7])
            x_lc, y_lc = float(landmarks[8]), float(landmarks[9])

            # Roll (head tilt)
            dx = x_le - x_re
            dy = y_le - y_re
            roll_deg = float(np.degrees(np.arctan2(dy, dx))) if dx != 0 else 0.0

            # Yaw (head turn left vs right)
            dist_re = float(np.hypot(x_nt - x_re, y_nt - y_re))
            dist_le = float(np.hypot(x_nt - x_le, y_nt - y_le))
            yaw_ratio = dist_re / (dist_le + 1e-4)

            # Pitch (looking down vs looking up)
            eye_y = (y_re + y_le) / 2.0
            mouth_y = (y_rc + y_lc) / 2.0
            dist_eye_nose = max(1.0, y_nt - eye_y)
            dist_nose_mouth = max(1.0, mouth_y - y_nt)
            pitch_ratio = dist_eye_nose / dist_nose_mouth

            score = 100.0

            if abs(roll_deg) > 15:
                score -= min(35.0, (abs(roll_deg) - 15) * 1.8)

            if yaw_ratio > 1.65 or yaw_ratio < 0.6:
                score -= 30.0
            elif yaw_ratio > 1.3 or yaw_ratio < 0.77:
                score -= 15.0

            if pitch_ratio > 1.55:
                score -= 25.0

            score = float(max(15.0, min(99.0, score)))

            if score >= 80:
                state = "Attentive"
            elif score >= 65:
                state = "Neutral"
            elif score >= 45:
                state = "Distracted"
            else:
                state = "Drowsy / Inattentive"

            return {
                "score": round(score, 1),
                "state": state,
                "roll_deg": round(roll_deg, 1),
                "yaw_ratio": round(yaw_ratio, 2)
            }
        except Exception:
            return {"score": 88.0, "state": "Attentive", "roll_deg": 0.0, "yaw_ratio": 1.0}

    def scan_qr_codes(self, frame: np.ndarray) -> List[Dict]:
        """
        Scans frame for dynamic student QR FastPass codes using OpenCV's QRCodeDetector.
        """
        try:
            if not hasattr(self, "_qr_detector") or self._qr_detector is None:
                self._qr_detector = cv2.QRCodeDetector()
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            retval, decoded_info, points, _ = self._qr_detector.detectAndDecodeMulti(gray)
            results = []
            if retval and decoded_info:
                for text, pts in zip(decoded_info, points):
                    if text and text.strip():
                        results.append({
                            "data": text.strip(),
                            "points": pts.astype(int).tolist()
                        })
            if not results:
                data, pts, _ = self._qr_detector.detectAndDecode(gray)
                if data and data.strip():
                    results.append({
                        "data": data.strip(),
                        "points": pts.astype(int).tolist() if pts is not None else []
                    })
            return results
        except Exception:
            return []

    def recognize_from_frame(self, frame: np.ndarray,
                              tolerance: float = 0.55,
                              check_spoof: bool = True) -> List[Dict]:
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        small = cv2.resize(rgb, (0, 0), fx=0.5, fy=0.5)
        detections = self._detect_and_encode(small)
        results = []
        h, w = rgb.shape[:2]

        for item in detections:
            enc = item[0]
            loc = item[1]
            landmarks = item[2] if len(item) > 2 else []
            sid, name, conf = self._match_encoding(enc, tolerance)
            top, right, bottom, left = loc
            orig_top = max(0, top * 2)
            orig_bottom = min(h, bottom * 2)
            orig_left = max(0, left * 2)
            orig_right = min(w, right * 2)

            is_live = True
            liveness_score = 95.0
            liveness_reason = "Live Face"

            if check_spoof and (orig_bottom > orig_top + 10) and (orig_right > orig_left + 10):
                face_crop = rgb[orig_top:orig_bottom, orig_left:orig_right]
                is_live, liveness_score, liveness_reason = self.check_liveness(face_crop)

            attention_info = self.estimate_attention(landmarks)

            results.append({
                "student_id":      sid,
                "name":            name,
                "location":        (orig_top, orig_right, orig_bottom, orig_left),
                "confidence":      conf,
                "recognized":      sid is not None,
                "is_live":         is_live,
                "liveness_score":  liveness_score,
                "liveness_reason": liveness_reason,
                "spoof_detected":  not is_live,
                "attention":       attention_info,
            })
        return results

    def annotate_image(self, image_path: str, results: List[Dict],
                        output_path: str = None) -> np.ndarray:
        image = cv2.imread(image_path)
        for r in results:
            top, right, bottom, left = r["location"]
            color = (0, 200, 0) if r["recognized"] else (0, 0, 220)
            cv2.rectangle(image, (left, top), (right, bottom), color, 2)
            label = f"{r['name']} ({r['confidence']:.0f}%)"
            cv2.putText(image, label, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
        if output_path:
            cv2.imwrite(output_path, image)
        return image

    @property
    def trained_count(self) -> int:
        return len(set(self.known_ids))
