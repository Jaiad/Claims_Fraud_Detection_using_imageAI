
from PIL import Image
import imagehash
import json

def phash_image(path: str) -> int:
    img = Image.open(path).convert('RGB')
    return int(str(imagehash.phash(img)), 16)

def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count('1')

def nearest(query_path: str, index_path: str, top_k: int = 4):
    q = phash_image(query_path)
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)
    entries = index.get('entries', [])
    scored = []
    for e in entries:
        dist = hamming(q, int(e['phash']))
        scored.append({"path": e['path'], "label": e['label'], "distance": dist})
    scored.sort(key=lambda x: x['distance'])
    return scored[:top_k]
