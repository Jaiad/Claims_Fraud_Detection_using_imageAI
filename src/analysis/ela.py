
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
from io import BytesIO


def compute_ela(image: Image.Image, resave_quality: int = 95, threshold: int = 30):
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=resave_quality)
    buffer.seek(0)
    resaved = Image.open(buffer)

    diff = ImageChops.difference(image, resaved)
    enhancer = ImageEnhance.Brightness(diff)
    ela_img = enhancer.enhance(20)

    arr = np.asarray(ela_img.convert('L'))
    score = float((arr > threshold).mean())
    overlay = ela_img.convert('RGB')
    return {"score": score, "overlay": overlay}
