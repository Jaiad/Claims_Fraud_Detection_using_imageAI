
# app/streamlit_app.py
import sys
import math
from pathlib import Path

# Make sure src is importable
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
from src.pipeline.chain import load_chain
from src.utils.report import generate_pdf_report


# ------------------------- Theme & Styles -------------------------
st.set_page_config(page_title="UC304 Image AI", layout="wide")

css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("UC304 — Claims Fraud Detection Using Image AI")
st.caption("White UI · Dataset Browser · Visual outputs")


# ------------------------- Helpers -------------------------
def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def pick_dataset_dir() -> Path:
    """
    Prefer images in 'data/damage_db/images/image/', else fallback to 'data/damage_db/images/'.
    """
    preferred = Path("data/damage_db/images/image")
    fallback = Path("data/damage_db/images")
    if preferred.exists() and any(preferred.glob("*")):
        return preferred
    return fallback

def list_images(ds_dir: Path):
    exts = (".jpg", ".jpeg", ".png")
    return sorted([p for p in ds_dir.glob("*") if p.suffix.lower() in exts])

def set_selected(path: Path | None):
    if path is None:
        st.session_state.pop("selected_path", None)
    else:
        st.session_state["selected_path"] = str(path)

def get_selected() -> Path | None:
    p = st.session_state.get("selected_path")
    return Path(p) if p else None


# ------------------------- Layout -------------------------
left, right = st.columns([1, 1], gap="large")

# ------------------------- LEFT: Upload & Dataset Browser -------------------------
with left:
    st.subheader("1) Choose a claim image")

    # Upload widget
    uploaded = st.file_uploader(
        "Upload claim image (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
        help="Drag & drop or browse a file. Max ~200MB."
    )

    if uploaded:
        input_dir = Path("data/input")
        ensure_dir(input_dir)
        target = input_dir / uploaded.name
        with open(target, "wb") as f:
            f.write(uploaded.getbuffer())
        set_selected(target)
        st.success(f"Uploaded: {uploaded.name}")
        st.image(str(target), caption="Uploaded image", use_column_width=True)

    st.divider()
    st.markdown("**Or pick from dataset**")

    ds_dir = pick_dataset_dir()
    all_imgs = list_images(ds_dir)
    st.caption(f"Dataset path: `{ds_dir}` · Images found: **{len(all_imgs)}**")

    if not all_imgs:
        st.warning(
            "No images found. Add files under `data/damage_db/images/image/` "
            "or `data/damage_db/images/`."
        )
    else:
        # pagination
        PAGE_SIZE = 8
        total_pages = max(1, math.ceil(len(all_imgs) / PAGE_SIZE))
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        subset = all_imgs[start:end]

        grid_cols = st.columns(4)
        for i, p in enumerate(subset):
            with grid_cols[i % 4]:
                st.image(str(p), caption=p.name, use_column_width=True)
                st.button(
                    "Select",
                    key=f"select_{start+i}",
                    help=f"Select {p.name} for analysis",
                    on_click=set_selected,
                    args=(p,)
                )

    selected_path = get_selected()
    if selected_path and selected_path.exists():
        st.success(f"Selected: {selected_path.name}")
        st.image(str(selected_path), caption="Selected image", use_column_width=True)
        st.button("Clear selection", on_click=set_selected, args=(None,), type="secondary")
    else:
        st.info("Upload or select an image to proceed.")


