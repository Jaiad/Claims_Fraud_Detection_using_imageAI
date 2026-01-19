
import numpy as np
from PIL import Image


def block_noise_score(image: Image.Image, block_size: int = 16):
    arr = np.asarray(image.convert('L'), dtype=np.float32)
    h, w = arr.shape
    blocks = []
    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            patch = arr[y:min(y+block_size,h), x:min(x+block_size,w)]
            blocks.append(float(np.var(patch)))
    blocks = np.array(blocks)
    if blocks.size == 0:
        return {"score": 0.0, "overlay": Image.fromarray(arr.astype('uint8')).convert('RGB')}
    norm = (blocks - blocks.min()) / (blocks.max() - blocks.min() + 1e-8)
    score = float(np.mean(np.sort(norm)[-max(1, len(norm)//4):]))

    overlay = np.zeros_like(arr)
    i = 0
    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            val = int(255 * norm[i])
            overlay[y:min(y+block_size,h), x:min(x+block_size,w)] = val
            i += 1
    return {"score": score, "overlay": Image.fromarray(overlay.astype('uint8')).convert('RGB')}
