import cv2
from datetime import datetime
from config import THU_MUC_ANH_VI_PHAM

_JPEG_PARAMS = [cv2.IMWRITE_JPEG_QUALITY, 85]

def luu_anh_vi_pham(khung):
    thoi_gian = datetime.now()
    ten_file = THU_MUC_ANH_VI_PHAM / f"vi_pham_{thoi_gian.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
    cv2.imwrite(str(ten_file), khung, _JPEG_PARAMS)
    return ten_file