# ------------------------- RIGHT: Analyze & Results -------------------------
with right:
    st.subheader("2) Run analysis")

    # Make the button disabled if nothing is selected
    analyze_disabled = get_selected() is None
    run = st.button("Analyze Image", type="primary", disabled=analyze_disabled)

    if run:
        selected_path = get_selected()
        if not selected_path:
            st.error("Please upload or select an image first.")
        else:
            with st.spinner("Running analysis..."):
                chain = load_chain()
                results = chain.invoke({"image_path": str(selected_path)})

            # ------------------------- Score card -------------------------
            st.markdown("### Fraud Likelihood")
            score = float(results.get("final_score", 0.0))
            color_class = "score-ok" if score < 0.35 else ("score-warn" if score < 0.65 else "score-bad")
            st.markdown(
                f"<div class='card'><h2 class='{color_class}'>Score: {score:.2f}</h2>"
                f"<span class='badge'>0 (low) → 1 (high)</span></div>",
                unsafe_allow_html=True
            )

            # ------------------------- Explanation -------------------------
            st.markdown("### Explanation")
            st.code(results.get("explanation", ""), language="text")

            # ------------------------- Visual Overlays -------------------------
            st.markdown("### Visual Overlays")
            tabs = st.tabs(["ELA", "Noise", "Edges"])
            overlays = [("ELA", "ela_overlay"), ("Noise", "noise_overlay"), ("Edges", "edges_overlay")]

            for tab, (label, key) in zip(tabs, overlays):
                with tab:
                    overlay = results.get(key)
                    if overlay is None:
                        st.info("No overlay available.")
                    else:
                        try:
                            st.image(overlay, caption=f"{label} overlay", use_column_width=True)
                        except Exception:
                            if isinstance(overlay, dict) and overlay.get("path"):
                                st.image(overlay["path"], caption=f"{label} overlay", use_column_width=True)
                            else:
                                st.info("Overlay could not be displayed.")

            # ------------------------- Similar cases -------------------------
            st.markdown("### Similar Damage Images (pHash)")
            sims = results.get("similar", [])
            if sims:
                sim_cols = st.columns(min(len(sims), 4))
                for i, s in enumerate(sims):
                    with sim_cols[i % 4]:
                        tpath = s.get("path")
                        label = s.get("label", "n/a")
                        dist = s.get("distance", "n/a")
                        caption = f"{Path(tpath).name}\nlabel={label}, dist={dist}"
                        if tpath and Path(tpath).exists():
                            st.image(str(tpath), caption=caption, use_column_width=True)
                        else:
                            st.write(f"{caption} (file missing)")
            else:
                st.info("No similar entries found—try rebuilding the index or adding more dataset images.")

            # ------------------------- Report export -------------------------
            st.divider()
            st.subheader("3) Export Report")
            pdf_name = f"report_{selected_path.stem}.pdf"
            pdf_path = Path("data") / pdf_name

            if st.button("Generate PDF Report", type="secondary"):
                try:
                    generate_pdf_report(str(pdf_path), str(selected_path), results)
                    st.success(f"Saved: {pdf_path}")
                    with open(pdf_path, "rb") as fh:
                        st.download_button("Download Report", data=fh.read(), file_name=pdf_name)
                except Exception as e:
                    st.error(f"Failed to generate report: {e}")


# ------------------------- Sidebar -------------------------
st.sidebar.header("Dataset & Index")
active_ds = pick_dataset_dir()
img_count = len(list_images(active_ds))
st.sidebar.success(f"Dataset path: `{active_ds}`")
st.sidebar.write(f"Images found: **{img_count}**")

if st.sidebar.button("Rebuild Hash Index"):
    try:
        from src.retrieval.build_index import build_index
        try:
            build_index(image_dir=str(active_ds))  # If signature supports image_dir
        except TypeError:
            build_index()  # Fallback to default
        st.sidebar.success("Index rebuilt.")
    except Exception as e:
        st.sidebar.error(f"Index rebuild failed: {e}")

st.sidebar.caption("Add images via: `scripts/fetch_hf_dataset.py` or `scripts/ingest_zip.py`")

# # app/streamlit_app.py
# import sys
# import math
# from pathlib import Path

# # Make sure src is importable
# sys.path.append(str(Path(__file__).resolve().parents[1]))

# import streamlit as st
# from src.pipeline.chain import load_chain
# from src.utils.report import generate_pdf_report


# # ------------------------- Theme & Styles -------------------------
# st.set_page_config(page_title="UC304 Image AI", layout="wide")

