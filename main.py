import sys
from PyQt6.QtWidgets import QApplication
from views.main_view import MainView
from controllers.main_controller import MainController
from config import DUONG_DAN_MO_HINH

def main():
    print(f"🚀 Khởi động Hệ Thống Cảnh Báo An Toàn Lao Động (MVC Architecture)")
    print(f"📦 Model: {DUONG_DAN_MO_HINH.name}")
    print(f"📂 Đường dẫn: {DUONG_DAN_MO_HINH}\n")
    
    ung_dung = QApplication(sys.argv)
    ung_dung.setStyle("Fusion")
    
    # Khởi tạo View (Giao diện)
    view = MainView()
    
    # Khởi tạo Controller (Điều khiển) và kết nối với View
    controller = MainController(view)
    
    # Hiển thị ứng dụng
    view.show()
    sys.exit(ung_dung.exec())

if __name__ == "__main__":
    main()
