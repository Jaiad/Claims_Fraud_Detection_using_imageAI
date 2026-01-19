
import argparse, random, shutil
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="Pick N random images for UI testing in data/input/")
    ap.add_argument("--src", default="data/damage_db/images")
    ap.add_argument("--out", default="data/input")
    ap.add_argument("--n", type=int, default=12)
    args = ap.parse_args()

    src = Path(args.src); out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    images = [p for p in src.glob("*") if p.suffix.lower() in (".jpg",".jpeg",".png")]
    random.shuffle(images); pick = images[:args.n]
    for p in pick:
        shutil.copy2(p, out / p.name)
    print(f"Copied {len(pick)} samples to {out.resolve()}")

if __name__ == "__main__":
    main()
