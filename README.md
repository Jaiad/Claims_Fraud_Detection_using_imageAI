
# UC304 — Claims Fraud Detection Using Image AI (White UI Edition)

This package provides a **clean white UI** with a **dataset browser** so you can select real-world car photos from your local datasets and run the analysis. Outputs are presented as **cards, charts and images**—no JSON dumps.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# (Optional) Fetch real-world damage photos into data/damage_db/images/
python scripts/fetch_hf_dataset.py --repo DrBimmer/comprehensive-car-damage --split train --limit 1000 --out data/damage_db/images

# Build similarity index
python -m src.retrieval.build_index

# Run the UI
streamlit run app/streamlit_app.py
```

## UI Highlights
- White theme, clean layout
- **Dataset Browser**: thumbnail grid with pagination; click to select image
- Drag & drop upload (jpg/png)
- Results: fraud score card, explanations, overlays as tabs, similar damage cards
- PDF report export

## Notes
- The ZIP includes a few **synthetic sample images** in `data/input/`.
- Use the provided scripts in `scripts/` to ingest **real-world datasets**.

