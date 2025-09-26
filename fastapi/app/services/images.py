import os, io, time, hashlib
from PIL import Image
from typing import Tuple
from app.config import settings

SIZES = [(128,128), (256,256), (512,512)]

def _safe_name(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".")).strip()

def process_and_save(image_file, filename: str) -> dict:
    os.makedirs(settings.media_root, exist_ok=True)
    base = os.path.splitext(_safe_name(filename))[0]
    data = {}
    with Image.open(image_file) as im:
        for w,h in SIZES:
            im_copy = im.copy()
            im_copy.thumbnail((w,h))
            hashed = hashlib.sha256(f"{time.time()}-{filename}-{w}x{h}".encode()).hexdigest()[:16]
            out_name = f"{base}-{w}x{h}-{hashed}.jpg"
            out_path = os.path.join(settings.media_root, out_name)
            im_copy.save(out_path, format="JPEG", quality=85, optimize=True)
            data[f"{w}x{h}"] = out_name
    return data
