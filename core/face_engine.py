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
        """Returns list of (encoding, location=(top,right,bottom,left))."""
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
                    results.append((feat, loc))
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
                results.append((encoding, loc))
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
        encoding, _ = detections[0]
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
                enc, _ = detections[0]
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
        enc, _ = detections[0]
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
        for enc, loc in detections:
            sid, name, conf = self._match_encoding(enc, tolerance)
            top, right, bottom, left = loc
            if scale != 1.0:
                top    = int(top    / scale)
                right  = int(right  / scale)
                bottom = int(bottom / scale)
                left   = int(left   / scale)
            results.append({
                "student_id": sid,
                "name":       name,
                "location":   (top, right, bottom, left),
                "confidence": conf,
                "recognized": sid is not None,
            })
        return results

    def recognize_from_frame(self, frame: np.ndarray,
                              tolerance: float = 0.55) -> List[Dict]:
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        small = cv2.resize(rgb, (0, 0), fx=0.5, fy=0.5)
        detections = self._detect_and_encode(small)
        results = []
        for enc, loc in detections:
            sid, name, conf = self._match_encoding(enc, tolerance)
            top, right, bottom, left = loc
            results.append({
                "student_id": sid,
                "name":       name,
                "location":   (top * 2, right * 2, bottom * 2, left * 2),
                "confidence": conf,
                "recognized": sid is not None,
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
