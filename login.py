# login.py
# Nếu không có tham số dòng lệnh -> khởi GUI từ login_modern.py
# Nếu có tham số -> chạy CLI yêu cầu -i/--image

import sys
import argparse

def run_gui():
    try:
        # Import class ModernLoginWindow từ file login_modern.py (cùng thư mục)
        from login_modern import ModernLoginWindow
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        win = ModernLoginWindow()
        win.show()
        sys.exit(app.exec())
    except Exception as e:
        print("Không thể khởi GUI:", e)
        sys.exit(1)

def run_cli(argv):
    parser = argparse.ArgumentParser(description="CLI mode: xử lý ảnh với -i/--image")
    parser.add_argument("-i", "--image", required=True, help="Path to image")
    args = parser.parse_args(argv)
    # Thay bằng logic xử lý ảnh cũ của bạn
    print("CLI mode, image:", args.image)

if __name__ == "__main__":
    # Nếu chạy không có tham số -> mở GUI
    if len(sys.argv) == 1:
        run_gui()
    else:
        run_cli(sys.argv[1:])