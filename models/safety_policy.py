import cv2
import numpy as np
from config import (
    MAU_LOP, CANH_BAO_DINH_NGHIA, MAC_DINH_CANH_BAO
)

_MAU_TRANG = (255, 255, 255)
_MAU_TRUNG_TINH = (160, 160, 160)
_MAU_VIEN_DO = (0, 0, 230)
_FONT_CV = cv2.FONT_HERSHEY_SIMPLEX

_SET_AO_BH = frozenset({"Safety-vest"})
_SET_AO_HIEN_THI = frozenset({"Safety-vest"})

_LY_DO_MAP = {
    "Head": "NO HELMET", "Hands": "NO GLOVES"
}
_SET_BO_PHAN = frozenset(_LY_DO_MAP.keys())

_NHAN_TRANG_BI = {
    "Helmet": "HELMET", "Gloves": "GLOVES"
}

def _co_trung_nhau(hop_a, hop_b):
    cx_b = (hop_b[0] + hop_b[2]) * 0.5
    rong_a = hop_a[2] - hop_a[0]
    mo_rong = rong_a * 0.3
    if not ((hop_a[0] - mo_rong) <= cx_b <= (hop_a[2] + mo_rong)):
        return False
    return hop_a[1] < hop_b[3] and hop_b[1] < hop_a[3]

def _ve_nhan(khung, noi_dung, x, y, mau_nen, co_chu=0.45, do_day=1):
    (w, h), _ = cv2.getTextSize(noi_dung, _FONT_CV, co_chu, do_day)
    cv2.rectangle(khung, (x, y - h - 4), (x + w + 4, y + 2), mau_nen, -1)
    cv2.putText(khung, noi_dung, (x + 2, y - 2),
                _FONT_CV, co_chu, _MAU_TRANG, do_day, cv2.LINE_AA)

