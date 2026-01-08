# login_user_gui.py
# Yêu cầu: PyQt6, opencv-python, numpy, pillow
# pip install PyQt6 opencv-python numpy pillow
#
# Chạy: python login_user_gui.py
#
# Ghi chú: nếu bạn có hàm recognize_plate(frame) trong lp_image.py (trong cùng folder/repo),
# GUI sẽ cố gắng import và gọi nó. Nếu không có, GUI sẽ yêu cầu nhập thủ công biển số.

import sys
import os
import cv2
import time
import datetime
import numpy as np
from PIL import Image
from io import BytesIO

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox,
    QComboBox, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QAbstractItemView, QSplitter, QFormLayout, QSpinBox, QInputDialog
)

# Try to import plate recognizer from repo (lp_image.py)
try:
    from lp_image import recognize_plate  # expected signature: recognize_plate(frame) -> (plate_text, plate_bbox)
    HAS_RECOGNIZER = True
except Exception:
    HAS_RECOGNIZER = False

# Ensure result dir exists
RESULT_DIR = os.path.join(os.getcwd(), "result")
os.makedirs(RESULT_DIR, exist_ok=True)

# Face cascade for face detection (OpenCV built-in path)
FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def save_image_numpy(img_bgr, prefix="capture"):
    """Save BGR numpy image to result folder and return path."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    fname = f"{prefix}_{ts}.jpg"
    path = os.path.join(RESULT_DIR, fname)
    cv2.imwrite(path, img_bgr)
    return path

def cv_frame_to_qpixmap(frame_bgr, max_width=None, max_height=None):
    """Convert cv2 BGR image to QPixmap, optional scaling (preserve aspect)."""
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    pix = QPixmap.fromImage(qimg)
    if max_width or max_height:
        pix = pix.scaled(max_width or w, max_height or h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return pix

class CameraThread(QThread):
    frame_signal = pyqtSignal(object)  # will emit numpy BGR frames
    error_signal = pyqtSignal(str)

    def __init__(self, source):
        super().__init__()
        self.source = source
        self._running = False
        self.cap = None

    def run(self):
        try:
            # If source string can be int, convert to int (local camera index)
            s = self.source
            try:
                s_conv = int(s)
            except Exception:
                s_conv = s
            self.cap = cv2.VideoCapture(s_conv, cv2.CAP_DSHOW if os.name == "nt" else 0)
            if not self.cap.isOpened():
                self.error_signal.emit(f"Không mở được camera: {self.source}")
                return
            self._running = True
            while self._running:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    # small wait, continue
                    time.sleep(0.03)
                    continue
                # emit frame (BGR)
                self.frame_signal.emit(frame)
                # throttle
                time.sleep(0.02)
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass

    def stop(self):
        self._running = False
        self.wait(500)

class CameraWidget(QGroupBox):
    """Widget controlling one camera: source selection, start/stop, preview, capture."""
    def __init__(self, name="Camera"):
        super().__init__(name)
        self.thread = None
        self.last_frame = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        form = QHBoxLayout()

        # Combobox: presets
        self.combo = QComboBox()
        self.combo.addItems(["0", "1", "2", "3", "Custom URL"])
        self.combo.currentTextChanged.connect(self._on_combo_change)
        form.addWidget(QLabel("Source:"))
        form.addWidget(self.combo)

        self.source_edit = QLineEdit("0")
        form.addWidget(self.source_edit)

        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.start_camera)
        form.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_camera)
        self.btn_stop.setEnabled(False)
        form.addWidget(self.btn_stop)

        self.btn_capture = QPushButton("Capture")
        self.btn_capture.clicked.connect(self.capture_once)
        self.btn_capture.setEnabled(False)
        form.addWidget(self.btn_capture)

        layout.addLayout(form)

        # Preview label
        self.preview = QLabel()
        self.preview.setFixedSize(420, 280)
        self.preview.setStyleSheet("background: #222; border-radius: 6px;")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview)

        self.setLayout(layout)

    def _on_combo_change(self, txt):
        if txt == "Custom URL":
            self.source_edit.setText("")
            self.source_edit.setPlaceholderText("rtsp://... or http://... or local file")
        else:
            self.source_edit.setText(txt)

    def start_camera(self):
        src = self.source_edit.text().strip()
        if src == "":
            QMessageBox.warning(self, "Source empty", "Vui lòng nhập source camera (index hoặc URL).")
            return
        # start thread
        if self.thread is not None:
            self.stop_camera()
        self.thread = CameraThread(src)
        self.thread.frame_signal.connect(self._on_frame)
        self.thread.error_signal.connect(self._on_error)
        self.thread.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_capture.setEnabled(True)

    def stop_camera(self):
        if self.thread:
            self.thread.stop()
            self.thread = None
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_capture.setEnabled(False)
        # clear preview
        self.preview.clear()
        self.preview.setText("Stopped")

    def _on_error(self, msg):
        QMessageBox.critical(self, "Camera error", msg)
        self.stop_camera()

    def _on_frame(self, frame):
        # Store last frame and update preview
        self.last_frame = frame
        pix = cv_frame_to_qpixmap(frame, max_width=self.preview.width(), max_height=self.preview.height())
        self.preview.setPixmap(pix)

    def capture_once(self):
        """Emit capture request to main app by returning last_frame or None. Main app will connect to get frame."""
        # This method is used by main app (it will call get_last_frame)
        pass

    def get_last_frame(self):
        return self.last_frame

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("User Dashboard - Camera & LP")
        self.resize(1200, 720)
        self.events = []  # list of dicts: {plate, time, status, face_path, plate_path}
        self.plate_last_status = {}  # plate -> last status ("IN" or "OUT")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        # Top: camera widgets side by side
        cam_layout = QHBoxLayout()
        self.cam1 = CameraWidget("Camera 1")
        self.cam2 = CameraWidget("Camera 2")
        cam_layout.addWidget(self.cam1)
        cam_layout.addWidget(self.cam2)
        main_layout.addLayout(cam_layout)

        # Middle: control buttons (global)
        ctrl_layout = QHBoxLayout()
        self.btn_capture_cam1 = QPushButton("Capture Cam1")
        self.btn_capture_cam1.clicked.connect(lambda: self._capture_from(self.cam1))
        self.btn_capture_cam2 = QPushButton("Capture Cam2")
        self.btn_capture_cam2.clicked.connect(lambda: self._capture_from(self.cam2))
        ctrl_layout.addWidget(self.btn_capture_cam1)
        ctrl_layout.addWidget(self.btn_capture_cam2)

        # Option: auto-capture interval (seconds)
        ctrl_layout.addWidget(QLabel("Auto-capture secs:"))
        self.auto_spin = QSpinBox()
        self.auto_spin.setRange(0, 3600)
        self.auto_spin.setValue(0)
        self.auto_spin.setToolTip("0 = disabled")
        ctrl_layout.addWidget(self.auto_spin)
        self.btn_start_auto = QPushButton("Start Auto")
        self.btn_start_auto.clicked.connect(self._toggle_auto)
        ctrl_layout.addWidget(self.btn_start_auto)

        main_layout.addLayout(ctrl_layout)

        # Table to show events
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Plate", "Time", "Status", "Face", "Plate image"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setIconSize(QSize(160, 80))
        main_layout.addWidget(self.table)

        # Footer instructions
        footer = QLabel("Ghi chú: GUI sẽ cố gắng import recognize_plate(frame) từ lp_image.py nếu tồn tại.")
        main_layout.addWidget(footer)

        self.setLayout(main_layout)

        # Timer for auto-capture
        from PyQt6.QtCore import QTimer
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self._auto_capture_tick)
        self.auto_running = False

    def _toggle_auto(self):
        secs = self.auto_spin.value()
        if secs <= 0:
            QMessageBox.information(self, "Auto capture", "Vui lòng chọn >0 giây để bật auto-capture.")
            return
        if not self.auto_running:
            self.auto_timer.start(secs * 1000)
            self.auto_running = True
            self.btn_start_auto.setText("Stop Auto")
        else:
            self.auto_timer.stop()
            self.auto_running = False
            self.btn_start_auto.setText("Start Auto")

    def _auto_capture_tick(self):
        # capture both cameras if running
        if self.cam1.thread:
            self._capture_from(self.cam1)
        if self.cam2.thread:
            self._capture_from(self.cam2)

    def _capture_from(self, cam_widget):
        frame = cam_widget.get_last_frame()
        if frame is None:
            QMessageBox.warning(self, "No frame", "Chưa có frame từ camera, hãy bấm Start hoặc chờ vài giây.")
            return
        # Run recognition if available
        plate_text = None
        plate_bbox = None
        if HAS_RECOGNIZER:
            try:
                # Expect recognize_plate returns (text, bbox) where bbox is (x,y,w,h) in image coords OR None
                res = recognize_plate(frame)
                if isinstance(res, tuple) and len(res) >= 1:
                    plate_text = res[0]
                    if len(res) >= 2:
                        plate_bbox = res[1]
                elif isinstance(res, str):
                    plate_text = res
            except Exception as e:
                # recognition failed, continue to manual input
                print("Recognizer error:", e)
                plate_text = None

        if not plate_text:
            # ask user to input plate manually
            plate_text, ok = QInputDialog.getText(self, "Nhập biển số", "Không nhận diện được, vui lòng nhập biển số thủ công:")
            if not ok or plate_text.strip() == "":
                # cancelled by user; skip
                return
            plate_text = plate_text.strip()

        # face detection: try to detect face and crop
        face_path = ""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
            if len(faces) > 0:
                # choose largest face
                faces = sorted(faces, key=lambda r: r[2]*r[3], reverse=True)
                x, y, w, h = faces[0]
                face_crop = frame[y:y+h, x:x+w]
                face_path = save_image_numpy(face_crop, prefix="face")
            else:
                # no face detected: save small resized image as fallback
                small = cv2.resize(frame, (300, 200))
                face_path = save_image_numpy(small, prefix="face_fallback")
        except Exception as e:
            print("Face detect error:", e)
            # fallback: save frame
            face_path = save_image_numpy(frame, prefix="face_err")

        # plate image crop: if recognizer returned bbox, try crop; otherwise save full frame or ask user to select
        plate_img_path = ""
        try:
            if plate_bbox:
                x, y, w, h = plate_bbox
                # ensure valid ints and bounds
                h_img, w_img = frame.shape[:2]
                x = max(0, int(x)); y = max(0, int(y)); w = int(w); h = int(h)
                x2 = min(w_img, x + w); y2 = min(h_img, y + h)
                plate_crop = frame[y:y2, x:x2]
                plate_img_path = save_image_numpy(plate_crop, prefix="plate")
            else:
                # save full frame as fallback
                plate_img_path = save_image_numpy(frame, prefix="plate_full")
        except Exception as e:
            print("Plate crop error:", e)
            plate_img_path = save_image_numpy(frame, prefix="plate_err")

        # Determine IN/OUT status: alternate per plate (if last was IN -> OUT; else IN)
        last = self.plate_last_status.get(plate_text)
        if last == "IN":
            status = "OUT"
        else:
            status = "IN"
        self.plate_last_status[plate_text] = status

        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        event = {
            "plate": plate_text,
            "time": ts,
            "status": status,
            "face": face_path,
            "plate_img": plate_img_path
        }
        self.events.insert(0, event)  # newest at top
        self._add_event_row(event)

    def _add_event_row(self, event):
        # Insert at top: row 0
        self.table.insertRow(0)
        r = 0
        self.table.setItem(r, 0, QTableWidgetItem(event["plate"]))
        self.table.setItem(r, 1, QTableWidgetItem(event["time"]))
        self.table.setItem(r, 2, QTableWidgetItem(event["status"]))

        # Face thumbnail
        face_label = QLabel()
        face_pix = QPixmap(event["face"])
        face_pix = face_pix.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        face_label.setPixmap(face_pix)
        face_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(r, 3, face_label)

        # Plate image thumbnail
        plate_label = QLabel()
        plate_pix = QPixmap(event["plate_img"])
        plate_pix = plate_pix.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        plate_label.setPixmap(plate_pix)
        plate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(r, 4, plate_label)

        # Optionally: double-click row to open images
        self.table.cellDoubleClicked.connect(self._on_cell_double)

    def _on_cell_double(self, row, col):
        # open images in external viewer if clicked on image cell
        if col in (3, 4):
            widget = self.table.cellWidget(row, col)
            if isinstance(widget, QLabel) and not widget.pixmap().isNull():
                # find corresponding event (table row 0 == events[0], but rows may reorder; map by plate+time)
                plate = self.table.item(row, 0).text()
                time_str = self.table.item(row, 1).text()
                for ev in self.events:
                    if ev["plate"] == plate and ev["time"] == time_str:
                        path = ev["face"] if col == 3 else ev["plate_img"]
                        if os.path.exists(path):
                            # open with default image viewer
                            try:
                                if sys.platform.startswith("darwin"):
                                    os.system(f"open \"{path}\"")
                                elif os.name == "nt":
                                    os.startfile(path)
                                else:
                                    os.system(f"xdg-open \"{path}\"")
                            except Exception as e:
                                QMessageBox.information(self, "Open image", f"Không mở được: {e}")
                        break

def main():
    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()