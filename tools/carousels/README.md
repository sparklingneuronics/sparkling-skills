# tools/carousels/ — LinkedIn carousel slide generator

Renders carousel slides from a JSON definition to PNG images + a combined PDF,
using Chrome headless. Edit text → re-render → committed slides.

## Requirements

- **Google Chrome** (macOS default path; override with `CHROME` env var)
- **Python 3** (stdlib only; Pillow for the PDF step)

## Usage

```bash
# Render slides to PNGs + PDF
python3 tools/carousels/render.py slides/post-4.json

# Custom output directory
python3 tools/carousels/render.py slides/post-4.json --output assets/carousels/post-4
```

## Files

- `template.html` — the slide design (dark theme, 1080×1080, inline CSS)
- `render.py` — reads a slides JSON, renders each slide via Chrome headless
- `slides/*.json` — one file per carousel (slide content: type, title, body)

## Slide types

- `cover` — centered, large title (the hook slide)
- `content` — blue label + body text (the main slides)
- `cta` — centered, medium title + dimmer body (the closing slide)

## Adding a new carousel

1. Create `slides/post-N.json` with your slide content.
2. Run `python3 tools/carousels/render.py slides/post-N.json --output assets/carousels/post-N`.
3. Upload the PDF to LinkedIn (or the individual PNGs as a multi-image post).

## Design

- 1080×1080 (LinkedIn square carousel standard)
- Dark background (#0f1419), clean sans-serif (system font)
- Titles: white (#e6edf3); labels: blue (#58a6ff); body: light gray (#c9d1d9)
- Edit `template.html` to change colors, fonts, or layout.
