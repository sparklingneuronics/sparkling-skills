# tools/ — maintainer tooling

Dev/maintainer scripts for the `sparkling-skills` marketplace. Not part of any shipped plugin — these
run on the maintainer's machine (so they may use macOS/Homebrew tools, unlike the cross-platform skills).

## demos/
Record and regenerate the README demo GIF + LinkedIn MP4 from a **real** `dispatch` session — a VHS
tape + a planted-bug workspace + `render.py` (cut → speed → final-frame hold → optimize).
See **[demos/README.md](demos/README.md)**.

## carousels/
Render LinkedIn carousel slides from JSON → PNG + PDF using Chrome headless. Edit slide text →
re-render → committed slides. Same docs-as-code spirit as the demo pipeline.
See **[carousels/README.md](carousels/README.md)**.
