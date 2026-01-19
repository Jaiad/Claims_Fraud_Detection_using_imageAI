
from pathlib import Path
import json
from .simple_hash import phash_image


def build_index():
    root = Path(__file__).resolve().parents[2]
    images_dir = root / 'data' / 'damage_db' / 'images'
    index_path = root / 'data' / 'index' / 'hash_index.json'
    entries = []
    for p in sorted(images_dir.glob('*.jpg')) + sorted(images_dir.glob('*.png')) + sorted(images_dir.glob('*.jpeg')):
        try:
            entries.append({
                'path': str(p),
                'label': p.stem.split('_')[0],
                'phash': str(phash_image(str(p)))
            })
        except Exception:
            pass
    index = {'entries': entries}
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
    print(f"Built index with {len(entries)} entries at {index_path}")

if __name__ == '__main__':
    build_index()
