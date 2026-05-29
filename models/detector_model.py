import cv2
import time
import numpy as np
import threading
from collections import deque
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
from config import (
    DUONG_DAN_MO_HINH, CAC_LOP,
    MAC_DINH_CANH_BAO, NGUONG_TIN_CAY, NGUONG_IOU, 
    THOI_GIAN_NGHI, KICH_THUOC_ANH,
)
from models.safety_policy import SafetyPolicy

try:
    from ultralytics import YOLO
    YOLO_SAN_SANG = True
except ImportError:
    YOLO_SAN_SANG = False

def tai_mo_hinh():
    if not YOLO_SAN_SANG:
        return None, "Chưa cài ultralytics! Chạy: pip install ultralytics"
    if not DUONG_DAN_MO_HINH.exists():
        return None, f"Không tìm thấy mô hình: {DUONG_DAN_MO_HINH}"
    try:
        mo_hinh = YOLO(str(DUONG_DAN_MO_HINH), task='detect')
        # Warmup model with a dummy image for instant initial inference
        dummy_img = np.zeros((KICH_THUOC_ANH, KICH_THUOC_ANH, 3), dtype=np.uint8)
        mo_hinh(dummy_img, conf=0.5, iou=0.5, imgsz=(KICH_THUOC_ANH, KICH_THUOC_ANH), verbose=False, device='cpu')
        return mo_hinh, None
    except Exception as e:
        return None, f"Lỗi tải mô hình: {e}"


