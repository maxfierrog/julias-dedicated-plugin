"""SVG figures for the dev collection, styled like textbook screenshots
(dark ink on an opaque white background), as real decks' images usually are.
"""

import math

W, H = 360, 240
PAD_L, PAD_B, PAD_T, PAD_R = 50, 40, 20, 20


def _frame(body: str, xlabel: str, ylabel: str) -> str:
    x0, y0 = PAD_L, H - PAD_B
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif" font-size="12">
<rect width="{W}" height="{H}" fill="white"/>
<line x1="{x0}" y1="{y0}" x2="{W - PAD_R}" y2="{y0}" stroke="black"/>
<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{PAD_T}" stroke="black"/>
<text x="{(x0 + W - PAD_R) / 2}" y="{H - 10}" text-anchor="middle">{xlabel}</text>
<text x="14" y="{(PAD_T + y0) / 2}" text-anchor="middle" transform="rotate(-90 14 {(PAD_T + y0) / 2})">{ylabel}</text>
{body}
</svg>
"""


def _path(fn, xmax: float, ymax: float, n: int = 120) -> str:
    """Polyline of y=fn(x) over [0, xmax], scaled into the plot area."""
    pw, ph = W - PAD_L - PAD_R, H - PAD_T - PAD_B
    pts = []
    for i in range(n + 1):
        x = xmax * i / n
        px = PAD_L + pw * x / xmax
        py = H - PAD_B - ph * fn(x) / ymax
        pts.append(f"{px:.1f},{py:.1f}")
    return " ".join(pts)


def _sy(y: float, ymax: float) -> float:
    return H - PAD_B - (H - PAD_T - PAD_B) * y / ymax


def _sx(x: float, xmax: float) -> float:
    return PAD_L + (W - PAD_L - PAD_R) * x / xmax


def michaelis_menten() -> str:
    vmax, km, xmax, ymax = 1.0, 2.0, 20.0, 1.15
    curve = _path(lambda s: vmax * s / (km + s), xmax, ymax)
    body = f"""<polyline points="{curve}" fill="none" stroke="#1f4e9c" stroke-width="2"/>
<line x1="{PAD_L}" y1="{_sy(vmax, ymax):.1f}" x2="{W - PAD_R}" y2="{_sy(vmax, ymax):.1f}" stroke="gray" stroke-dasharray="4 3"/>
<text x="{W - PAD_R - 4}" y="{_sy(vmax, ymax) - 5:.1f}" text-anchor="end">Vmax</text>
<line x1="{PAD_L}" y1="{_sy(vmax / 2, ymax):.1f}" x2="{_sx(km, xmax):.1f}" y2="{_sy(vmax / 2, ymax):.1f}" stroke="gray" stroke-dasharray="4 3"/>
<line x1="{_sx(km, xmax):.1f}" y1="{_sy(vmax / 2, ymax):.1f}" x2="{_sx(km, xmax):.1f}" y2="{H - PAD_B}" stroke="gray" stroke-dasharray="4 3"/>
<text x="{PAD_L + 4}" y="{_sy(vmax / 2, ymax) - 5:.1f}">½Vmax</text>
<text x="{_sx(km, xmax):.1f}" y="{H - PAD_B + 14}" text-anchor="middle">Km</text>"""
    return _frame(body, "[S]", "v₀")


def oxygen_dissociation() -> str:
    xmax, ymax = 100.0, 105.0
    hb = _path(lambda p: 100 * p**2.8 / (26**2.8 + p**2.8), xmax, ymax)
    mb = _path(lambda p: 100 * p / (2.8 + p), xmax, ymax)
    body = f"""<polyline points="{mb}" fill="none" stroke="#b03030" stroke-width="2"/>
