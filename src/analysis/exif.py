
from PIL import Image

def inspect_exif(image_path: str, suspicious_software=None):
    suspicious_software = suspicious_software or []
    info = {"has_exif": False, "software": None, "flags": []}
    try:
        img = Image.open(image_path)
        exif = img.getexif()
        if exif and len(exif) > 0:
            info["has_exif"] = True
            sw = exif.get(305)
            if sw:
                info["software"] = str(sw)
                for s in suspicious_software:
                    if s.lower() in str(sw).lower():
                        info["flags"].append(f"Software mentions {s}")
    except Exception:
        pass
    score = 1.0 if info["flags"] else (0.1 if info["has_exif"] else 0.0)
    info["score"] = score
    return info
