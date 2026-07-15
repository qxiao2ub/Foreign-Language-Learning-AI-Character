"""Generate the lightweight SVG assets used by the Streamlit interface."""

from __future__ import annotations

from pathlib import Path

from lingglot.visuals import CHARACTERS, character_svg, logo_icon_svg

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CHARACTER_DIR = ASSETS / "characters"


def horizontal_logo_svg() -> str:
    return """<svg width="260" height="64" viewBox="0 0 260 64" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Lingglot">
  <defs>
    <linearGradient id="brand-gradient" x1="4" y1="4" x2="62" y2="62" gradientUnits="userSpaceOnUse">
      <stop stop-color="#FF6A3D"/>
      <stop offset=".56" stop-color="#FF4F9A"/>
      <stop offset="1" stop-color="#FF4DC4"/>
    </linearGradient>
  </defs>
  <path d="M12 10h40a8 8 0 0 1 8 8v25a8 8 0 0 1-8 8H31L18 60v-9h-6a8 8 0 0 1-8-8V18a8 8 0 0 1 8-8Z" fill="url(#brand-gradient)"/>
  <circle cx="24" cy="30" r="3" fill="#FFF9ED"/>
  <circle cx="40" cy="30" r="3" fill="#FFF9ED"/>
  <path d="M24 39c4.5 4 11.5 4 16 0" stroke="#FFF9ED" stroke-width="3" stroke-linecap="round" fill="none"/>
  <text x="76" y="43" fill="#351C1C" font-family="Fraunces, Georgia, serif" font-size="34" font-weight="650" letter-spacing="-1">lingglot</text>
</svg>"""


def main() -> None:
    CHARACTER_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS / "logo-icon.svg").write_text(logo_icon_svg(64), encoding="utf-8")
    (ASSETS / "logo-horizontal.svg").write_text(
        horizontal_logo_svg(), encoding="utf-8"
    )
    for index, (name, _trait) in enumerate(CHARACTERS):
        svg = character_svg(
            index,
            size=320,
            id_prefix=f"asset-{name.lower()}",
            include_background=True,
        )
        (CHARACTER_DIR / f"{name.lower()}.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