<polyline points="{hb}" fill="none" stroke="#1f4e9c" stroke-width="2"/>
<text x="{_sx(14, xmax):.1f}" y="{_sy(92, ymax):.1f}" fill="#b03030">Myoglobin</text>
<text x="{_sx(42, xmax):.1f}" y="{_sy(52, ymax):.1f}" fill="#1f4e9c">Hemoglobin</text>
<line x1="{_sx(26, xmax):.1f}" y1="{_sy(50, ymax):.1f}" x2="{_sx(26, xmax):.1f}" y2="{H - PAD_B}" stroke="gray" stroke-dasharray="4 3"/>
<text x="{_sx(26, xmax):.1f}" y="{H - PAD_B + 14}" text-anchor="middle">P50 ≈ 26</text>"""
    return _frame(body, "pO₂ (mmHg)", "% O₂ saturation")


def action_potential() -> str:
    xmax, lo, hi = 6.0, -90.0, 45.0

    def vm(t: float) -> float:
        if t < 1.0:
            return -70
        if t < 1.3:
            return -70 + 15 * (t - 1.0) / 0.3
        if t < 1.7:
            return -55 + 95 * math.sin((t - 1.3) / 0.4 * math.pi / 2)
        if t < 2.6:
            return 40 - 125 * (t - 1.7) / 0.9
        if t < 4.2:
            return -85 + 15 * (1 - math.exp(-(t - 2.6) * 2.5))
        return -70

    curve = _path(lambda t: vm(t) - lo, xmax, hi - lo, n=300)

    def y(v: float) -> float:
        return _sy(v - lo, hi - lo)

    body = f"""<polyline points="{curve}" fill="none" stroke="#1f4e9c" stroke-width="2"/>
<line x1="{PAD_L}" y1="{y(-55):.1f}" x2="{W - PAD_R}" y2="{y(-55):.1f}" stroke="gray" stroke-dasharray="4 3"/>
<text x="{W - PAD_R - 2}" y="{y(-55) - 4:.1f}" text-anchor="end">threshold −55</text>
<text x="{PAD_L - 4}" y="{y(-70) + 4:.1f}" text-anchor="end">−70</text>
<text x="{PAD_L - 4}" y="{y(40) + 4:.1f}" text-anchor="end">+40</text>
<text x="{_sx(1.15, xmax):.1f}" y="{y(10):.1f}" text-anchor="end">1</text>
<text x="{_sx(2.35, xmax):.1f}" y="{y(10):.1f}">2</text>
<text x="{_sx(3.0, xmax):.1f}" y="{y(-90) + 2:.1f}">3</text>"""
    return _frame(body, "time (ms)", "Vm (mV)")


def amino_acid_zwitterion() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200" font-family="Helvetica, Arial, sans-serif" font-size="18">
<rect width="300" height="200" fill="white"/>
<text x="150" y="40" text-anchor="middle">R</text>
<line x1="150" y1="48" x2="150" y2="85" stroke="black" stroke-width="2"/>
<text x="150" y="105" text-anchor="middle">C</text>
<text x="165" y="96" font-size="12">α</text>
<line x1="138" y1="100" x2="92" y2="100" stroke="black" stroke-width="2"/>
<text x="62" y="106" text-anchor="middle">H₃N⁺</text>
<line x1="162" y1="100" x2="205" y2="100" stroke="black" stroke-width="2"/>
<text x="215" y="106">C</text>
<line x1="220" y1="112" x2="220" y2="140" stroke="black" stroke-width="2"/>
<line x1="226" y1="112" x2="226" y2="140" stroke="black" stroke-width="2"/>
<text x="223" y="160" text-anchor="middle">O</text>
<line x1="232" y1="100" x2="262" y2="100" stroke="black" stroke-width="2"/>
<text x="268" y="106">O⁻</text>
<line x1="150" y1="112" x2="150" y2="145" stroke="black" stroke-width="2"/>
<text x="150" y="165" text-anchor="middle">H</text>
</svg>
"""


FIGURES = {
    "michaelis_menten.svg": michaelis_menten,
    "oxygen_dissociation.svg": oxygen_dissociation,
    "action_potential.svg": action_potential,
    "amino_acid_zwitterion.svg": amino_acid_zwitterion,
}
