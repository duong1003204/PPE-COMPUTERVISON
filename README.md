# 🛡️ Hệ Thống Cảnh Báo An Toàn Lao Động (PPE Computer Vision System)

Hệ thống sử dụng thị giác máy tính (**YOLOv8/OpenVINO**) để giám sát và cảnh báo thời gian thực việc tuân thủ trang thiết bị bảo hộ lao động (**PPE - Personal Protective Equipment**) của công nhân. 

Dự án được xây dựng dựa trên kiến trúc **MVC (Model-View-Controller)** chuẩn mực, kết hợp giao diện máy tính để bàn hiện đại bằng **PyQt6 (Fusion Style)**.

---

## 🚀 Tính năng nổi bật

* **Nhận diện & Theo dõi Đa Đối Tượng (Multi-Object Tracking):**
  * Sử dụng bộ theo dõi **IoU Tracker** tự phát triển bằng Numpy thuần (tránh lỗi rò rỉ bộ nhớ/nạp lại mô hình liên tục của backend OpenVINO gốc).
  * Gán nhãn ID ổn định trực quan cho từng công nhân theo thứ tự từ trái sang phải.
* **Đánh Giá Vi Phạm Theo Không Gian (Spatial Violation Cross-Checking):**
  * **Mũ bảo hộ (Helmet):** Kiểm tra sự tồn tại của Mũ bảo hộ trong vùng 50% phía trên của khung bảo công nhân.
  * **Áo phản quang (Safety-Vest):** So khớp tỉ lệ chồng lấp (IoU) giữa áo bảo hộ và toàn bộ cơ thể công nhân.
  * **Găng tay bảo hộ (Gloves):** Thuật toán kết hợp kiểm tra độ chồng lấp bàn tay trần và đếm số lượng găng tay so với tổng số bàn tay nhìn thấy để tránh cảnh báo sai.
* **Hệ Thống Phản Hồi Cảnh Báo:**
  * Cooldown cảnh báo tùy chỉnh (giảm spam thông báo/âm thanh cho cùng một ID vi phạm).
  * Bộ đếm lọc nhiễu (xác nhận vi phạm liên tục qua các khung hình để tránh lỗi nhận diện sai nhất thời).
  * Phát tín hiệu âm thanh cảnh báo bằng còi (`winsound.Beep`).
  * Tự động lưu bằng chứng ảnh chụp vi phạm (`anh_vi_pham/`).
* **Đa Dạng Nguồn Đầu Vào:** Hỗ trợ giám sát trực tiếp từ Webcam, camera iVCam, luồng trực tuyến (RTSP/HTTP), hoặc phân tích từ tệp video và hình ảnh tĩnh.
* **Xuất Báo Cáo Chuyên Nghiệp:** Xuất nhật ký vi phạm ra file báo cáo `.csv` kèm mốc thời gian chi tiết và đường dẫn ảnh bằng chứng phục vụ công tác thanh tra.

---

## 📌 Các Lớp Nhận Diện & Định Nghĩa Cảnh Báo

| Tên Lớp Mô Hình | Tên Hiển Thị | Trạng Thái Cảnh Báo | Ghi Chú |
| :--- | :--- | :--- | :--- |
| `Person` | Người | **Không mặc áo bảo hộ** | Nếu thiếu liên kết với `Safety-vest` |
| `Head` | Đầu trần | **Không đội mũ bảo hộ** | Phát hiện đầu trần trong vùng đỉnh đầu công nhân |
| `Hands` | Bàn tay trần | **Không đeo găng tay** | Phát hiện tay không đeo găng |
| `Helmet` | Mũ bảo hộ | *An toàn* | Thiết bị bảo hộ đầu |
| `Gloves` | Găng tay | *An toàn* | Thiết bị bảo hộ tay |
| `Safety-vest` | Áo phản quang | *An toàn* | Thiết bị bảo hộ thân |

---

## 🛠️ Yêu Cầu Hệ Thống & Cài Đặt

### 1. Yêu cầu môi trường
* **Python**: Khuyến nghị phiên bản **3.9 - 3.11**
* **Hệ điều hành**: Windows (để hỗ trợ cảnh báo âm thanh hệ thống qua `winsound`)

### 2. Cài đặt các thư viện phụ thuộc
Mở terminal tại thư mục gốc của dự án và chạy lệnh:
```bash
pip install -r requirements.txt
```

### 3. Cấu hình Model
Đảm bảo mô hình YOLO OpenVINO được lưu trữ tại thư mục mô hình thiết lập trong file `config.py` (Mặc định: `test2/best_int8_openvino_model` hoặc `test2/best_openvino_model`). Thư mục này cần chứa các tệp:
* `openvino_model.xml`
* `openvino_model.bin`
* `metadata.yaml` (lưu tên lớp và thông số cấu hình tối ưu)

### 4. Khởi chạy ứng dụng
Chạy tệp `main.py` để mở giao diện giám sát:
```bash
python main.py
```

---

## 📂 Kiến Trúc Mã Nguồn (MVC Pattern)

```
DATN-CODE - Copy/
├── main.py                # Điểm khởi chạy ứng dụng (Bootstrap)
├── config.py              # Cấu hình ngưỡng tin cậy, màu sắc, stylesheet và ánh xạ lớp
├── requirements.txt       # Danh sách thư viện cần thiết (PyQt6, OpenCV, Ultralytics,...)
├── models/                
│   ├── detector_model.py  # QThread điều phối luồng đọc frame & daemon thread chạy model AI
│   └── safety_policy.py   # Bộ lọc quy định an toàn (Spatial check, cooldown, confirmation)
├── views/                 
│   └── main_view.py       # Thiết kế bố cục giao diện PyQt6 (Bảng lịch sử, khu vực hiển thị, công cụ)
├── controllers/           
│   └── main_controller.py # Bộ điều khiển kết nối tín hiệu từ View sang logic Model
├── utils/                 
│   └── helpers.py         # Hàm bổ trợ lưu ảnh vi phạm bất đồng bộ
├── anh_vi_pham/           # Thư mục tự động tạo để lưu ảnh bằng chứng vi phạm
└── bao_cao/               # Thư mục chứa các file báo cáo CSV xuất ra
```

---

## ⚙️ Hướng Dẫn Git & Triển Khai Repo (Quick Start)

Nếu bạn muốn khởi tạo Git và đẩy dự án này lên GitHub cá nhân của mình, hãy chạy tuần tự các lệnh sau:

### Khởi tạo & Đẩy mã nguồn lên Github
```bash
# Khởi tạo Git repository cục bộ
git init

# Tạo file README.md (nếu chưa có)
echo "# PPE-COMPUTERVISON-1" >> README.md

# Thêm tất cả tệp vào staging area
git add .

# Tạo bản commit đầu tiên
git commit -m "first commit"

# Chuyển nhánh mặc định sang main
git branch -M main

# Liên kết với kho chứa trên GitHub
git remote add origin https://github.com/duong1003204/PPE-COMPUTERVISON.git

# Đẩy code lên GitHub nhánh main
git push -u origin main
```

### Cách cập nhật lại URL nếu cấu hình sai chính tả:
```bash
git remote set-url origin https://github.com/duong1003204/PPE-COMPUTERVISON.git
```
# PPE-COMPUTERVISON-1
