from pathlib import Path

THU_MUC_GOC = Path(__file__).parent
TEN_THU_MUC_MO_HINH = "exp-2.openvino"
THU_MUC_MO_HINH = THU_MUC_GOC / TEN_THU_MUC_MO_HINH

# Tự động tìm thư mục chứa model bên trong (best_int8_openvino_model hoặc best_openvino_model)
DUONG_DAN_MO_HINH = THU_MUC_MO_HINH / "best_int8_openvino_model"
if not DUONG_DAN_MO_HINH.exists():
    DUONG_DAN_MO_HINH = THU_MUC_MO_HINH / "best_openvino_model"


THU_MUC_ANH_VI_PHAM = Path(__file__).parent / "anh_vi_pham"
THU_MUC_ANH_VI_PHAM.mkdir(exist_ok=True)

THU_MUC_BAO_CAO = Path(__file__).parent / "bao_cao"
THU_MUC_BAO_CAO.mkdir(exist_ok=True)

import yaml

def doc_danh_sach_lop():
    duong_dan_meta = DUONG_DAN_MO_HINH / "metadata.yaml"
    if duong_dan_meta.exists():
        try:
            with open(duong_dan_meta, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if 'names' in data:
                    names_dict = data['names']
                    lop_map = {}
                    chuan_hoa = {
                        "gloves": "Gloves",
                        "hands": "Hands",
                        "head": "Head",
                        "helmet": "Helmet",
                        "person": "Person",
                        "vest": "Safety-vest",
                        "safety-vest": "Safety-vest",
                        "hand": "Hands"
                    }
                    for k, v in names_dict.items():
                        ten_goc = str(v).lower().strip()
                        ten_chuan = chuan_hoa.get(ten_goc, str(v).capitalize())
                        lop_map[int(k)] = ten_chuan
                    return lop_map
        except Exception as e:
            print(f"[Warning] Lỗi khi đọc metadata.yaml: {e}")
    
    # Mặc định dự phòng (6 lớp)
    return {
        0: "Gloves", 1: "Hands", 2: "Head", 3: "Helmet", 4: "Person", 5: "Safety-vest"
    }


def doc_kich_thuoc_anh():
    duong_dan_meta = DUONG_DAN_MO_HINH / "metadata.yaml"
    if duong_dan_meta.exists():
        try:
            with open(duong_dan_meta, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if 'imgsz' in data:
                    img = data['imgsz']
                    if isinstance(img, list) and len(img) > 0:
                        return int(img[0])
                    elif isinstance(img, (int, float)):
                        return int(img)
        except Exception as e:
            print(f"[Warning] Lỗi khi đọc imgsz từ metadata.yaml: {e}")
    return 640

CAC_LOP = doc_danh_sach_lop()


TEN_HIEN_THI = {
    "Head":           "Đầu trần",
    "Helmet":         "Mũ bảo hộ",
    "Person":         "Người",
    "Safety-vest":    "Áo phản quang",
    "Gloves":         "Găng tay",
    "Hands":          "Bàn tay",
}

MAU_LOP = {
    "Head":           (0,   60,  255),
    "Hands":          (0,   60,  255),
    "Helmet":         (0,  200,   60),
    "Gloves":         (0,  200,   60),
    "Person":         (255, 165,   0),
    "Safety-vest":    (60,  220,  220),
}

CANH_BAO_DINH_NGHIA = {
    "no_helmet":  {"lop": "Head",  "ly_do": "NO HELMET",  "mo_ta": "Không đội mũ bảo hộ"},
    "no_gloves":  {"lop": "Hands", "ly_do": "NO GLOVES",  "mo_ta": "Không đeo găng tay"},
    "no_vest":    {"lop": "Person","ly_do": "NO VEST/SUIT","mo_ta": "Không mặc áo/đồ bảo hộ"},
}

CANH_BAO_PHU_THUOC = {
    "no_helmet":  {"Head", "Helmet"},
    "no_gloves":  {"Hands", "Gloves"},
    "no_vest":    {"Person", "Safety-vest"}
}


def khoi_tao_mac_dinh_canh_bao():
    set_lop_model = set(CAC_LOP.values())
    mac_dinh = set()
    if "Head" in set_lop_model or "Helmet" in set_lop_model:
        mac_dinh.add("no_helmet")
    if "Person" in set_lop_model or "Safety-vest" in set_lop_model or "Safety-suit" in set_lop_model or "Medical-suit" in set_lop_model:
        mac_dinh.add("no_vest")
    if not mac_dinh:
        for k, deps in CANH_BAO_PHU_THUOC.items():
            if deps.intersection(set_lop_model):
                mac_dinh.add(k)
                break
    return mac_dinh

MAC_DINH_CANH_BAO = khoi_tao_mac_dinh_canh_bao()

NGUONG_TIN_CAY = 0.40
NGUONG_IOU = 0.45
THOI_GIAN_NGHI = 3
KICH_THUOC_ANH = doc_kich_thuoc_anh()

GIAO_DIEN_SANG = """
QMainWindow, QWidget {
    background-color: #ffffff;
    color: #24292f;
    font-family: 'Segoe UI', sans-serif;
}
QGroupBox {
    border: 1px solid #d0d7de;
    border-radius: 8px;
    margin-top: 12px;
    padding: 8px;
    font-size: 12px;
    color: #57606a;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QPushButton {
    background-color: #f6f8fa;
    color: #24292f;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}
QPushButton:hover { background-color: #f3f4f6; border-color: #0969da; }
QPushButton:pressed { background-color: #0969da; color: #ffffff; }
QPushButton:disabled { color: #8c959f; }
QPushButton#btn_dung {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #cf222e,stop:1 #a40e26);
    border: none; color: white; font-weight: bold;
}
QPushButton#btn_dung:hover { background: #a40e26; }
QLabel#trang_thai_tot {
    background-color: #dafbe1; color: #1a7f37;
    border: 1px solid #4ac26b; border-radius: 6px;
    padding: 6px 14px; font-weight: bold; font-size: 14px;
}
QLabel#trang_thai_canh_bao {
    background-color: #ffebe9; color: #cf222e;
    border: 1px solid #ff8182; border-radius: 6px;
    padding: 6px 14px; font-weight: bold; font-size: 14px;
}
QLabel#trang_thai_cho {
    background-color: #f6f8fa; color: #57606a;
    border: 1px solid #d0d7de; border-radius: 6px;
    padding: 6px 14px; font-size: 14px;
}
QTabWidget::pane { border: 1px solid #d0d7de; border-radius: 6px; }
QTabBar::tab {
    background: #f6f8fa; color: #57606a;
    padding: 8px 18px; border: 1px solid #d0d7de;
    border-bottom: none; border-radius: 6px 6px 0 0;
}
QTabBar::tab:selected { background: #ffffff; color: #24292f; }
QTableWidget {
    background-color: #ffffff; color: #24292f;
    gridline-color: #d0d7de; border: none;
}
QTableWidget::item:selected { background-color: #0969da; color: #ffffff; }
QHeaderView::section {
    background-color: #f6f8fa; color: #57606a;
    border: none; padding: 6px; font-size: 12px;
}
QScrollBar:vertical {
    background: #ffffff; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical { background: #d0d7de; border-radius: 4px; }
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff; color: #24292f;
    border: 1px solid #d0d7de; border-radius: 4px; padding: 4px;
}
QLineEdit {
    background-color: #ffffff; color: #24292f;
    border: 1px solid #d0d7de; border-radius: 4px; padding: 6px;
    font-size: 12px;
}
QLineEdit:focus { border-color: #0969da; }
"""
