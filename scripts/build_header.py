"""Gera assets/header-dark.svg e assets/header-light.svg.

O banner é estático (não depende de API), então é gerado uma vez e commitado.
Rode de novo depois de mudar textos ou cores:

    python3 scripts/build_header.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

THEMES = {
    "dark": {
        "bg1": "#0d1117",
        "bg2": "#0b1a2e",
        "grid": "#1f2a3a",
        "title": "#e6edf3",
        "muted": "#8b949e",
        "accent1": "#38bdf8",
        "accent2": "#818cf8",
        "accent3": "#c084fc",
        "chip_bg": "#161b22",
        "chip_stroke": "#30363d",
    },
    "light": {
        "bg1": "#ffffff",
        "bg2": "#eef6ff",
        "grid": "#dbe6f3",
        "title": "#0d1117",
        "muted": "#57606a",
        "accent1": "#0284c7",
        "accent2": "#4f46e5",
        "accent3": "#9333ea",
        "chip_bg": "#f6f8fa",
        "chip_stroke": "#d0d7de",
    },
}

ROLES = [
    "Full Stack Developer",
    "TypeScript • Next.js • Supabase",
    "Dados, Automação e APIs",
    "Construindo com IA no fluxo",
]

CHIPS = ["Next.js", "TypeScript", "Supabase", "Python", "AWS"]

W, H = 1000, 280


def role_lines(t: dict) -> str:
    """Cada papel aparece em sequência, com fade e leve deslocamento."""
    n = len(ROLES)
    dur = n * 3
    out = []
    for i, role in enumerate(ROLES):
        out.append(
            f'<text class="role" x="80" y="176" style="animation-delay:{i * 3}s;'
            f'animation-duration:{dur}s">{role}</text>'
        )
    return "\n    ".join(out)


def chips(t: dict) -> str:
    out = []
    x = 80
    for i, label in enumerate(CHIPS):
        w = 22 + len(label) * 8.2
        out.append(
            f'<g class="chip" style="animation-delay:{0.9 + i * 0.12:.2f}s">'
            f'<rect x="{x:.0f}" y="206" width="{w:.0f}" height="30" rx="15" '
            f'fill="{t["chip_bg"]}" stroke="{t["chip_stroke"]}"/>'
            f'<text x="{x + w / 2:.0f}" y="226" text-anchor="middle" class="chip-t">{label}</text>'
            f"</g>"
        )
        x += w + 10
    return "\n    ".join(out)


def build(name: str, t: dict) -> str:
    n = len(ROLES)
    # Fração do ciclo em que cada papel fica visível.
    show = 100 / n
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Victor Franco — Full Stack Developer">
  <title>Victor Franco — Full Stack Developer</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t["bg1"]}"/>
      <stop offset="1" stop-color="{t["bg2"]}"/>
    </linearGradient>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t["accent1"]}"/>
      <stop offset="0.5" stop-color="{t["accent2"]}"/>
      <stop offset="1" stop-color="{t["accent3"]}"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-0.4 0;0.4 0;-0.4 0" dur="8s" repeatCount="indefinite"/>
    </linearGradient>
    <radialGradient id="orb1">
      <stop offset="0" stop-color="{t["accent1"]}" stop-opacity="0.45"/>
      <stop offset="1" stop-color="{t["accent1"]}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="orb2">
      <stop offset="0" stop-color="{t["accent3"]}" stop-opacity="0.35"/>
      <stop offset="1" stop-color="{t["accent3"]}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0V32" fill="none" stroke="{t["grid"]}" stroke-width="1"/>
    </pattern>
    <mask id="fade">
      <linearGradient id="fadeg" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0.35" stop-color="#fff" stop-opacity="0"/>
        <stop offset="1" stop-color="#fff" stop-opacity="1"/>
      </linearGradient>
      <rect width="{W}" height="{H}" fill="url(#fadeg)"/>
    </mask>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>
  <style>
    text {{ font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }}
    .hello {{ fill: {t["muted"]}; font-size: 18px; opacity: 0; animation: up .7s ease-out .1s forwards; }}
    .name {{ font-family: 'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif; font-size: 64px; font-weight: 800; letter-spacing: -1.5px; opacity: 0; animation: up .8s ease-out .3s forwards; }}
    .role {{ fill: {t["title"]}; font-size: 22px; font-weight: 600; opacity: 0; animation-name: cycle; animation-iteration-count: infinite; animation-timing-function: ease-in-out; }}
    .prompt {{ fill: {t["accent1"]}; font-size: 22px; font-weight: 700; }}
    .chip {{ opacity: 0; animation: up .6s ease-out forwards; }}
    .chip-t {{ fill: {t["muted"]}; font-size: 13px; }}
    .orbit {{ transform-origin: 800px 140px; animation: spin 24s linear infinite; }}
    .orbit2 {{ transform-origin: 800px 140px; animation: spin 36s linear infinite reverse; }}
    .float1 {{ animation: drift 9s ease-in-out infinite; }}
    .float2 {{ animation: drift 12s ease-in-out infinite reverse; }}
    @keyframes up {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes cycle {{
      0% {{ opacity: 0; transform: translateY(10px); }}
      {show * 0.12:.1f}% {{ opacity: 1; transform: translateY(0); }}
      {show * 0.85:.1f}% {{ opacity: 1; transform: translateY(0); }}
      {show:.1f}% {{ opacity: 0; transform: translateY(-10px); }}
      100% {{ opacity: 0; }}
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes drift {{ 0%,100% {{ transform: translate(0,0); }} 50% {{ transform: translate(-30px,18px); }} }}
    @media (prefers-reduced-motion: reduce) {{
      * {{ animation: none !important; }}
      .hello, .name, .chip {{ opacity: 1; }}
      .role:first-of-type {{ opacity: 1; }}
    }}
  </style>

  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#fade)"/>
    <circle class="float1" cx="820" cy="60" r="190" fill="url(#orb1)"/>
    <circle class="float2" cx="960" cy="260" r="170" fill="url(#orb2)"/>

    <!-- Órbitas decorativas -->
    <g class="orbit" fill="none" stroke="{t["accent1"]}" stroke-opacity="0.35">
      <ellipse cx="800" cy="140" rx="120" ry="120" stroke-dasharray="4 10"/>
      <circle cx="920" cy="140" r="6" fill="{t["accent1"]}" stroke="none"/>
    </g>
    <g class="orbit2" fill="none" stroke="{t["accent2"]}" stroke-opacity="0.3">
      <ellipse cx="800" cy="140" rx="78" ry="78"/>
      <circle cx="800" cy="62" r="5" fill="{t["accent2"]}" stroke="none"/>
    </g>
    <text x="800" y="152" text-anchor="middle" font-size="34" font-weight="700" fill="url(#name)">&lt;/&gt;</text>

    <text class="hello" x="80" y="70">// olá, mundo — eu sou</text>
    <text class="name" x="76" y="134" fill="url(#name)">Victor Franco</text>

    <text class="prompt" x="52" y="176">›</text>
    {role_lines(t)}

    {chips(t)}
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{t["chip_stroke"]}"/>
</svg>
"""


def main() -> None:
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    for name, theme in THEMES.items():
        (out / f"header-{name}.svg").write_text(build(name, theme), encoding="utf-8")
        print(f"assets/header-{name}.svg")


if __name__ == "__main__":
    main()
