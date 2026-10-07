from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "generated"
OUTPUT_DIR.mkdir(exist_ok=True)

def generate_certificate(recipient_name: str, course_name: str, issue_date: str, certificate_id: int) -> str:
    """Generate one PDF from the single predefined certificate template."""
    path = OUTPUT_DIR / f"certificate_{certificate_id}.pdf"
    c = canvas.Canvas(str(path), pagesize=landscape(A4))
    width, height = landscape(A4)

    c.setStrokeColor(colors.HexColor("#B08D57"))
    c.setLineWidth(5)
    c.rect(25, 25, width - 50, height - 50)
    c.setStrokeColor(colors.HexColor("#D6B56D"))
    c.setLineWidth(1.5)
    c.rect(38, 38, width - 76, height - 76)

    c.setFillColor(colors.HexColor("#1F2937"))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 105, "CERTIFICATE OF COMPLETION")

    c.setFont("Helvetica", 15)
    c.drawCentredString(width / 2, height - 145, "This certificate is proudly presented to")

    c.setFillColor(colors.HexColor("#8B6B2E"))
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width / 2, height - 205, recipient_name)

    c.setFillColor(colors.HexColor("#1F2937"))
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 250, "for successfully completing")
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 285, course_name)

    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2, 100, f"Issued on: {issue_date}")
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(width / 2, 75, "Bulk Certificate Generator")
    c.save()
    return str(path)
