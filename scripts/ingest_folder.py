
import argparse, shutil
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="Copy images from a local folder into damage_db/images/")
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default="data/damage_db/images")
    ap.add_argument("--exts", default=".jpg,.jpeg,.png")
    args = ap.parse_args()

    src = Path(args.src); out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    exts = {e.strip().lower() for e in args.exts.split(",")}
    count = 0
    for p in src.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            tgt = out / p.name
            i = 0
            while tgt.exists():
                tgt = out / f"{p.stem}_{i}{p.suffix}"
                i += 1
            shutil.copy2(p, tgt)
            count += 1
    print(f"Copied {count} images to {out.resolve()}")

if __name__ == "__main__":
    main()
