import os
import csv
import threading
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QDialog, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import QObject, Qt
from PyQt6.QtGui import QPixmap

from models.detector_model import LuongPhatHien, tai_mo_hinh
from utils.helpers import luu_anh_vi_pham
from config import THU_MUC_BAO_CAO, TEN_HIEN_THI

try:
    import winsound
    CO_AM_THANH = True
except ImportError:
    CO_AM_THANH = False

class MainController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self.mo_hinh = None
        self.luong = None
        self.nhat_ky_vi_pham = []
        self.am_thanh_bat = True
        self.duong_dan_anh_cuoi = None
        
        self._ket_noi_tin_hieu()
        self._tai_mo_hinh()
        self.view.on_resize_callback = self._khi_giao_dien_resize

    def _ket_noi_tin_hieu(self):
        self.view.nut_camera.clicked.connect(self._bat_dau_camera)
        self.view.nut_ivcam.clicked.connect(self._bat_dau_ivcam)
        self.view.nut_video.clicked.connect(self._mo_video)
        self.view.nut_anh.clicked.connect(self._mo_anh)
        self.view.nut_link.clicked.connect(self._mo_tu_link)
        self.view.nut_dung.clicked.connect(self._dung_lai)
        self.view.nut_xuat_csv.clicked.connect(self._xuat_bao_cao)
        self.view.nut_xoa.clicked.connect(self._xoa_lich_su)
        self.view.bang_lich_su.cellDoubleClicked.connect(self._xem_anh_vi_pham)
        
        # Audio setting
        self.view.hop_am_thanh.stateChanged.connect(
            lambda state: setattr(self, 'am_thanh_bat', state == Qt.CheckState.Checked.value)
        )
        
        # Ensure we stop the thread when closing
        self.view.closeEvent = self._khi_dong_cua_so

    def _tai_mo_hinh(self):
        self.view.dat_trang_thai("Đang tải mô hình…", "cho")
        mo_hinh, loi = tai_mo_hinh()
        if loi:
            self.view.dat_trang_thai(loi, "cho")
            return
        self.mo_hinh = mo_hinh
        self.view.dat_trang_thai("✔ Mô hình đã sẵn sàng — Chọn nguồn video để bắt đầu", "tot")
        
    def _bat_dau_camera(self):
        self._khoi_chay(0)

    def _bat_dau_ivcam(self):
        self._khoi_chay(1)

    def _mo_video(self):
        duong_dan, _ = QFileDialog.getOpenFileName(
            self.view, "Chọn Tệp Video", "",
            "Video (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        if duong_dan:
            self._khoi_chay(duong_dan)

    def _mo_anh(self):
        duong_dan, _ = QFileDialog.getOpenFileName(
            self.view, "Chọn Tệp Ảnh", "",
            "Ảnh (*.jpg *.jpeg *.png *.bmp)"
        )
        if duong_dan:
            self._khoi_chay(duong_dan)

    def _mo_tu_link(self):
        link = self.view.o_nhap_link.text().strip()
        if not link:
            QMessageBox.warning(
                self.view, "Thiếu đường dẫn",
                "Vui lòng nhập đường dẫn video vào ô phía trên."
            )
            return
        self._khoi_chay(link)

    def _khoi_chay(self, nguon):
        self._dung_lai()
        if not self.mo_hinh:
            QMessageBox.critical(
                self.view, "Chưa tải được mô hình",
                "Mô hình AI chưa được tải thành công. Vui lòng kiểm tra lại đường dẫn model hoặc khởi động lại ứng dụng."
            )
            return
            
        canh_bao_bat = self.view.lay_canh_bao_bat()
        if not canh_bao_bat:
            QMessageBox.warning(
                self.view, "Thiếu cảnh báo",
                "Vui lòng chọn ít nhất 1 loại cảnh báo trước khi bắt đầu giám sát."
            )
            return

            
        # Accessing view's spinboxes for parameters
        nguong_tc = self.view.hop_nguong_tc.value()
        nguong_iou = self.view.hop_nguong_iou.value()
        thoi_gian_nghi = self.view.hop_thoi_gian_nghi.value()

        self.luong = LuongPhatHien(
            nguon, self.mo_hinh,
            nguong_tin_cay=nguong_tc,
            nguong_iou=nguong_iou,
            thoi_gian_nghi=thoi_gian_nghi,
            cac_canh_bao_bat=canh_bao_bat,
        )
        self.luong.kich_thuoc_hien_thi = (self.view.khung_video.width(), self.view.khung_video.height())
        self.luong.tin_hieu_khung_hinh.connect(self._khi_co_khung_hinh)
        self.luong.tin_hieu_vi_pham.connect(self._khi_co_vi_pham)
        self.luong.tin_hieu_thong_ke.connect(self._khi_co_thong_ke)
        self.luong.tin_hieu_loi.connect(
            lambda loi: self.view.dat_trang_thai(f"⚠ {loi}", "cho")
        )
        self.luong.start()
        
        # Toggle UI states
        self.view.nut_dung.setEnabled(True)
        self.view.nut_camera.setEnabled(False)
        self.view.nut_ivcam.setEnabled(False)
        self.view.nut_video.setEnabled(False)
        self.view.nut_anh.setEnabled(False)
        self.view.nut_link.setEnabled(False)
        self.view.dat_trang_thai("🔴 Đang giám sát…", "tot")

    def _dung_lai(self):
        if self.luong and self.luong.isRunning():
            self.luong.dung_lai()
            self.luong.wait()
        self.luong = None
        
        self.view.nut_dung.setEnabled(False)
        self.view.nut_camera.setEnabled(True)
        self.view.nut_ivcam.setEnabled(True)
        self.view.nut_video.setEnabled(True)
        self.view.nut_anh.setEnabled(True)
        self.view.nut_link.setEnabled(True)
        self.view.dat_trang_thai("⏹ Đã dừng — Chọn nguồn video để tiếp tục", "cho")
        self.view.xoa_khung_hinh()

    def _khi_co_khung_hinh(self, anh_qimage, cac_doi_tuong):
        self.view.cap_nhat_khung_hinh(anh_qimage)

    def _khi_giao_dien_resize(self, w, h):
        if self.luong:
            self.luong.kich_thuoc_hien_thi = (w, h)

    def _khi_co_thong_ke(self, thong_ke):
        self.view.cap_nhat_thong_ke(thong_ke)
        if thong_ke["so_vi_pham"] > 0:
            self.view.dat_trang_thai("⚠ PHÁT HIỆN VI PHẠM AN TOÀN LAO ĐỘNG!", "canh_bao")

    def _khi_co_vi_pham(self, khung, cac_vi_pham):
        thoi_gian = datetime.now()
        
        def _luu_anh_trong_thread():
            duong_dan_anh = luu_anh_vi_pham(khung)
            self.duong_dan_anh_cuoi = duong_dan_anh
        
        threading.Thread(target=_luu_anh_trong_thread, daemon=True).start()

        if self.am_thanh_bat and CO_AM_THANH:
            threading.Thread(
                target=lambda: winsound.Beep(1000, 400), daemon=True
            ).start()

        ten_vi_pham = ", ".join({
            TEN_HIEN_THI.get(v["lop"], v["lop"]) for v in cac_vi_pham
        })
        ly_do = ", ".join({
            v.get("ly_do", "") for v in cac_vi_pham if v.get("ly_do")
        })
        so_luong = len(cac_vi_pham)

        dong_hien_tai = self.view.bang_lich_su.rowCount()
        stt = dong_hien_tai + 1
        
        thoi_gian_str = thoi_gian.strftime("%d/%m/%Y  %H:%M:%S")
        self.view.them_dong_vi_pham(stt, thoi_gian_str, ten_vi_pham, so_luong, ly_do)

        self.nhat_ky_vi_pham.append({
            "thoi_gian": thoi_gian,
            "vi_pham": cac_vi_pham,
            "duong_dan_anh": str(self.duong_dan_anh_cuoi) if self.duong_dan_anh_cuoi else "",
        })

    def _xoa_lich_su(self):
        self.nhat_ky_vi_pham.clear()
        self.view.xoa_bang_lich_su()

    def _xuat_bao_cao(self):
        if not self.nhat_ky_vi_pham:
            QMessageBox.information(
                self.view, "Trống",
                "Chưa có dữ liệu vi phạm để xuất báo cáo."
            )
            return

        thoi_gian = datetime.now().strftime("%Y%m%d_%H%M%S")
        ten_file = THU_MUC_BAO_CAO / f"bao_cao_vi_pham_{thoi_gian}.csv"

        try:
            with open(str(ten_file), "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "STT", "Ngày Giờ", "Loại Vi Phạm",
                    "Số Lượng", "Lý Do Chi Tiết", "Đường Dẫn Ảnh"
                ])
                for idx, ban_ghi in enumerate(self.nhat_ky_vi_pham, start=1):
                    tg = ban_ghi["thoi_gian"].strftime("%d/%m/%Y %H:%M:%S")
                    ten_vp = ", ".join({
                        TEN_HIEN_THI.get(v["lop"], v["lop"])
                        for v in ban_ghi["vi_pham"]
                    })
                    ly_do = ", ".join({
                        v.get("ly_do", "")
                        for v in ban_ghi["vi_pham"] if v.get("ly_do")
                    })
                    sl = len(ban_ghi["vi_pham"])
                    anh = ban_ghi.get("duong_dan_anh", "")
                    writer.writerow([idx, tg, ten_vp, sl, ly_do, anh])

            QMessageBox.information(
                self.view, "Thành công",
                f"Đã xuất báo cáo thành công!\nFile: {ten_file}"
            )
            os.startfile(str(THU_MUC_BAO_CAO))
        except Exception as e:
            QMessageBox.critical(
                self.view, "Lỗi",
                f"Không thể xuất báo cáo: {e}"
            )

    def _xem_anh_vi_pham(self, dong, cot):
        if dong < 0 or dong >= len(self.nhat_ky_vi_pham):
            return

        ban_ghi = self.nhat_ky_vi_pham[dong]
        duong_dan = ban_ghi.get("duong_dan_anh", "")

        if not duong_dan or not Path(duong_dan).exists():
            QMessageBox.warning(
                self.view, "Không tìm thấy",
                "Không tìm thấy ảnh vi phạm cho dòng này."
            )
            return

        dialog = QDialog(self.view)
        dialog.setWindowTitle(
            f"Bằng chứng vi phạm #{dong + 1} - "
            f"{ban_ghi['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S')}"
        )
        dialog.setMinimumSize(800, 600)
        dialog.setStyleSheet("background-color: #0d1117;")

        bc = QVBoxLayout(dialog)

        ly_do = ", ".join({
            v.get("ly_do", "") for v in ban_ghi["vi_pham"] if v.get("ly_do")
        })
        nhan_ly_do = QLabel(ly_do if ly_do else "Vi phạm an toàn lao động")
        nhan_ly_do.setStyleSheet(
            "color:#f85149; font-size:16px; font-weight:bold; padding:8px;"
        )
        nhan_ly_do.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bc.addWidget(nhan_ly_do)

        pixmap = QPixmap(duong_dan)
        nhan_anh = QLabel()
        nhan_anh.setPixmap(pixmap.scaled(
            780, 520,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        nhan_anh.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bc.addWidget(nhan_anh)

        nut_dong = QPushButton("Đóng")
        nut_dong.setStyleSheet(
            "background:#21262d; color:#e6edf3; border:1px solid #30363d;"
            "border-radius:6px; padding:8px 24px; font-size:13px;"
        )
        nut_dong.clicked.connect(dialog.close)
        bc.addWidget(nut_dong, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.exec()

    def _khi_dong_cua_so(self, event):
        self._dung_lai()
        event.accept()
