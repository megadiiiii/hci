# login_modern.py
# Yêu cầu: PyQt6
# Chạy: pip install PyQt6
#       python login_modern.py

import sys
import traceback
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QCheckBox,
    QFrame, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QFont, QCursor, QColor
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint

# Thay bằng kiểm tra thực tế (DB/API)
VALID_CREDENTIALS = {
    "admin": "admin",
    "user": "user"
}

class ModernLoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._drag_pos = None
        self._main_window_ref = None  # giữ reference tới main app nếu mở
        self.setWindowTitle("Đăng nhập - Modern UI")
        self.setFixedSize(480, 340)
        # Frameless để trông hiện đại; thêm khả năng kéo
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._init_ui()
        self._apply_animations()

    def _init_ui(self):
        central = QWidget()
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(20, 20, 20, 20)
        central.setLayout(central_layout)
        self.setCentralWidget(central)

        # Card (white panel)
        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(420, 280)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(30, 20, 30, 20)
        card_layout.setSpacing(12)
        card.setLayout(card_layout)

        # Shadow effect cho card
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 80))
        card.setGraphicsEffect(shadow)

        # Header
        header = QLabel("Chào mừng")
        header.setObjectName("header")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setFixedHeight(40)
        card_layout.addWidget(header)

        # Subtitle
        subtitle = QLabel("Vui lòng đăng nhập để tiếp tục")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        subtitle.setFixedHeight(18)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(6)

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Tên đăng nhập")
        self.username_input.setObjectName("input")
        self.username_input.setFixedHeight(36)
        card_layout.addWidget(self.username_input)

        # Password input + toggle button
        pw_row = QHBoxLayout()
        pw_row.setSpacing(8)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mật khẩu")
        self.password_input.setObjectName("input")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(36)
        pw_row.addWidget(self.password_input)

        self.toggle_pw_btn = QPushButton("👁")
        self.toggle_pw_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_pw_btn.setFixedSize(36, 36)
        self.toggle_pw_btn.setObjectName("iconbtn")
        self.toggle_pw_btn.setToolTip("Hiện/Mở mật khẩu")
        self.toggle_pw_btn.clicked.connect(self._toggle_show_password)
        pw_row.addWidget(self.toggle_pw_btn)

        card_layout.addLayout(pw_row)

        # Remember + forgot
        row = QHBoxLayout()
        self.remember_cb = QCheckBox("Ghi nhớ")
        self.remember_cb.setObjectName("remember")
        row.addWidget(self.remember_cb)
        row.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        forgot = QLabel('<a href="#">Quên mật khẩu?</a>')
        forgot.setOpenExternalLinks(False)
        forgot.linkActivated.connect(self._forgot_pw)
        forgot.setObjectName("link")
        row.addWidget(forgot)
        card_layout.addLayout(row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        self.login_btn = QPushButton("Đăng nhập")
        self.login_btn.setObjectName("primary")
        self.login_btn.setFixedHeight(40)
        self.login_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.login_btn.clicked.connect(self._handle_login)
        self.login_btn.setDefault(True)
        btn_row.addWidget(self.login_btn)

        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.setObjectName("secondary")
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(self.cancel_btn)

        card_layout.addLayout(btn_row)

        footer = QLabel("Built with ❤️  •  PyQt6")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(footer)

        # Center card
        central_layout.addStretch()
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(card)
        hbox.addStretch()
        central_layout.addLayout(hbox)
        central_layout.addStretch()

        # Enter handling
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self._handle_login)

        # Styles
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop:0 #2b5876, stop:1 #4e4376);
        }
        QFrame#card {
            background: rgba(255, 255, 255, 0.98);
            border-radius: 14px;
        }
        QLabel#header {
            font-size: 20px;
            font-weight: 700;
            color: #222;
        }
        QLabel#subtitle {
            font-size: 12px;
            color: #555;
        }
        QLabel#footer {
            font-size: 11px;
            color: #888;
        }
        QLineEdit#input {
            background: #fbfbfd;
            border: 1px solid #e6e6f0;
            border-radius: 8px;
            padding-left: 12px;
            padding-right: 12px;
            font-size: 13px;
            color: #222;
        }
        QLineEdit#input:focus {
            border: 1px solid #6c63ff;
            background: #ffffff;
        }
        QPushButton#primary {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6c63ff, stop:1 #8a79ff);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 6px 12px;
            font-weight: 600;
        }
        QPushButton#primary:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a4df5, stop:1 #7968ff);
        }
        QPushButton#secondary {
            background: transparent;
            border: 1px solid #ddd;
            color: #444;
            border-radius: 8px;
            padding: 6px 12px;
        }
        QPushButton#secondary:hover {
            background: #f6f6fb;
        }
        QPushButton#iconbtn {
            background: transparent;
            border: none;
            font-size: 14px;
        }
        QCheckBox#remember {
            color: #444;
        }
        QLabel#link {
            color: #6c63ff;
            font-size: 12px;
        }
        QLabel#link:hover {
            text-decoration: underline;
        }
        QPushButton:focus { outline: none; }
        """)

    def _apply_animations(self):
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(350)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.anim.start()

    def _toggle_show_password(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_pw_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_pw_btn.setText("👁")

    def _forgot_pw(self):
        QMessageBox.information(self, "Quên mật khẩu", "Chức năng quên mật khẩu chưa được triển khai.")

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên đăng nhập và mật khẩu.")
            return

        if VALID_CREDENTIALS.get(username) == password:
            QMessageBox.information(self, "Thành công", f"Xin chào, {username}!")
            self._open_main_app(username)
        else:
            QMessageBox.critical(self, "Thất bại", "Tên đăng nhập hoặc mật khẩu không đúng.")
            self.password_input.clear()
            self.password_input.setFocus()

    def _open_main_app(self, username):
        """
        Thử import và mở MainWindow từ module login_user_gui.py (nếu có).
        Nếu không có, fallback sang một cửa sổ simple.
        """
        try:
            # Thử import module chứa MainWindow (camera GUI)
            import login_user_gui as usergui
        except Exception as e:
            # show error in console and keep usergui = None so fallback runs
            traceback.print_exc()
            QMessageBox.warning(self, "Lỗi import", f"Không thể import login_user_gui.py:\n{e}")
            usergui = None

        if usergui and hasattr(usergui, "MainWindow"):
            try:
                # Reuse QApplication hiện có
                app = QApplication.instance() or QApplication(sys.argv)
                main_win = usergui.MainWindow()
                main_win.setWindowTitle("Main App - Camera")
                main_win.show()
                # Giữ tham chiếu để không bị GC
                self._main_window_ref = main_win
                # Ẩn login thay vì đóng để tránh mất styling hoặc exit app
                self.hide()
                return
            except Exception as e:
                traceback.print_exc()
                QMessageBox.warning(self, "Lỗi mở GUI chính", f"Lỗi khi mở MainWindow từ login_user_gui.py:\n{e}")

        # Fallback: nếu không có login_user_gui.MainWindow, dùng simple main
        try:
            main = QMainWindow()
            main.setWindowTitle("Main App")
            main.resize(640, 420)
            lbl = QLabel(f"Bạn đã đăng nhập với: {username}", alignment=Qt.AlignmentFlag.AlignCenter)
            font = QFont()
            font.setPointSize(14)
            lbl.setFont(font)
            main.setCentralWidget(lbl)
            main.show()
            # Giữ ref và ẩn login
            self._main_window_ref = main
            self.hide()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Lỗi", f"Không thể mở cửa sổ chính: {e}")

    # Window drag support for frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

# python
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="login_modern: GUI (default) or CLI with -i/--image")
    parser.add_argument("-i", "--image", help="Path to image (optional). If provided, CLI mode is used.", required=False)
    args = parser.parse_args()

    if args.image:
        # CLI mode: handle image and exit (replace with your processing)
        print("CLI mode, image:", args.image)
        sys.exit(0)
    else:
        # GUI mode (default when no -i)
        app = QApplication(sys.argv)
        app.setFont(QFont("Segoe UI", 10))
        win = ModernLoginWindow()
        win.show()
        sys.exit(app.exec())