# css_path = Path(__file__).parent / "styles.css"
# if css_path.exists():
#     with open(css_path, "r", encoding="utf-8") as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# st.title("UC304 — Claims Fraud Detection Using Image AI")
# st.caption("White UI · Dataset Browser · Visual outputs")


# # ------------------------- Helpers -------------------------
# def ensure_dir(p: Path):
#     p.mkdir(parents=True, exist_ok=True)

# def pick_dataset_dir() -> Path:
#     """
#     Prefer images in 'data/damage_db/images/image/', else fallback to 'data/damage_db/images/'.
#     """
#     preferred = Path("data/damage_db/images/image")
#     fallback = Path("data/damage_db/images")
#     if preferred.exists() and any(preferred.glob("*")):
#         return preferred
#     return fallback

# def list_images(ds_dir: Path):
#     exts = (".jpg", ".jpeg", ".png")
#     return sorted([p for p in ds_dir.glob("*") if p.suffix.lower() in exts])

# def set_selected(path: Path | None):
#     if path is None:
#         st.session_state.pop("selected_path", None)
#     else:
#         st.session_state["selected_path"] = str(path)

# def get_selected() -> Path | None:
#     p = st.session_state.get("selected_path")
#     return Path(p) if p else None


# # ------------------------- Layout -------------------------
# left, right = st.columns([1, 1], gap="large")

# # ------------------------- LEFT: Upload & Dataset Browser -------------------------
# with left:
#     st.subheader("1) Choose a claim image")

#     # Upload widget
#     uploaded = st.file_uploader(
#         "Upload claim image (JPG/PNG)",
#         type=["jpg", "jpeg", "png"],
#         accept_multiple_files=False,
#         help="Drag & drop or browse a file. Max ~200MB."
#     )

#     if uploaded:
#         input_dir = Path("data/input")
#         ensure_dir(input_dir)
#         target = input_dir / uploaded.name
#         with open(target, "wb") as f:
#             f.write(uploaded.getbuffer())
#         set_selected(target)
#         st.success(f"Uploaded: {uploaded.name}")
#         st.image(str(target), caption="Uploaded image", use_column_width=True)

#     st.divider()
#     st.markdown("**Or pick from dataset**")

#     ds_dir = pick_dataset_dir()
#     all_imgs = list_images(ds_dir)
#     st.caption(f"Dataset path: `{ds_dir}` · Images found: **{len(all_imgs)}**")

#     if not all_imgs:
#         st.warning(
#             "No images found. Add files under `data/damage_db/images/image/` "
#             "or `data/damage_db/images/`."
#         )
#     else:
#         # pagination
#         PAGE_SIZE = 8
#         total_pages = max(1, math.ceil(len(all_imgs) / PAGE_SIZE))
#         page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

#         start = (page - 1) * PAGE_SIZE
#         end = start + PAGE_SIZE
#         subset = all_imgs[start:end]

#         grid_cols = st.columns(4)
#         for i, p in enumerate(subset):
#             with grid_cols[i % 4]:
#                 st.image(str(p), caption=p.name, use_column_width=True)
#                 st.button(
#                     "Select",
#                     key=f"select_{start+i}",
#                     help=f"Select {p.name} for analysis",
#                     on_click=set_selected,
#                     args=(p,)
#                 )

#     selected_path = get_selected()
#     if selected_path and selected_path.exists():
#         st.success(f"Selected: {selected_path.name}")
#         st.image(str(selected_path), caption="Selected image", use_column_width=True)
#         st.button("Clear selection", on_click=set_selected, args=(None,), type="secondary")
#     else:
#         st.info("Upload or select an image to proceed.")


# # ------------------------- RIGHT: Analyze & Results -------------------------
# with right:
#     st.subheader("2) Run analysis")

#     # Make the button disabled if nothing is selected
#     analyze_disabled = get_selected() is None
#     run = st.button("Analyze Image", type="primary", disabled=analyze_disabled)

