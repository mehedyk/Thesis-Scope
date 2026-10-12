"""Regenerates every logo/icon/animation asset in ../assets (SVG hand-written, GIF/PNG/ICO via Pillow)."""
import math, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"); os.makedirs(OUT, exist_ok=True)
W = lambda n, s: open(os.path.join(OUT, n), "w", encoding="utf-8").write(s)

def inner(p):
    L = lambda y, w, vals, kt: f'<rect x="80" y="{y}" width="{w}" height="9" rx="4.5" fill="#cbd5e1"><animate attributeName="fill" values="{vals}" keyTimes="{kt}" dur="4s" repeatCount="indefinite"/></rect>'
    return f"""<defs><linearGradient id="{p}g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4f46e5"/><stop offset="1" stop-color="#06b6d4"/></linearGradient>
<clipPath id="{p}c"><path d="M70 44h78l46 46v122a8 8 0 0 1-8 8H70a8 8 0 0 1-8-8V52a8 8 0 0 1 8-8z"/></clipPath></defs>
<rect width="256" height="256" rx="56" fill="url(#{p}g)"/>
<path d="M70 44h78l46 46v122a8 8 0 0 1-8 8H70a8 8 0 0 1-8-8V52a8 8 0 0 1 8-8z" fill="#fff"/>
<path d="M148 44v30a8 8 0 0 0 8 8h30z" fill="#c7d2fe"/>
{L(96,96,"#cbd5e1;#34d399;#cbd5e1;#cbd5e1","0;.18;.34;1")}{L(120,104,"#cbd5e1;#cbd5e1;#f87171;#cbd5e1;#cbd5e1","0;.2;.32;.5;1")}{L(144,84,"#cbd5e1;#cbd5e1;#34d399;#cbd5e1;#cbd5e1","0;.38;.5;.66;1")}{L(168,100,"#cbd5e1;#cbd5e1;#fbbf24;#cbd5e1;#cbd5e1","0;.55;.66;.82;1")}{L(192,72,"#cbd5e1;#cbd5e1;#34d399;#cbd5e1;#cbd5e1","0;.72;.84;.96;1")}
<g clip-path="url(#{p}c)"><rect x="60" y="30" width="140" height="16" fill="#22d3ee" opacity=".55"><animate attributeName="y" values="36;212;36" keyTimes="0;.5;1" dur="4s" repeatCount="indefinite"/></rect></g>
<circle cx="176" cy="176" r="34" fill="#4f46e5" fill-opacity=".35" stroke="#fff" stroke-width="10"><animate attributeName="r" values="34;38;34" dur="2s" repeatCount="indefinite"/></circle>
<path d="M201 201l26 26" stroke="#fff" stroke-width="13" stroke-linecap="round"/>
<path d="M161 177l11 11 21-24" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="60" stroke-dashoffset="60"><animate attributeName="stroke-dashoffset" values="60;0;0;60" keyTimes="0;.25;.85;1" dur="4s" repeatCount="indefinite"/></path>"""

