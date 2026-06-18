# Hệ Thống Cảnh Báo An Toàn Lao Động (PPE Computer Vision System)

Hệ thống sử dụng thị giác máy tính (YOLO/OpenVINO) để phát hiện và cảnh báo việc tuân thủ trang thiết bị bảo hộ lao động (PPE - Personal Protective Equipment) của công nhân trong thời gian thực. Dự án được phát triển theo kiến trúc MVC (Model-View-Controller) với giao diện PyQt6 hiện đại.

---

## 📌 Thông tin dữ liệu & Model
- **Roboflow Dataset Link:** [Roboflow Dataset - New2806](https://app.roboflow.com/dngs-workspace-hnioc/new2806/1)
- **Model format:** OpenVINO (được tối ưu hóa chạy trên CPU)
- **Các lớp phát hiện cảnh báo:**
  - `Head` (Đầu trần) / `Helmet` (Mũ bảo hộ)
  - `Hands` (Bàn tay trần) / `Gloves` (Găng tay bảo hộ)
  - `Person` (Người) / `Safety-vest` (Áo phản quang)

---

## 🛠️ Cài đặt & Sử dụng

### 1. Cài đặt thư viện cần thiết
Đảm bảo bạn đã cài đặt Python (phiên bản khuyến nghị: 3.9 - 3.11). Cài đặt các thư viện phụ thuộc bằng lệnh:
```bash
pip install -r requirements.txt
```

### 2. Khởi chạy ứng dụng
Chạy file `main.py` để khởi động giao diện người dùng:
```bash
python main.py
```

---

## 📂 Cấu trúc thư mục dự án (MVC Architecture)
- `main.py`: Điểm khởi chạy chương trình.
- `config.py`: Cấu hình chung cho hệ thống (ngưỡng tin cậy, IOU, đường dẫn model, giao diện,...).
- `models/`: Chứa logic xử lý của ứng dụng (xử lý hình ảnh, suy luận mô hình bằng OpenVINO, logic kiểm tra quy định an toàn).
- `views/`: Chứa thiết kế giao diện đồ họa sử dụng PyQt6.
- `controllers/`: Cầu nối điều khiển và xử lý sự kiện giữa `Model` và `View`.
- `exp-2.openvino/`: Thư mục lưu trữ model YOLO dạng OpenVINO đã được convert.
# PPE-COMPUTERVISON-1
# PPE-COMPUTERVISON-1
# PPE-COMPUTERVISON-1
# PPE-COMPUTERVISON-1