#     if run:
#         selected_path = get_selected()
#         if not selected_path:
#             st.error("Please upload or select an image first.")
#         else:
#             with st.spinner("Running analysis..."):
#                 chain = load_chain()
#                 results = chain.invoke({"image_path": str(selected_path)})

#             # ------------------------- Score card -------------------------
#             st.markdown("### Fraud Likelihood")
#             score = float(results.get("final_score", 0.0))
#             color_class = "score-ok" if score < 0.35 else ("score-warn" if score < 0.65 else "score-bad")
#             st.markdown(
#                 f"<div class='card'><h2 class='{color_class}'>Score: {score:.2f}</h2>"
#                 f"<span class='badge'>0 (low) → 1 (high)</span></div>",
#                 unsafe_allow_html=True
#             )

#             # ------------------------- Explanation -------------------------
#             st.markdown("### Explanation")
#             st.code(results.get("explanation", ""), language="text")

#             # ------------------------- Visual Overlays -------------------------
#             st.markdown("### Visual Overlays")
#             tabs = st.tabs(["ELA", "Noise", "Edges"])
#             overlays = [("ELA", "ela_overlay"), ("Noise", "noise_overlay"), ("Edges", "edges_overlay")]

#             for tab, (label, key) in zip(tabs, overlays):
#                 with tab:
#                     overlay = results.get(key)
#                     if overlay is None:
#                         st.info("No overlay available.")
#                     else:
#                         try:
#                             st.image(overlay, caption=f"{label} overlay", use_column_width=True)
#                         except Exception:
#                             if isinstance(overlay, dict) and overlay.get("path"):
#                                 st.image(overlay["path"], caption=f"{label} overlay", use_column_width=True)
#                             else:
#                                 st.info("Overlay could not be displayed.")

#             # ------------------------- Similar cases -------------------------
#             st.markdown("### Similar Damage Images (pHash)")
#             sims = results.get("similar", [])
#             if sims:
#                 sim_cols = st.columns(min(len(sims), 4))
#                 for i, s in enumerate(sims):
#                     with sim_cols[i % 4]:
#                         tpath = s.get("path")
#                         label = s.get("label", "n/a")
#                         dist = s.get("distance", "n/a")
#                         caption = f"{Path(tpath).name}\nlabel={label}, dist={dist}"
#                         if tpath and Path(tpath).exists():
#                             st.image(str(tpath), caption=caption, use_column_width=True)
#                         else:
#                             st.write(f"{caption} (file missing)")
#             else:
#                 st.info("No similar entries found—try rebuilding the index or adding more dataset images.")

#             # ------------------------- Report export -------------------------
#             st.divider()
#             st.subheader("3) Export Report")
#             pdf_name = f"report_{selected_path.stem}.pdf"
#             pdf_path = Path("data") / pdf_name

#             if st.button("Generate PDF Report", type="secondary"):
#                 try:
#                     generate_pdf_report(str(pdf_path), str(selected_path), results)
#                     st.success(f"Saved: {pdf_path}")
#                     with open(pdf_path, "rb") as fh:
#                         st.download_button("Download Report", data=fh.read(), file_name=pdf_name)
#                 except Exception as e:
#                     st.error(f"Failed to generate report: {e}")


# # ------------------------- Sidebar -------------------------
# st.sidebar.header("Dataset & Index")
# active_ds = pick_dataset_dir()
# img_count = len(list_images(active_ds))
# st.sidebar.success(f"Dataset path: `{active_ds}`")
# st.sidebar.write(f"Images found: **{img_count}**")

# if st.sidebar.button("Rebuild Hash Index"):
#     try:
#         from src.retrieval.build_index import build_index
#         try:
#             build_index(image_dir=str(active_ds))  # If signature supports image_dir
#         except TypeError:
#             build_index()  # Fallback to default
#         st.sidebar.success("Index rebuilt.")
#     except Exception as e:
#         st.sidebar.error(f"Index rebuild failed: {e}")

# st.sidebar.caption("Add images via: `scripts/fetch_hf_dataset.py` or `scripts/ingest_zip.py`")