W("logo.svg", f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">{inner("a")}</svg>')
W("favicon.svg", f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">{inner("f")}</svg>')

dots = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#22d3ee" opacity=".35"><animate attributeName="cy" values="{y};{y-40};{y}" dur="{d}s" repeatCount="indefinite"/><animate attributeName="opacity" values=".1;.5;.1" dur="{d}s" repeatCount="indefinite"/></circle>'
               for x, y, r, d in [(520,60,3,5),(700,250,4,6),(900,90,2.5,4),(1100,230,3.5,7),(1200,70,3,5.5),(610,280,2,4.5),(1000,40,2,6.5)])
FN = 'font-family="Segoe UI,Helvetica,Arial,sans-serif"'
W("banner.svg", f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 320" width="1280" height="320">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0f172a"/><stop offset="1" stop-color="#1e1b4b"/></linearGradient>
<linearGradient id="tx" x1="0" x2="1"><stop offset="0" stop-color="#818cf8"><animate attributeName="stop-color" values="#818cf8;#22d3ee;#818cf8" dur="6s" repeatCount="indefinite"/></stop><stop offset="1" stop-color="#22d3ee"><animate attributeName="stop-color" values="#22d3ee;#818cf8;#22d3ee" dur="6s" repeatCount="indefinite"/></stop></linearGradient>
<linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#22d3ee" stop-opacity="0"/><stop offset=".5" stop-color="#22d3ee" stop-opacity=".25"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></linearGradient>
<clipPath id="tp"><rect x="300" y="190" width="0" height="50"><animate attributeName="width" values="0;800;800;0" keyTimes="0;.45;.9;1" dur="8s" repeatCount="indefinite"/></rect></clipPath></defs>
<rect width="1280" height="320" fill="url(#bg)"/>
<circle cx="190" cy="160" r="150" fill="#4f46e5" opacity=".18"><animate attributeName="r" values="140;170;140" dur="5s" repeatCount="indefinite"/></circle>
{dots}<rect y="0" width="160" height="320" fill="url(#sw)"><animate attributeName="x" values="-160;1280" dur="6s" repeatCount="indefinite"/></rect>
<g transform="translate(60,32)">{inner("b")}</g>
<text x="300" y="150" {FN} font-size="72" font-weight="800" fill="url(#tx)">ThesisScope</text>
<g clip-path="url(#tp)"><text x="300" y="222" font-family="Consolas,Menlo,monospace" font-size="26" fill="#cbd5e1">Explainable AI-text &amp; plagiarism checks for whole theses</text></g>
<rect x="300" y="198" width="3" height="32" fill="#22d3ee"><animate attributeName="x" values="300;1100;1100;300" keyTimes="0;.45;.9;1" dur="8s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect></svg>""")

nodes = [("1 · Upload", ".docx / .pdf / .txt", "#6366f1"), ("2 · Split", "150–300 word blocks\nreferences removed", "#8b5cf6"), ("3 · AI detection", "EditLens + Binoculars\ncalibrated thresholds", "#06b6d4"),
         ("4 · Source checks", "local · infini-gram · web\nCrossref references", "#10b981"), ("5 · Report", "Low / Medium / High\nwith “why” boxes", "#f59e0b")]
g = ""
for i, (t, s, c) in enumerate(nodes):
    x = 30 + i * 235
    g += f'<rect x="{x}" y="105" width="200" height="120" rx="16" fill="#111827" stroke="{c}" stroke-width="3"><animate attributeName="stroke-opacity" values=".4;1;.4" begin="{i*.8}s" dur="4s" repeatCount="indefinite"/></rect><text x="{x+100}" y="148" text-anchor="middle" {FN} font-size="19" font-weight="700" fill="{c}">{t}</text>'
    g += "".join(f'<text x="{x+100}" y="{176+j*20}" text-anchor="middle" {FN} font-size="14" fill="#cbd5e1">{ln}</text>' for j, ln in enumerate(s.split("\n")))
    if i < 4: g += f'<path d="M{x+205} 165h25" stroke="#64748b" stroke-width="3" stroke-dasharray="6 5" marker-end="url(#ar)"><animate attributeName="stroke-dashoffset" values="22;0" dur="1s" repeatCount="indefinite"/></path>'
W("pipeline.svg", f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 330" width="1200" height="330"><defs><marker id="ar" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0 0L8 4L0 8z" fill="#64748b"/></marker></defs>
<rect width="1200" height="330" rx="20" fill="#0b1020"/><text x="600" y="55" text-anchor="middle" {FN} font-size="26" font-weight="700" fill="#e2e8f0">How a check flows</text>{g}
<circle r="7" fill="#22d3ee"><animateMotion dur="7s" repeatCount="indefinite" path="M130 165H1100"/></circle>
<text x="600" y="285" text-anchor="middle" {FN} font-size="14" fill="#94a3b8">Everything is cached, so re-running after edits only rescans changed blocks.</text></svg>""")

def chip(x, y, lab, col): return f'<rect x="{x}" y="{y}" width="64" height="20" rx="10" fill="{col}"/><text x="{x+32}" y="{y+15}" text-anchor="middle" font-size="12" fill="#fff">{lab}</text>'
cardc = lambda x, lab, n, col, w=200: f'<rect x="{x}" y="62" width="{w}" height="70" rx="12" fill="none" stroke="{col}" stroke-width="2"/><text x="{x+w//2}" y="95" font-size="26" font-weight="700" fill="#fff">{n}</text><text x="{x+w//2}" y="119">{lab}</text>'
W("ui-demo.svg", f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 560" width="900" height="560">
<rect width="900" height="560" rx="18" fill="#0b1020"/><rect width="900" height="40" rx="18" fill="#1f2937"/><circle cx="24" cy="20" r="6" fill="#f87171"/><circle cx="44" cy="20" r="6" fill="#fbbf24"/><circle cx="64" cy="20" r="6" fill="#34d399"/>
<text x="450" y="26" text-anchor="middle" {FN} font-size="14" fill="#9ca3af">ThesisScope — report (animated preview)</text>
<g {FN} text-anchor="middle" font-size="13" fill="#cbd5e1">{cardc(30,"blocks · 7,043 words",34,"#64748b")}{cardc(250,"High",2,"#d64545")}{cardc(470,"Medium",5,"#d9a300")}{cardc(690,"Low",27,"#2a9d5b",180)}</g>
<g {FN} font-size="14" fill="#e5e7eb">
<rect x="30" y="152" width="840" height="46" rx="10" fill="#111827" stroke="#334155"/>{chip(44,165,"Low","#2a9d5b")}<text x="120" y="181">#1  Health expenditure per capita rose from about $8 to $57…</text>
<rect x="30" y="208" width="840" height="46" rx="10" fill="#111827" stroke="#d9a300"><animate attributeName="height" values="46;46;200;200;46" keyTimes="0;.15;.3;.85;1" dur="9s" repeatCount="indefinite"/></rect>
{chip(44,221,"Medium","#d9a300")}<text x="120" y="237">#2  Section 3.1 definitions of current health expenditure…  ▾</text>
<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.3;.38;.85;.9" dur="9s" repeatCount="indefinite"/>
<text x="48" y="276" font-weight="700">Why this rating</text><text x="48" y="302" fill="#cbd5e1">• EditLens AI score 0.41 → medium (High ≥ 0.60, Medium ≥ 0.35)</text>
<text x="48" y="326" fill="#cbd5e1">• Binoculars 0.93 (z = −1.2) → more predictable than baseline</text><text x="48" y="350" fill="#fbbf24">⚠ Formulaic text (definitions): detectors often flag this wrongly</text>
<text x="48" y="374" fill="#cbd5e1">• Possible overlap: exact 12-word phrase found in an open web corpus</text></g>
<g><animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 154;0 154;0 0" keyTimes="0;.15;.3;.85;1" dur="9s" repeatCount="indefinite"/>
<rect x="30" y="264" width="840" height="46" rx="10" fill="#111827" stroke="#d64545"/>{chip(44,277,"High","#d64545")}<text x="120" y="293">#7  Both detectors agree this paragraph reads as AI-written…</text>
<rect x="30" y="320" width="840" height="46" rx="10" fill="#111827" stroke="#334155"/>{chip(44,333,"Low","#2a9d5b")}<text x="120" y="349">#8  The ARDL bounds test finds no long-run relationship…</text></g></g></svg>""")

def logo(S=512, t=0.0):
    k = S / 256; y, x = np.mgrid[0:S, 0:S]; tt = (x + y) / (2 * S)
    c1, c2 = np.array([79, 70, 229]), np.array([6, 182, 212])
    img = Image.fromarray((c1 * (1 - tt[..., None]) + c2 * tt[..., None]).astype("uint8")).convert("RGBA")
    m = Image.new("L", (S, S), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(56 * k), fill=255)
    bg = Image.new("RGBA", (S, S), (0, 0, 0, 0)); bg.paste(img, (0, 0), m)
    d = ImageDraw.Draw(bg, "RGBA"); P = lambda p: [(a * k, b * k) for a, b in p]
    d.polygon(P([(70, 44), (148, 44), (194, 90), (194, 212), (186, 220), (70, 220), (62, 212), (62, 52)]), fill=(255, 255, 255, 255))
    d.polygon(P([(148, 44), (148, 74), (156, 82), (186, 82)]), fill=(199, 210, 254, 255))
    sy = 36 + 176 * (1 - abs(2 * t - 1))
    for ly, w, col in [(100, 96, (52, 211, 153)), (124, 104, (248, 113, 113)), (148, 84, (52, 211, 153)), (172, 100, (251, 191, 36)), (196, 72, (52, 211, 153))]:
        hot = abs(sy + 8 - ly) < 16
        d.rounded_rectangle([80 * k, (ly - 4.5) * k, (80 + w) * k, (ly + 4.5) * k], radius=max(1, int(4.5 * k)), fill=col + (255,) if hot else (203, 213, 225, 255))
    ov = Image.new("RGBA", (S, S), (0, 0, 0, 0)); ImageDraw.Draw(ov).rectangle([62 * k, max(44, sy) * k, 194 * k, min(220, sy + 16) * k], fill=(34, 211, 238, 140))
    bg = Image.alpha_composite(bg, ov); d = ImageDraw.Draw(bg, "RGBA"); r = (34 + 3 * math.sin(t * 2 * math.pi)) * k; c = 176 * k
    d.ellipse([c - r, c - r, c + r, c + r], fill=(79, 70, 229, 90), outline=(255, 255, 255, 255), width=max(1, int(10 * k)))
    d.line([(201 * k, 201 * k), (227 * k, 227 * k)], fill=(255, 255, 255, 255), width=max(1, int(13 * k)))
    d.line([(161 * k, 177 * k), (172 * k, 188 * k), (193 * k, 164 * k)], fill=(255, 255, 255, 255), width=max(1, int(8 * k)), joint="curve")
    return bg

N = 36; pal = []
for i in range(N):
    f = logo(512, i / N).resize((256, 256), Image.LANCZOS); b = Image.new("RGBA", f.size, (15, 23, 42, 255)); b.alpha_composite(f); pal.append(b.convert("RGB").quantize(256))
pal[0].save(os.path.join(OUT, "logo.gif"), save_all=True, append_images=pal[1:], duration=90, loop=0)
base = logo(512, 0.5); base.save(os.path.join(OUT, "logo.png"))
for s in (16, 32, 48, 64, 128, 192, 256, 512): base.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, f"favicon-{s}.png"))
base.resize((180, 180), Image.LANCZOS).save(os.path.join(OUT, "apple-touch-icon.png"))
base.save(os.path.join(OUT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
a = np.zeros((630, 1200, 3), "uint8")
for i in range(3): a[..., i] = np.linspace([15, 23, 42][i], [30, 27, 75][i], 1200)[None, :]
og = Image.fromarray(a); lg = logo(300, 0.5); og.paste(lg, (90, 165), lg)
dr = ImageDraw.Draw(og); fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 86); fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
dr.text((440, 200), "ThesisScope", font=fb, fill=(129, 140, 248)); dr.text((440, 320), "Explainable AI-text & plagiarism", font=fs, fill=(203, 213, 225)); dr.text((440, 368), "checks for whole theses", font=fs, fill=(203, 213, 225))
og.save(os.path.join(OUT, "og-image.png"))
open(os.path.join(OUT, "site.webmanifest"), "w").write('{"name":"ThesisScope","short_name":"ThesisScope","icons":[{"src":"favicon-192.png","sizes":"192x192","type":"image/png"},{"src":"favicon-512.png","sizes":"512x512","type":"image/png"}],"theme_color":"#4f46e5","background_color":"#0f172a","display":"standalone"}')
print(sorted(os.listdir(OUT)))
