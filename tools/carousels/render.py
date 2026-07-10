#!/usr/bin/env python3
"""Render carousel slides from a JSON definition to PNG images + a PDF.

Uses Chrome headless for HTML → PNG rendering. No external Python packages
required beyond Pillow (for the optional PDF combine step).

Usage:
    python3 tools/carousels/render.py slides/post-4.json
    python3 tools/carousels/render.py slides/post-4.json --output assets/carousels/post-4

The slide JSON format:
    {
      "slides": [
        {"type": "cover|content|cta", "title": "...", "body": "..."},
        ...
      ]
    }

Requires: Google Chrome installed at the standard macOS path (or set CHROME env var).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR / "template.html"

# Chrome path — override with CHROME env var if needed
CHROME = os.environ.get(
    "CHROME",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)

SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1080


def render_slide(html_content: str, output_path: str) -> None:
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
        f.write(html_content)
        tmp_html = f.name
    try:
        cmd = [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--window-size={SLIDE_WIDTH},{SLIDE_HEIGHT}",
            f"--screenshot={output_path}",
            f"file://{tmp_html}",
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if not Path(output_path).exists():
            print(f"  ⚠ Chrome did not produce {output_path}", file=sys.stderr)
            if result.stderr:
                print(f"    stderr: {result.stderr.decode()[:200]}", file=sys.stderr)
            sys.exit(1)
    finally:
        os.unlink(tmp_html)


def make_slide_html(template: str, slide: dict, index: int, total: int) -> str:
    slide_type = slide.get("type", "content")
    title = slide.get("title", "").replace("\n", "<br>")
    body = slide.get("body", "").replace("\n", "<br>")

    html = template
    html = html.replace("{{TYPE}}", f"slide-{slide_type}")
    html = html.replace("{{TITLE}}", title)
    html = html.replace("{{BODY}}", body)
    html = html.replace("{{SLIDE_NUM}}", str(index + 1))
    html = html.replace("{{TOTAL}}", str(total))
    return html


def combine_pdf(output_dir: Path, stem: str, total: int) -> None:
    try:
        from PIL import Image
    except ImportError:
        print("  (pillow not available — skipping PDF)")
        return

    images = []
    for i in range(total):
        img = Image.open(output_dir / f"slide-{i + 1:02d}.png")
        if img.mode == "RGBA":
            img = img.convert("RGB")
        images.append(img)

    pdf_path = output_dir / f"{stem}.pdf"
    images[0].save(pdf_path, save_all=True, append_images=images[1:])
    print(f"  📄 PDF → {pdf_path}")


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <slides.json> [--output <dir>]")
        sys.exit(1)

    slides_path = Path(sys.argv[1])
    if not slides_path.exists() and not slides_path.is_absolute():
        # Try relative to script dir as fallback
        slides_path = SCRIPT_DIR / sys.argv[1]

    data = json.loads(slides_path.read_text())
    slides = data["slides"]
    total = len(slides)

    # Output directory
    if "--output" in sys.argv:
        output_dir = Path(sys.argv[sys.argv.index("--output") + 1])
    else:
        output_dir = SCRIPT_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Verify Chrome exists
    if not Path(CHROME).exists():
        print(f"Chrome not found at {CHROME}", file=sys.stderr)
        print("Set CHROME env var to your Chrome/Chromium path.", file=sys.stderr)
        sys.exit(1)

    template = TEMPLATE_PATH.read_text()

    for i, slide in enumerate(slides):
        html = make_slide_html(template, slide, i, total)
        out = output_dir / f"slide-{i + 1:02d}.png"
        print(f"  [{i + 1}/{total}] {slide.get('type', 'content')}: {slide.get('title', '')[:40]}")
        render_slide(html, str(out.resolve()))

    print(f"\n✅ {total} slides → {output_dir}/")
    combine_pdf(output_dir, slides_path.stem, total)


if __name__ == "__main__":
    main()
