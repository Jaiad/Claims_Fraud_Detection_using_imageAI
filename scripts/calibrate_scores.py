
import csv, yaml
from pathlib import Path
import numpy as np
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report

from src.analysis.ela import compute_ela
from src.analysis.noise import block_noise_score
from src.analysis.edges import edge_inconsistency
from src.analysis.exif import inspect_exif

CFG_PATH = Path("config/config.yaml")
CFG = yaml.safe_load(open(CFG_PATH, "r"))


def features(image_path: str):
    img = Image.open(image_path).convert("RGB")
    ela = compute_ela(img, CFG["analysis"]["ela_quality"], CFG["analysis"]["ela_threshold"])['score']
    noise = block_noise_score(img, CFG["analysis"]["block_size"])['score']
    edges = edge_inconsistency(img, CFG["analysis"]["block_size"])['score']
    exif = inspect_exif(image_path, CFG["scoring"]["suspicious_software"])['score']
    return [ela, noise, edges, exif]


def main():
    labels_csv = Path("data/calibration/labels.csv")
    if not labels_csv.exists():
        print("Create data/calibration/labels.csv with columns: image_path,label")
        return
    rows = list(csv.DictReader(open(labels_csv, "r")))
    X, y = [], []
    for r in rows:
        X.append(features(r['image_path']))
        y.append(1 if r['label']=='manipulated' else 0)
    X = np.array(X); y = np.array(y)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    clf = LogisticRegression(max_iter=300, class_weight='balanced')
    clf.fit(Xtr, ytr)

    prob = clf.predict_proba(Xte)[:,1]
    print("AUC:", roc_auc_score(yte, prob))
    print(classification_report(yte, (prob>0.5).astype(int), digits=3))

    coefs = clf.coef_[0]
    coefs = (coefs - coefs.min()) / (coefs.max() - coefs.min() + 1e-8)
    new_w = {"ela":float(coefs[0]), "noise":float(coefs[1]), "edges":float(coefs[2]), "exif":float(coefs[3])}
    CFG['scoring']['weights'] = new_w
    yaml.safe_dump(CFG, open(CFG_PATH, "w"))
    print("Updated config weights:", new_w)

if __name__ == '__main__':
    main()