class SafetyPolicy:
    def __init__(self, cac_canh_bao_bat=None):
        self.cac_canh_bao_bat = cac_canh_bao_bat or set(MAC_DINH_CANH_BAO)
        self.vi_pham_bo_phan = {}
        self.kiem_tra_ao = False
        self.ly_do_ao = "NO VEST/SUIT"
        
        # Ánh xạ từ cảnh báo bật sang lớp và lý do vi phạm tương ứng
        for key in self.cac_canh_bao_bat:
            dinh_nghia = CANH_BAO_DINH_NGHIA.get(key)
            if not dinh_nghia:
                continue
            if dinh_nghia["lop"] == "Person":
                self.kiem_tra_ao = True
                self.ly_do_ao = dinh_nghia["ly_do"]
            else:
                self.vi_pham_bo_phan[dinh_nghia["lop"]] = dinh_nghia["ly_do"]
                
        self.lop_vi_pham_bat = frozenset(self.vi_pham_bo_phan.keys())
        
        # Thiết lập các bộ phận cần bảo vệ và loại trang bị tương ứng
        self.bang_trang_bi = {
            "Head": {"Helmet"},
            "Hands": {"Gloves"}
        }

    def evaluate(self, cac_doi_tuong):
        cac_vi_pham = []
        
        # Nhóm đối tượng theo lớp để truy xuất O(1) nhanh chóng
        doi_tuong_theo_lop = {}
        for d in cac_doi_tuong:
            lop = d["lop"]
            if lop not in doi_tuong_theo_lop:
                doi_tuong_theo_lop[lop] = []
            doi_tuong_theo_lop[lop].append(d)

        ds_nguoi = doi_tuong_theo_lop.get("Person", [])
        
        # Gom danh sách áo bảo hộ hiện có
        ds_ao = []
        for ao_lop in _SET_AO_BH:
            if ao_lop in doi_tuong_theo_lop:
                ds_ao.extend(doi_tuong_theo_lop[ao_lop])

        # 1. Kiểm tra các bộ phận (Đầu, Tay) xem có trang bị bảo hộ (Mũ, Găng) che phủ không
        for lop in self.vi_pham_bo_phan:
            if lop not in doi_tuong_theo_lop:
                continue
            set_trang_bi_can_co = self.bang_trang_bi.get(lop, set())
            
            # Lấy danh sách trang bị bảo vệ tương ứng đang có trong khung hình
            ds_trang_bi = []
            for tb_lop in set_trang_bi_can_co:
                if tb_lop in doi_tuong_theo_lop:
                    ds_trang_bi.extend(doi_tuong_theo_lop[tb_lop])
            
            for dt in doi_tuong_theo_lop[lop]:
                co_trang_bi = False
                for tb in ds_trang_bi:
                    if _co_trung_nhau(dt["khung_bao"], tb["khung_bao"]):
                        co_trang_bi = True
                        break
                
                # Nếu không có trang bị bảo vệ -> cảnh báo vi phạm
                if not co_trang_bi:
                    so_nguoi = None
                    kb = dt["khung_bao"]
                    # Ánh xạ bộ phận này thuộc về người nào dựa vào không gian trùng lắp
                    for nguoi in ds_nguoi:
                        if _co_trung_nhau(nguoi["khung_bao"], kb):
                            so_nguoi = nguoi.get("track_id")
                            break
                    ly_do_goc = self.vi_pham_bo_phan[lop]
                    ly_do = f"ID:{so_nguoi} - {ly_do_goc}" if so_nguoi else ly_do_goc
                    cac_vi_pham.append({
                        "lop": lop,
                        "khung_bao": kb,
                        "ly_do": ly_do,
                        "so_nguoi": so_nguoi,
                        "id_doi_tuong": id(dt)
                    })

        # 2. Kiểm tra xem người có mặc áo phản quang không
        if self.kiem_tra_ao and ds_nguoi:
            ds_ao_da_ghep = set()
            for nguoi in ds_nguoi:
                co_ao = False
                kb_nguoi = nguoi["khung_bao"]
                for i, ao in enumerate(ds_ao):
                    if i in ds_ao_da_ghep:
                        continue
                    if _co_trung_nhau(kb_nguoi, ao["khung_bao"]):
                        co_ao = True
                        ds_ao_da_ghep.add(i)
                        break
                if not co_ao:
                    so = nguoi.get("track_id", "?")
                    cac_vi_pham.append({
                        "lop": "Person",
                        "khung_bao": kb_nguoi,
                        "ly_do": f"ID:{so} - {self.ly_do_ao}",
                        "so_nguoi": so,
                        "id_doi_tuong": id(nguoi)
                    })

        return cac_vi_pham

    def annotate_frame(self, khung, cac_doi_tuong, cac_vi_pham):
        # Tập hợp các ID đối tượng được phát hiện bị vi phạm
        set_id_vi_pham = {v.get("id_doi_tuong") for v in cac_vi_pham if v.get("id_doi_tuong") is not None}

        # Nhóm đối tượng theo lớp để tránh duyệt toàn bộ danh sách O(N^2)
        doi_tuong_theo_lop = {}
        for d in cac_doi_tuong:
            lop = d["lop"]
            if lop not in doi_tuong_theo_lop:
                doi_tuong_theo_lop[lop] = []
            doi_tuong_theo_lop[lop].append(d)

        # Xác định các bộ phận cơ thể đã được bảo vệ (để tránh vẽ đè cảnh báo vi phạm)
        set_bo_phan_duoc_bao_ve = set()
        for lop, set_trang_bi_can_co in self.bang_trang_bi.items():
            if lop in doi_tuong_theo_lop:
                ds_trang_bi = []
                for tb_lop in set_trang_bi_can_co:
                    if tb_lop in doi_tuong_theo_lop:
                        ds_trang_bi.extend(doi_tuong_theo_lop[tb_lop])
                for dt in doi_tuong_theo_lop[lop]:
                    for tb in ds_trang_bi:
                        if _co_trung_nhau(dt["khung_bao"], tb["khung_bao"]):
                            set_bo_phan_duoc_bao_ve.add(id(dt))
                            break

        for dt in cac_doi_tuong:
            lop = dt["lop"]
            x1, y1, x2, y2 = dt["khung_bao"]
            do_tin = dt["do_tin_cay"]
            dt_id = id(dt)

            if lop == "Person":
                tid = dt.get("track_id", "?")
                if self.kiem_tra_ao and dt_id in set_id_vi_pham:
                    nhan = f"ID:{tid} NO VEST/SUIT {do_tin:.0%}"
                    mau_bgr = _MAU_VIEN_DO
                else:
                    mau_bgr = MAU_LOP.get(lop, _MAU_TRUNG_TINH)
                    nhan = f"ID:{tid} {do_tin:.0%}"
            elif lop in _SET_BO_PHAN:
                # Chỉ vẽ nếu cấu hình cảnh báo cho bộ phận này được bật
                if lop in self.lop_vi_pham_bat:
                    # Nếu bộ phận này đã có trang bị bảo hộ che phủ -> bỏ qua không vẽ cảnh báo lỗi
                    if dt_id in set_bo_phan_duoc_bao_ve:
                        continue
                    mau_bgr = _MAU_VIEN_DO
                    nhan = f"{_LY_DO_MAP[lop]} {do_tin:.0%}"
                else:
                    continue
            elif lop in _NHAN_TRANG_BI:
                mau_bgr = MAU_LOP.get(lop, _MAU_TRUNG_TINH)
                nhan = f"{_NHAN_TRANG_BI[lop]} {do_tin:.0%}"
            elif lop in _SET_AO_HIEN_THI:
                mau_bgr = MAU_LOP.get(lop, _MAU_TRUNG_TINH)
                nhan = f"VEST {do_tin:.0%}"
            else:
                mau_bgr = _MAU_TRUNG_TINH
                nhan = f"{lop.upper()} {do_tin:.0%}"

            cv2.rectangle(khung, (x1, y1), (x2, y2), mau_bgr, 1)
            _ve_nhan(khung, nhan, x1 + 2, y1, mau_bgr)

        if cac_vi_pham:
            h, w = khung.shape[:2]
            cv2.rectangle(khung, (0, 0), (w - 1, h - 1), _MAU_VIEN_DO, 3)
            
        return khung
