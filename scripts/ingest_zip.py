
import argparse, zipfile, shutil
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="Extract and ingest a ZIP of images into damage_db/images/")
    ap.add_argument("--zip", required=True)
    ap.add_argument("--out", default="data/damage_db/images")
    ap.add_argument("--exts", default=".jpg,.jpeg,.png")
    args = ap.parse_args()

    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    exts = {e.strip().lower() for e in args.exts.split(",")}
    tmp = out_dir.parent / "_tmp_extract"
    if tmp.exists(): shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(args.zip, "r") as z:
        z.extractall(tmp)

    count = 0
    for p in tmp.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            target = out_dir / p.name
            i = 0
            while target.exists():
                target = out_dir / f"{p.stem}_{i}{p.suffix}"
                i += 1
            shutil.copy2(p, target)
            count += 1
    shutil.rmtree(tmp)
    print(f"Ingested {count} images to {out_dir.resolve()}")

if __name__ == "__main__":
    main()