def _letterbox_nearest(khung, size=640, color=(114, 114, 114)):
    h, w = khung.shape[:2]
    r = size / max(h, w)
    new_w, new_h = int(w * r), int(h * r)
    khung_nho = cv2.resize(khung, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
    
    top = (size - new_h) // 2
    bottom = size - new_h - top
    left = (size - new_w) // 2
    right = size - new_w - left
    
    khung_padded = cv2.copyMakeBorder(
        khung_nho, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=color
    )
    return khung_padded, r, (left, top)


class LuongPhatHien(QThread):
    tin_hieu_khung_hinh = pyqtSignal(QImage, list)
    tin_hieu_vi_pham    = pyqtSignal(np.ndarray, list)
    tin_hieu_thong_ke   = pyqtSignal(dict)
    tin_hieu_loi        = pyqtSignal(str)

    def __init__(self, nguon, mo_hinh, nguong_tin_cay=NGUONG_TIN_CAY,
                 nguong_iou=NGUONG_IOU, thoi_gian_nghi=THOI_GIAN_NGHI, cac_canh_bao_bat=None):
        super().__init__()
        self.nguon = nguon
        self.mo_hinh = mo_hinh
        self.nguong_tin_cay = nguong_tin_cay
        self.nguong_iou = nguong_iou
        self.thoi_gian_nghi = thoi_gian_nghi
        self.cac_canh_bao_bat = cac_canh_bao_bat or set(MAC_DINH_CANH_BAO)
        self._dang_chay = True
        self._lan_canh_bao_cuoi = 0.0
        self.thong_ke = {
            "so_khung": 0, "so_vi_pham": 0, "fps": 0.0,
            "so_nguoi": 0, "so_mu": 0, "so_ao": 0,
        }
        self.policy = SafetyPolicy(self.cac_canh_bao_bat)
        
        # Cấu hình kích thước hiển thị mục tiêu (Controller cập nhật để khớp với QLabel của View)
        self.kich_thuoc_hien_thi = (960, 540)
        
        # Cơ chế Asynchronous Inference với 1 thread duy nhất dùng Condition
        self.lock = threading.Lock()
        self.ai_busy = False
        self.cac_doi_tuong_moi_nhat = []
        
        self.bo_dem_fps = deque(maxlen=30)
        self._cv_ai = threading.Condition()
        self._khung_cho_ai = None
        self._ai_chay = True
        self._thread_ai = threading.Thread(
            target=self._vong_lap_inference_ngam,
            daemon=True
        )
        self._thread_ai.start()

    def dung_lai(self):
        self._dang_chay = False
        self._ai_chay = False
        with self._cv_ai:
            self._cv_ai.notify_all()

    def _la_anh(self):
        if isinstance(self.nguon, str):
            return self.nguon.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))
        return False

    @staticmethod
    def _doc_anh_unicode(duong_dan):
        du_lieu = np.fromfile(duong_dan, dtype=np.uint8)
        return cv2.imdecode(du_lieu, cv2.IMREAD_COLOR)

    def _vong_lap_inference_ngam(self):
        while self._dang_chay and self._ai_chay:
            with self._cv_ai:
                while self._khung_cho_ai is None and self._dang_chay and self._ai_chay:
                    self._cv_ai.wait(timeout=0.1)
                if not self._dang_chay or not self._ai_chay:
                    break
                khung_ai = self._khung_cho_ai
                self._khung_cho_ai = None
            
            self._chay_inference_ngam(khung_ai, self.bo_dem_fps)

    def run(self):
        if self._la_anh():
            khung = self._doc_anh_unicode(self.nguon)
            if khung is None:
                self.tin_hieu_loi.emit(f"Không thể đọc ảnh: {self.nguon}")
                return
            # Chạy inference đồng bộ trực tiếp trên thread này để đảm bảo có kết quả trước khi hiển thị
            self._chay_inference_ngam(khung.copy(), self.bo_dem_fps)
            self._xu_ly_khung(khung)
            return

        cap = cv2.VideoCapture(self.nguon)
        if not cap.isOpened():
            self.tin_hieu_loi.emit(f"Không thể mở nguồn video: {self.nguon}")
            return

        if isinstance(self.nguon, int) or (isinstance(self.nguon, str) and self.nguon.isdigit()):
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Điều khiển tốc độ phát video nếu nguồn là tệp video local
        is_video_file = isinstance(self.nguon, str) and not self._la_anh()
        fps_nguon = 30.0
        if is_video_file:
            fps_nguon = cap.get(cv2.CAP_PROP_FPS)
            if fps_nguon <= 0:
                fps_nguon = 30.0
        thoi_gian_khung = 1.0 / fps_nguon if is_video_file else 0.0

        while self._dang_chay:
            t_bat_dau = time.perf_counter()
            ok, khung = cap.read()
            if not ok:
                if isinstance(self.nguon, str):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
            self._xu_ly_khung(khung)
            
            # Khống chế tốc độ hiển thị video
            if thoi_gian_khung > 0:
                tg_da_qua = time.perf_counter() - t_bat_dau
                tg_cho = thoi_gian_khung - tg_da_qua
                if tg_cho > 0:
                    time.sleep(tg_cho)
                    
        cap.release()

    def _xu_ly_khung(self, khung):
        # 1. Lấy kết quả nhận diện mới nhất
        with self.lock:
            cac_doi_tuong_ve = list(self.cac_doi_tuong_moi_nhat)

        cac_vi_pham = self.policy.evaluate(cac_doi_tuong_ve)

        # 2. Gửi khung hình sạch cho thread AI xử lý ngầm (không tạo thread mới)
        if not self.ai_busy:
            self.ai_busy = True
            with self._cv_ai:
                self._khung_cho_ai = khung.copy()
                self._cv_ai.notify()

        # 3. Vẽ đè khung nhận diện và vi phạm lên khung hình hiển thị
        self.policy.annotate_frame(khung, cac_doi_tuong_ve, cac_vi_pham)

        # 4. Tối ưu: Resize và chuyển đổi BGR->RGB trên thread phụ
        rgb = cv2.cvtColor(khung, cv2.COLOR_BGR2RGB)
        cao, rong, _ = rgb.shape
        w_max, h_max = self.kich_thuoc_hien_thi
        
        if rong > w_max or cao > h_max:
            scale = min(w_max / rong, h_max / cao)
            new_w = int(rong * scale)
            new_h = int(cao * scale)
            rgb = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
            cao, rong, _ = rgb.shape
            
        # Copy dữ liệu để QImage sở hữu vùng nhớ riêng an toàn khi truyền tín hiệu
        q_image = QImage(rgb.data, rong, cao, 3 * rong, QImage.Format.Format_RGB888).copy()

        self.tin_hieu_khung_hinh.emit(q_image, cac_doi_tuong_ve)
        
        # Chỉ thông báo vi phạm nếu vi phạm xảy ra và hết thời gian chờ nguội
        hien_tai = time.perf_counter()
        if cac_vi_pham and (hien_tai - self._lan_canh_bao_cuoi) >= self.thoi_gian_nghi:
            self._lan_canh_bao_cuoi = hien_tai
            self.thong_ke["so_vi_pham"] += len(cac_vi_pham)
            self.tin_hieu_vi_pham.emit(khung.copy(), cac_vi_pham)

    def _chay_inference_ngam(self, khung_ai, bo_dem_fps):
        t1 = time.perf_counter()
        try:
            cao_goc, rong_goc = khung_ai.shape[:2]
            kich_thuoc_ai = KICH_THUOC_ANH
            
            # Sử dụng letterbox_nearest tự thiết kế để chuẩn hóa ảnh vuông mà không làm méo tỉ lệ
            khung_nho, r, (left, top) = _letterbox_nearest(khung_ai, kich_thuoc_ai)

            # Chạy inference mô hình OpenVINO trên CPU với shape vuông cố định
            ket_qua = self.mo_hinh(
                khung_nho, conf=self.nguong_tin_cay,
                iou=self.nguong_iou, verbose=False,
                imgsz=(kich_thuoc_ai, kich_thuoc_ai), half=False,
                device='cpu'
            )[0]

            cac_doi_tuong = []
            so_nguoi = so_mu = so_ao = 0
            boxes = ket_qua.boxes
            if len(boxes) > 0:
                # Chuyển dữ liệu sang numpy để thực hiện tính toán vector hóa nhanh gấp nhiều lần vòng lặp Python
                xyxy_np = boxes.xyxy.cpu().numpy()
                cls_np = boxes.cls.cpu().numpy().astype(int)
                conf_np = boxes.conf.cpu().numpy()

                # Phép dịch chuyển và nhân ma trận song song hóa trên numpy (tránh overhead tính toán trên CPU)
                xyxy_np[:, [0, 2]] = (xyxy_np[:, [0, 2]] - left) / r
                xyxy_np[:, [1, 3]] = (xyxy_np[:, [1, 3]] - top) / r
                
                # Giới hạn tọa độ trong biên ảnh gốc để tránh sai số làm tràn khung
                xyxy_np[:, [0, 2]] = np.clip(xyxy_np[:, [0, 2]], 0, rong_goc - 1)
                xyxy_np[:, [1, 3]] = np.clip(xyxy_np[:, [1, 3]], 0, cao_goc - 1)
                xyxy_scaled = xyxy_np.astype(int)

                for i in range(len(cls_np)):
                    ma_lop = cls_np[i]
                    ten_lop = CAC_LOP.get(ma_lop, "khong_xac_dinh")
                    do_tin_cay = float(conf_np[i])
                    
                    x1, y1, x2, y2 = xyxy_scaled[i]
                    cac_doi_tuong.append({
                        "lop": ten_lop, "do_tin_cay": do_tin_cay,
                        "khung_bao": (x1, y1, x2, y2), "track_id": None,
                    })
                    if ten_lop == "Person":        so_nguoi += 1
                    elif ten_lop == "Helmet":      so_mu    += 1
                    elif ten_lop == "Safety-vest": so_ao    += 1

            # Đánh số ID cho các đối tượng Person phát hiện được
            idx_nguoi = 1
            for dt in cac_doi_tuong:
                if dt["lop"] == "Person":
                    dt["track_id"] = idx_nguoi
                    idx_nguoi += 1

            # Cập nhật kết quả AI mới nhất dưới sự bảo vệ của lock thread-safe
            with self.lock:
                self.cac_doi_tuong_moi_nhat = cac_doi_tuong

            self.thong_ke["so_nguoi"] = so_nguoi
            self.thong_ke["so_mu"]    = so_mu
            self.thong_ke["so_ao"]    = so_ao
            
        except Exception as e:
            print(f"[Warning] Lỗi khi nhận diện background: {e}")
        finally:
            t2 = time.perf_counter()
            fps_hien_tai = 1.0 / max(t2 - t1, 1e-6)
            if bo_dem_fps is not None:
                bo_dem_fps.append(fps_hien_tai)
                self.thong_ke["fps"] = sum(bo_dem_fps) / len(bo_dem_fps)
            else:
                self.thong_ke["fps"] = fps_hien_tai
            self.thong_ke["so_khung"] += 1
            
            # Gửi tín hiệu thông báo thống kê mới cập nhật sang UI
            self.tin_hieu_thong_ke.emit(self.thong_ke)
            self.ai_busy = False
