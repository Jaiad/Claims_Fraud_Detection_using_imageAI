
import numpy as np
from PIL import Image, ImageFilter


def edge_inconsistency(image: Image.Image, block_size: int = 16):
    edges = image.convert('L').filter(ImageFilter.FIND_EDGES)
    arr = np.asarray(edges, dtype=np.float32)
    h, w = arr.shape
    mags = []
    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            patch = arr[y:min(y+block_size,h), x:min(x+block_size,w)]
            mags.append(float(np.mean(patch)))
    mags = np.array(mags)
    if mags.size == 0:
        return {"score": 0.0, "overlay": edges.convert('RGB')}
    norm = (mags - mags.min()) / (mags.max() - mags.min() + 1e-8)
    score = float(np.std(norm))

    overlay = np.zeros_like(arr)
    i = 0
    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            val = int(255 * norm[i])
            overlay[y:min(y+block_size,h), x:min(x+block_size,w)] = val
            i += 1
    return {"score": score, "overlay": Image.fromarray(overlay.astype('uint8')).convert('RGB')}
