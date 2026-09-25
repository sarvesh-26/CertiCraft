from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from app.core.config import settings

def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def generate_certificate(template_path: str, output_path: str, participant: dict):
    # Sample template is a PNG background. The backend overlays participant data and emits PDF.
    with Image.open(template_path).convert("RGB") as base:
        draw = ImageDraw.Draw(base)
        w, h = base.size
        name_font = _font(max(32, w // 22), True)
        detail_font = _font(max(18, w // 55), False)
        name = participant["name"]
        bbox = draw.textbbox((0, 0), name, font=name_font)
        draw.text(((w-(bbox[2]-bbox[0]))/2, h*0.46), name, fill=(25,25,35), font=name_font)
        pid = f'Certificate ID: {participant["participant_id"]}'
        bbox = draw.textbbox((0,0), pid, font=detail_font)
        draw.text(((w-(bbox[2]-bbox[0]))/2, h*0.60), pid, fill=(70,70,80), font=detail_font)
        base.save(output_path.replace(".pdf", ".png"), "PNG")
    c = canvas.Canvas(output_path, pagesize=A4)
    c.drawImage(ImageReader(output_path.replace(".pdf", ".png")), 0, 0, width=A4[0], height=A4[1])
    c.showPage(); c.save()
    Path(output_path.replace(".pdf", ".png")).unlink(missing_ok=True)
