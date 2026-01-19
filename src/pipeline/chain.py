
# src/pipeline/chain.py

from typing import Dict, Any
from pathlib import Path
import yaml

from langchain_core.runnables import RunnableLambda, RunnableParallel

# Import tool factories
from .tools import ela_tool, noise_tool, edges_tool, exif_tool, retrieval_tool

# ----------------------------- Config -----------------------------
# Load config safely (works whether you run from project root or elsewhere)
CONFIG_PATH = Path("config/config.yaml")
if not CONFIG_PATH.exists():
    # Fallback: try relative to this file
    CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "config.yaml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

# ----------------------------- Aggregation -----------------------------
def aggregate_scores(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine tool outputs into a single scored result and build a human‑readable explanation.
    Expect keys: 'ela', 'noise', 'edges', 'exif' — each a dict containing 'score' and optional 'overlay'.
    """
    ela = inputs["ela"]
    noise = inputs["noise"]
    edges = inputs["edges"]
    exif = inputs["exif"]

    w = CONFIG["scoring"]["weights"]

    final = (
        w["ela"] * float(ela.get("score", 0))
        + w["noise"] * float(noise.get("score", 0))
        + w["edges"] * float(edges.get("score", 0))
        + w["exif"] * float(exif.get("score", 0))
    )

    # Build explanation lines
    explanation_lines = [
        f"ELA score={float(ela.get('score', 0)):.2f} (manipulation hotspots)",
        f"Noise score={float(noise.get('score', 0)):.2f} (block variance)",
        f"Edges score={float(edges.get('score', 0)):.2f} (edge magnitude std)",
    ]
    if exif.get("software"):
        flags = ",".join(exif.get("flags", [])) or "none"
        explanation_lines.append(f"EXIF software={exif['software']} — flags={flags}")
    else:
        explanation_lines.append(f"EXIF present={bool(exif.get('has_exif', False))}")

    # IMPORTANT: join with "\n" in ONE string (avoids unterminated literal)
    explanation_text = "\n".join(explanation_lines)

    return {
        "final_score": float(final),
        "explanation": explanation_text,
        "ela":   {"score": ela.get("score", 0),   "overlay": ela.get("overlay")},
        "noise": {"score": noise.get("score", 0), "overlay": noise.get("overlay")},
        "edges": {"score": edges.get("score", 0), "overlay": edges.get("overlay")},
        "exif":  {
            "score": exif.get("score", 0),
            "software": exif.get("software"),
            "flags": exif.get("flags", []),
            "has_exif": exif.get("has_exif", False),
        },
    }

def attach_overlays(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten overlay paths into top‑level keys expected by the UI tabs.
    """
    out = dict(inputs)
    out["ela_overlay"] = inputs.get("ela", {}).get("overlay")
    out["noise_overlay"] = inputs.get("noise", {}).get("overlay")
    out["edges_overlay"] = inputs.get("edges", {}).get("overlay")
    return out

def add_similarity(inputs: Dict[str, Any], sim: Any) -> Dict[str, Any]:
    """
    Attach list of similar items from retrieval tool.
    """
    out = dict(inputs)
    out["similar"] = sim
    return out

# ----------------------------- Chain loader -----------------------------
def load_chain() -> RunnableLambda:
    """
    Build the runnable graph:
      1) Run ELA, Noise, Edges, EXIF in parallel
      2) Aggregate scores + explanation
      3) Attach overlays
      4) Run similarity retrieval and attach results
    """
    # Each tool returns a callable client; we call .run(image_path) inside the lambda
    ela   = RunnableLambda(lambda inputs: ela_tool().run(inputs["image_path"]))
    noise = RunnableLambda(lambda inputs: noise_tool().run(inputs["image_path"]))
    edges = RunnableLambda(lambda inputs: edges_tool().run(inputs["image_path"]))
    exif  = RunnableLambda(lambda inputs: exif_tool().run(inputs["image_path"]))
    sim   = RunnableLambda(lambda inputs: retrieval_tool().run(inputs["image_path"]))

    # Step 1: parallel execution for speed
    parallel = RunnableParallel(ela=ela, noise=noise, edges=edges, exif=exif)

    # Step 2 & 3: aggregate -> attach overlays
    chain = parallel | RunnableLambda(aggregate_scores) | RunnableLambda(attach_overlays)

    # Step 4: similarity retrieval and final merge
    def full_chain(inputs: Dict[str, Any]) -> Dict[str, Any]:
        intermediate = chain.invoke(inputs)
        similar = sim.invoke(inputs)
        return add_similarity(intermediate, similar)

    return RunnableLambda(full_chain)
