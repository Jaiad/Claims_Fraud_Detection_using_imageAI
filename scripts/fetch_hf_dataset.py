
import argparse
from pathlib import Path
from io import BytesIO
from PIL import Image
from datasets import load_dataset

def save_pil(img, out_dir: Path, idx: int):
    out_dir.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_dir / f"hf_{idx:06d}.jpg", quality=95)

def main():
    ap = argparse.ArgumentParser(description="Fetch images from a Hugging Face dataset.")
    ap.add_argument("--repo", required=True, help="e.g., DrBimmer/comprehensive-car-damage")
    ap.add_argument("--split", default="train", help="split name")
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--out", default="data/damage_db/images")
    args = ap.parse_args()

    out_dir = Path(args.out)
    ds = load_dataset(args.repo, split=args.split)
    n = min(len(ds), args.limit)
    print(f"Downloading {n} images from {args.repo}:{args.split} ...")
    for i in range(n):
        row = ds[i]
        img = row.get("image")
        if img is None:
            for key in ("img", "Image", "image_bytes"):
                if key in row:
                    img = row[key]
                    break
        if img is None:
            continue
        if hasattr(img, "convert"):
            save_pil(img, out_dir, i)
        else:
            pil = Image.open(BytesIO(img)).convert("RGB")
            save_pil(pil, out_dir, i)
    print(f"Saved {n} images to {out_dir.resolve()}")

if __name__ == "__main__":
    main()
