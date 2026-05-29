import cv2
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea,
    QSizePolicy, QSpinBox, QDoubleSpinBox, QGroupBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QSplitter, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QFont, QColor

from config import (
    GIAO_DIEN_SANG, NGUONG_TIN_CAY, NGUONG_IOU, THOI_GIAN_NGHI,
    CANH_BAO_DINH_NGHIA, MAC_DINH_CANH_BAO, CANH_BAO_PHU_THUOC, CAC_LOP
)

class MainView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.on_resize_callback = None
        self._xay_dung_giao_dien()
        
        # Clock timer for UI
        self.dong_ho = QTimer()
        self.dong_ho.timeout.connect(self._cap_nhat_gio)
        self.dong_ho.start(1000)
        self._cap_nhat_gio()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.on_resize_callback:
            self.on_resize_callback(self.khung_video.width(), self.khung_video.height())

    def _xay_dung_giao_dien(self):
        self.setWindowTitle("Hệ Thống Cảnh Báo An Toàn Lao Động")
        self.setMinimumSize(1360, 860)
        self.setStyleSheet(GIAO_DIEN_SANG)

        trung_tam = QWidget()
        self.setCentralWidget(trung_tam)
        bo_cuc_chinh = QVBoxLayout(trung_tam)
        bo_cuc_chinh.setContentsMargins(12, 8, 12, 8)
        bo_cuc_chinh.setSpacing(8)

        hang_tieu_de = QHBoxLayout()
        tieu_de = QLabel("HỆ THỐNG CẢNH BÁO AN TOÀN LAO ĐỘNG")
        tieu_de.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        tieu_de.setStyleSheet("color:#0969da;")

        self.nhan_ngay_gio = QLabel()
        self.nhan_ngay_gio.setFont(QFont("Segoe UI", 13))
        self.nhan_ngay_gio.setStyleSheet(
            "color:#24292f; background:#f6f8fa; border:1px solid #d0d7de;"
            "border-radius:6px; padding:6px 14px;"
        )

        hang_tieu_de.addWidget(tieu_de)
        hang_tieu_de.addStretch()
        hang_tieu_de.addWidget(self.nhan_ngay_gio)
        bo_cuc_chinh.addLayout(hang_tieu_de)

        self.nhan_trang_thai = QLabel("Đang khởi tạo…")
        self.nhan_trang_thai.setObjectName("trang_thai_cho")
        self.nhan_trang_thai.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bo_cuc_chinh.addWidget(self.nhan_trang_thai)

        phan_tren = QSplitter(Qt.Orientation.Horizontal)
        phan_tren.setStyleSheet("QSplitter::handle { background: #d0d7de; width: 2px; }")

        w_video = QWidget()
        bc_video = QVBoxLayout(w_video)
        bc_video.setContentsMargins(0, 0, 0, 0)
        bc_video.setSpacing(6)

        self.khung_video = QLabel()
        self.khung_video.setMinimumSize(640, 400)
        self.khung_video.setStyleSheet(
            "background:#e1e4e8; border:1px solid #d0d7de; border-radius:8px;"
        )
        self.khung_video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.khung_video.setText("Chưa có tín hiệu video")
        self.khung_video.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        bc_video.addWidget(self.khung_video)

        hang_thong_ke = QHBoxLayout()
        self.tk_fps     = self._o_thong_ke("FPS",           "–")
        self.tk_nguoi   = self._o_thong_ke("Người",         "0")
        self.tk_vi_pham = self._o_thong_ke("Vi phạm",       "0", "#cf222e")
        for w in [self.tk_fps, self.tk_nguoi, self.tk_vi_pham]:
            hang_thong_ke.addWidget(w)
        bc_video.addLayout(hang_thong_ke)
        phan_tren.addWidget(w_video)

        w_dieu_khien = QWidget()
        bc_dk = QVBoxLayout(w_dieu_khien)
        bc_dk.setContentsMargins(4, 0, 4, 0)
        bc_dk.setSpacing(6)

        nhom_nguon = QGroupBox("Nguồn Video")
        bc_nguon = QVBoxLayout(nhom_nguon)
        self.nut_camera = QPushButton("Camera Trực Tiếp")
        self.nut_ivcam = QPushButton("Camera iVCam")
        self.nut_video = QPushButton("Mở Tệp Video")
        self.nut_anh = QPushButton("Mở Tệp Ảnh")
        self.nut_link = QPushButton("Mở Từ Đường Dẫn")
        self.o_nhap_link = QLineEdit()
        self.o_nhap_link.setPlaceholderText("http / rtsp ...")
        self.nut_dung = QPushButton("Dừng Giám Sát")
        self.nut_dung.setObjectName("btn_dung")
        self.nut_dung.setEnabled(False)
        bc_nguon.addWidget(self.nut_camera)
        bc_nguon.addWidget(self.nut_ivcam)
        bc_nguon.addWidget(self.nut_video)
        bc_nguon.addWidget(self.nut_anh)
        bc_nguon.addWidget(self.o_nhap_link)
        bc_nguon.addWidget(self.nut_link)
        bc_nguon.addWidget(self.nut_dung)
        bc_dk.addWidget(nhom_nguon)

        nhom_cai_dat = QGroupBox("Cài Đặt Phát Hiện")
        bc_cai_dat = QGridLayout(nhom_cai_dat)
        bc_cai_dat.addWidget(QLabel("Ngưỡng tin cậy:"), 0, 0)
        self.hop_nguong_tc = QDoubleSpinBox()
        self.hop_nguong_tc.setRange(0.1, 0.99)
        self.hop_nguong_tc.setSingleStep(0.05)
        self.hop_nguong_tc.setValue(NGUONG_TIN_CAY)
        bc_cai_dat.addWidget(self.hop_nguong_tc, 0, 1)
        bc_cai_dat.addWidget(QLabel("Ngưỡng IoU:"), 1, 0)
        self.hop_nguong_iou = QDoubleSpinBox()
        self.hop_nguong_iou.setRange(0.1, 0.99)
        self.hop_nguong_iou.setSingleStep(0.05)
        self.hop_nguong_iou.setValue(NGUONG_IOU)
        bc_cai_dat.addWidget(self.hop_nguong_iou, 1, 1)
        bc_cai_dat.addWidget(QLabel("Nghỉ cảnh báo (s):"), 2, 0)
        self.hop_thoi_gian_nghi = QSpinBox()
        self.hop_thoi_gian_nghi.setRange(1, 30)
        self.hop_thoi_gian_nghi.setValue(THOI_GIAN_NGHI)
        bc_cai_dat.addWidget(self.hop_thoi_gian_nghi, 2, 1)
        bc_dk.addWidget(nhom_cai_dat)

        nhom_canh_bao = QGroupBox("Chọn Loại Cảnh Báo")
        bc_canh_bao = QVBoxLayout(nhom_canh_bao)
        self.cac_hop_canh_bao = {}
        set_lop_model = set(CAC_LOP.values())
        for key, dinh_nghia in CANH_BAO_DINH_NGHIA.items():
            hop = QCheckBox(dinh_nghia["mo_ta"])
            hop.setStyleSheet("color:#24292f; font-size:11px; padding:2px;")
            
            # Kiểm tra xem mô hình có hỗ trợ lớp này không
            cac_lop_can = CANH_BAO_PHU_THUOC.get(key, set())
            co_ho_tro = bool(cac_lop_can.intersection(set_lop_model))
            
            hop.setEnabled(co_ho_tro)
            if not co_ho_tro:
                hop.setChecked(False)
                hop.setToolTip("Mô hình hiện tại không hỗ trợ phát hiện lớp này")
                hop.setStyleSheet("color:#8c959f; font-size:11px; padding:2px; text-decoration: line-through;")
            else:
                hop.setChecked(key in MAC_DINH_CANH_BAO)
                
            self.cac_hop_canh_bao[key] = hop
            bc_canh_bao.addWidget(hop)

        hang_chon = QHBoxLayout()
        nut_chon_tat_ca = QPushButton("Chọn tất cả")
        nut_chon_tat_ca.setStyleSheet("font-size:10px; padding:4px 8px;")
        nut_chon_tat_ca.clicked.connect(
            lambda: [hop.setChecked(True) for hop in self.cac_hop_canh_bao.values()]
        )
        nut_bo_chon = QPushButton("Bỏ chọn")
        nut_bo_chon.setStyleSheet("font-size:10px; padding:4px 8px;")
        nut_bo_chon.clicked.connect(
            lambda: [hop.setChecked(False) for hop in self.cac_hop_canh_bao.values()]
        )
        hang_chon.addWidget(nut_chon_tat_ca)
        hang_chon.addWidget(nut_bo_chon)
        bc_canh_bao.addLayout(hang_chon)
        bc_dk.addWidget(nhom_canh_bao)

        nhom_cong_cu = QGroupBox("Công Cụ Nâng Cao")
        bc_cong_cu = QVBoxLayout(nhom_cong_cu)
        self.nut_xuat_csv = QPushButton("Xuất Báo Cáo (CSV)")
        self.hop_am_thanh = QCheckBox("Bật cảnh báo âm thanh")
        self.hop_am_thanh.setChecked(True)
        self.hop_am_thanh.setStyleSheet("color:#24292f; font-size:11px; padding:2px;")
        
        bc_cong_cu.addWidget(self.nut_xuat_csv)
        bc_cong_cu.addWidget(self.hop_am_thanh)
        bc_dk.addWidget(nhom_cong_cu)

        bc_dk.addStretch()

        vung_cuon = QScrollArea()
        vung_cuon.setWidget(w_dieu_khien)
        vung_cuon.setWidgetResizable(True)
        vung_cuon.setMaximumWidth(260)
        vung_cuon.setMinimumWidth(220)
        vung_cuon.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollBar:vertical { width: 6px; }"
            "QScrollBar::handle:vertical { background: #d0d7de; border-radius: 3px; }"
        )
        phan_tren.addWidget(vung_cuon)

        phan_tren.setStretchFactor(0, 4)
        phan_tren.setStretchFactor(1, 1)
        bo_cuc_chinh.addWidget(phan_tren, stretch=3)

        nhom_bang = QGroupBox("📋  LỊCH SỬ VI PHẠM AN TOÀN LAO ĐỘNG")
        nhom_bang.setStyleSheet(
            "QGroupBox {"
            "    border: 1px solid #d0d7de;"
            "    border-radius: 8px;"
            "    margin-top: 14px;"
            "    padding: 10px;"
            "    font-size: 14px;"
            "    font-weight: bold;"
            "    color: #cf222e;"
            "}"
            "QGroupBox::title {"
            "    subcontrol-origin: margin;"
            "    left: 14px;"
            "    padding: 0 6px;"
            "}"
        )
        bc_bang = QVBoxLayout(nhom_bang)
        bc_bang.setSpacing(6)

        self.bang_lich_su = QTableWidget(0, 5)
        self.bang_lich_su.setHorizontalHeaderLabels([
            "STT", "Ngày Giờ", "Loại Vi Phạm", "Số Lượng", "Lý Do Chi Tiết"
        ])

        tieu_de_bang = self.bang_lich_su.horizontalHeader()
        tieu_de_bang.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        tieu_de_bang.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        tieu_de_bang.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        tieu_de_bang.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        tieu_de_bang.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.bang_lich_su.setColumnWidth(0, 55)
        self.bang_lich_su.setColumnWidth(1, 180)
        self.bang_lich_su.setColumnWidth(2, 200)
        self.bang_lich_su.setColumnWidth(3, 90)

        self.bang_lich_su.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.bang_lich_su.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.bang_lich_su.setAlternatingRowColors(True)
        self.bang_lich_su.verticalHeader().setVisible(False)
        self.bang_lich_su.verticalHeader().setDefaultSectionSize(32)
        self.bang_lich_su.setStyleSheet(
            "QTableWidget {"
            "    font-size: 14px;"
            "    alternate-background-color: #f6f8fa;"
            "    background-color: #ffffff;"
            "    color: #24292f;"
            "    gridline-color: #d0d7de;"
            "    border: none;"
            "}"
            "QTableWidget::item:selected {"
            "    background-color: #0969da;"
            "    color: #ffffff;"
            "}"
            "QHeaderView::section {"
            "    background-color: #f6f8fa;"
            "    color: #0969da;"
            "    border: none;"
            "    padding: 8px;"
            "    font-size: 13px;"
            "    font-weight: bold;"
            "}"
        )

        hang_nut = QHBoxLayout()
        hang_nut.addStretch()
        self.nhan_tong = QLabel("Tổng vi phạm: 0")
        self.nhan_tong.setStyleSheet(
            "color:#cf222e; font-size:13px; font-weight:bold;"
        )
        hang_nut.addWidget(self.nhan_tong)
        hang_nut.addStretch()
        self.nut_xoa = QPushButton("🗑  Xóa Toàn Bộ Lịch Sử")
        hang_nut.addWidget(self.nut_xoa)

        bc_bang.addWidget(self.bang_lich_su)
        bc_bang.addLayout(hang_nut)
        bo_cuc_chinh.addWidget(nhom_bang, stretch=2)

    def _o_thong_ke(self, nhan, gia_tri, mau="#24292f"):
        khung = QFrame()
        khung.setStyleSheet(
            "background:#f6f8fa; border:1px solid #d0d7de; border-radius:6px;"
        )
        bc = QVBoxLayout(khung)
        bc.setContentsMargins(8, 4, 8, 4)
        nhan_ten = QLabel(nhan)
        nhan_ten.setStyleSheet("color:#57606a; font-size:10px;")
        nhan_ten.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nhan_so = QLabel(gia_tri)
        nhan_so.setStyleSheet(f"color:{mau}; font-size:16px; font-weight:bold;")
        nhan_so.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bc.addWidget(nhan_ten)
        bc.addWidget(nhan_so)
        khung._nhan_so = nhan_so
        return khung

    def _cap_nhat_gio(self):
        hien_tai = datetime.now()
        self.nhan_ngay_gio.setText(
            "Ngày: " + hien_tai.strftime("%d/%m/%Y") +
            "   Giờ: " + hien_tai.strftime("%H:%M:%S")
        )

    # UI Update methods for Controller to call
    def dat_trang_thai(self, noi_dung, loai="cho"):
        ten_doi_tuong = {
            "tot": "trang_thai_tot",
            "canh_bao": "trang_thai_canh_bao",
            "cho": "trang_thai_cho",
        }
        self.nhan_trang_thai.setObjectName(ten_doi_tuong.get(loai, "trang_thai_cho"))
        self.nhan_trang_thai.setText(noi_dung)
        self.nhan_trang_thai.setStyle(self.nhan_trang_thai.style())

    def cap_nhat_khung_hinh(self, anh_qimage):
        anh_thu_nho = QPixmap.fromImage(anh_qimage)
        self.khung_video.setPixmap(anh_thu_nho)
        
    def xoa_khung_hinh(self):
        self.khung_video.clear()
        self.khung_video.setText("Chưa có tín hiệu video")

    def cap_nhat_thong_ke(self, thong_ke):
        self.tk_fps._nhan_so.setText(f"{thong_ke['fps']:.1f}")
        self.tk_nguoi._nhan_so.setText(str(thong_ke["so_nguoi"]))
        self.tk_vi_pham._nhan_so.setText(str(thong_ke["so_vi_pham"]))

    def them_dong_vi_pham(self, stt, thoi_gian_str, ten_vi_pham, so_luong, ly_do):
        dong = self.bang_lich_su.rowCount()
        self.bang_lich_su.insertRow(dong)

        o_stt = QTableWidgetItem(str(stt))
        o_stt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        o_ngay_gio = QTableWidgetItem(thoi_gian_str)
        o_ngay_gio.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        o_loai = QTableWidgetItem(ten_vi_pham)
        o_loai.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        o_so_luong = QTableWidgetItem(str(so_luong))
        o_so_luong.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        o_ly_do = QTableWidgetItem(ly_do)

        self.bang_lich_su.setItem(dong, 0, o_stt)
        self.bang_lich_su.setItem(dong, 1, o_ngay_gio)
        self.bang_lich_su.setItem(dong, 2, o_loai)
        self.bang_lich_su.setItem(dong, 3, o_so_luong)
        self.bang_lich_su.setItem(dong, 4, o_ly_do)

        for c in range(5):
            muc = self.bang_lich_su.item(dong, c)
            if muc:
                muc.setForeground(QColor("#cf222e"))

        self.bang_lich_su.scrollToBottom()
        self.nhan_tong.setText(f"Tổng vi phạm: {stt}")

    def xoa_bang_lich_su(self):
        self.bang_lich_su.setRowCount(0)
        self.nhan_tong.setText("Tổng vi phạm: 0")

    def lay_canh_bao_bat(self):
        return {
            key for key, hop in self.cac_hop_canh_bao.items()
            if hop.isChecked()
        }
