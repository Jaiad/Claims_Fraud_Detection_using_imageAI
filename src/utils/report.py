
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from pathlib import Path
import textwrap


def generate_pdf_report(pdf_path: str, original_image: str, results: dict):
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    c.setTitle("UC304 Claims Fraud Detection Report")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 40, "UC304 — Claims Fraud Detection Report")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.gray)
    c.drawString(40, height - 60, f"Original: {Path(original_image).name}")

    # Original image block
    try:
        img = ImageReader(original_image)
        c.drawImage(img, 40, height - 360, width=300, height=300, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    # Score
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    c.drawString(360, height - 80, f"Final Score: {results.get('final_score', 0):.2f}")

    # Explanation (wrapped)
    c.setFont("Helvetica", 10)
    explanation = str(results.get("explanation", ""))
    text_obj = c.beginText(360, height - 100)
    text_obj.setLeading(12)
    for line in explanation.splitlines():
        for wline in textwrap.wrap(line, width=60) or [""]:
            text_obj.textLine(wline)
    c.drawText(text_obj)

    # Component scores
    y = height - 180
    for key in ["ela", "noise", "edges", "exif"]:
        c.setFont("Helvetica", 10)
        c.drawString(360, y, f"{key.upper()} score: {results.get(key, {}).get('score', 0):.2f}")
        y -= 18

    # Similar images list
    y = height - 360
    c.setFont("Helvetica-Bold", 12)
    c.drawString(360, y, "Top similar damage entries:")
    y -= 18
    c.setFont("Helvetica", 10)
    for s in results.get("similar", []):
        line = f"{Path(s.get('path','')).name} — label={s.get('label','')} (dist={s.get('distance','')})"
        for wline in textwrap.wrap(line, width=60) or [""]:
            c.drawString(360, y, wline)
            y -= 14
            if y < 40:
                c.showPage(); y = height - 40; c.setFont("Helvetica", 10)

    c.showPage()
    c.save()
