"""Mini-Renderbibliothek fuer Lernvideos: PIL-Frames in 1920x1080."""
import math, os, textwrap
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
CAP_Y = 892                      # Oberkante der Untertitel-Leiste
FDIR = "/usr/share/fonts/truetype/dejavu/"
_fc = {}


def F(size, bold=False, mono=False, serif=False):
    if serif:
        name = "DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf"
    elif mono:
        name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    else:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    key = (name, size)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(FDIR + name, size)
    return _fc[key]


@dataclass
class Theme:
    bg1: tuple
    bg2: tuple
    panel: tuple
    panel2: tuple
    fg: tuple
    muted: tuple
    a1: tuple          # Hauptakzent
    a2: tuple          # Warn-/Gegenakzent
    a3: tuple          # dritter Akzent
    capbg: tuple
    capfg: tuple
    line: tuple


DARK = Theme(
    bg1=(16, 21, 28), bg2=(9, 12, 17), panel=(27, 34, 44), panel2=(36, 45, 58),
    fg=(234, 240, 246), muted=(140, 155, 172),
    a1=(45, 212, 191), a2=(248, 86, 86), a3=(245, 185, 66),
    capbg=(6, 9, 13), capfg=(236, 242, 248), line=(58, 72, 90))

LIGHT = Theme(
    bg1=(250, 248, 244), bg2=(238, 234, 227), panel=(255, 255, 255), panel2=(244, 240, 233),
    fg=(32, 34, 38), muted=(116, 120, 128),
    a1=(232, 112, 24), a2=(40, 96, 168), a3=(28, 140, 108),
    capbg=(26, 27, 30), capfg=(248, 246, 242), line=(206, 200, 190))


def _mix(c1, c2, t):
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(3))


def new_frame(th, grid=True):
    img = Image.new("RGB", (W, H), th.bg1)
    d = ImageDraw.Draw(img)
    for y in range(0, CAP_Y):
        d.line([(0, y), (W, y)], fill=_mix(th.bg1, th.bg2, y / CAP_Y))
    if grid:
        g = _mix(th.bg1, th.line, 0.18)
        for x in range(0, W, 80):
            d.line([(x, 0), (x, CAP_Y)], fill=g)
        for y in range(0, CAP_Y, 80):
            d.line([(0, y), (W, y)], fill=g)
    return img, d


def wrap(text, font, maxw):
    out, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if font.getlength(t) <= maxw or not cur:
            cur = t
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def txt(d, xy, s, font, fill, anchor="la"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def txt_block(d, x, y, s, font, fill, maxw, lh=None, anchor="l", center_x=None):
    lh = lh or int(font.size * 1.38)
    for i, ln in enumerate(wrap(s, font, maxw)):
        if anchor == "c":
            d.text((center_x if center_x is not None else x, y + i * lh), ln,
                   font=font, fill=fill, anchor="ma")
        else:
            d.text((x, y + i * lh), ln, font=font, fill=fill, anchor="la")
    return y + len(wrap(s, font, maxw)) * lh


def card(d, box, fill, border=None, r=20, width=3):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=border, width=width)


def header(d, th, kicker, title, num=None, total=None):
    d.rectangle([0, 0, W, 6], fill=th.a1)
    txt(d, (96, 44), kicker.upper(), F(26, True), th.a1)
    txt(d, (96, 84), title, F(58, True), th.fg)
    if num:
        txt(d, (W - 96, 52), f"{num}/{total}", F(30, True), th.muted, anchor="ra")
    d.line([(96, 172), (W - 96, 172)], fill=th.line, width=2)


def caption(img, d, th, text):
    d.rectangle([0, CAP_Y, W, H], fill=th.capbg)
    d.line([(0, CAP_Y), (W, CAP_Y)], fill=th.a1, width=4)
    f = F(40)
    lines = wrap(text, f, W - 260)
    if len(lines) > 2:                      # notfalls kleiner setzen
        f = F(34)
        lines = wrap(text, f, W - 220)[:3]
    lh = int(f.size * 1.3)
    y0 = CAP_Y + (H - CAP_Y - len(lines) * lh) / 2 + 4
    for i, ln in enumerate(lines):
        d.text((W / 2, y0 + i * lh), ln, font=f, fill=th.capfg, anchor="ma")


def arrow(d, p1, p2, color, w=5, head=18, dash=False):
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    L = max(math.hypot(dx, dy), 1e-6)
    ux, uy = dx / L, dy / L
    ex, ey = x2 - ux * head * 0.9, y2 - uy * head * 0.9
    if dash:
        seg, pos = 18, 0.0
        while pos < L - head:
            a = (x1 + ux * pos, y1 + uy * pos)
            b = (x1 + ux * min(pos + seg, L - head), y1 + uy * min(pos + seg, L - head))
            d.line([a, b], fill=color, width=w)
            pos += seg * 2
    else:
        d.line([(x1, y1), (ex, ey)], fill=color, width=w)
    px, py = -uy, ux
    d.polygon([(x2, y2), (ex + px * head * 0.62, ey + py * head * 0.62),
               (ex - px * head * 0.62, ey - py * head * 0.62)], fill=color)


def dot(d, xy, r, fill, outline=None, width=2):
    x, y = xy
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline, width=width)


def pill(d, xy, text, font, fg, bg, pad=(22, 11), anchor="lt", r=None):
    tw = font.getlength(text)
    th_ = font.size * 1.34
    x, y = xy
    if anchor[0] == "c":
        x -= (tw + 2 * pad[0]) / 2
    if anchor[0] == "r":
        x -= tw + 2 * pad[0]
    box = [x, y, x + tw + 2 * pad[0], y + th_ + 2 * pad[1]]
    d.rounded_rectangle(box, radius=r if r is not None else int(th_ / 2 + pad[1]), fill=bg)
    d.text((x + pad[0], y + pad[1] - 1), text, font=font, fill=fg)
    return box


def bullets(d, x, y, items, shown, th, accent, size=36, lh=None, maxw=1500, gap=24):
    """items: Liste von str oder (str, sub). shown: Anzahl sichtbarer Punkte."""
    f, fs = F(size, True), F(int(size * 0.8))
    lh = lh or int(size * 1.3)
    cy = y
    for i, it in enumerate(items):
        main, sub = (it, None) if isinstance(it, str) else it
        on = i < shown
        col = th.fg if on else _mix(th.bg1, th.muted, 0.35)
        acc = accent if on else _mix(th.bg1, th.muted, 0.3)
        dot(d, (x + 9, cy + size * 0.55), 9, acc)
        ls = wrap(main, f, maxw)
        for j, ln in enumerate(ls):
            d.text((x + 38, cy + j * lh), ln, font=f, fill=col)
        cy += len(ls) * lh
        if sub:
            sl = wrap(sub, fs, maxw - 20)
            for j, ln in enumerate(sl):
                d.text((x + 40, cy + 2 + j * int(fs.size * 1.3)), ln, font=fs,
                       fill=th.muted if on else _mix(th.bg1, th.muted, 0.25))
            cy += len(sl) * int(fs.size * 1.3) + 4
        cy += gap
    return cy


def big_statement(img, d, th, text, color=None, sub=None):
    """Grosser Merksatz, vollflaechig."""
    d.rectangle([0, 0, W, CAP_Y], fill=th.bg2)
    col = color or th.a3
    d.rectangle([0, 0, 14, CAP_Y], fill=col)
    f = F(72, True)
    lines = wrap(text, f, W - 420)
    if len(lines) > 3:
        f = F(58, True)
        lines = wrap(text, f, W - 380)
    lh = int(f.size * 1.3)
    y0 = (CAP_Y - len(lines) * lh) / 2 - (40 if sub else 0)
    for i, ln in enumerate(lines):
        d.text((W / 2, y0 + i * lh), ln, font=f, fill=th.fg, anchor="ma")
    if sub:
        d.text((W / 2, y0 + len(lines) * lh + 34), sub, font=F(36), fill=col, anchor="ma")


def title_card(img, d, th, kicker, title, sub, badge=None):
    d.rectangle([0, 0, W, CAP_Y], fill=th.bg2)
    for i in range(7):
        d.line([(0, CAP_Y - 70 + i * 10), (W, CAP_Y - 70 + i * 10)],
               fill=_mix(th.bg2, th.a1, 0.08 + i * 0.03))
    txt(d, (W / 2, 250), kicker.upper(), F(34, True), th.a1, anchor="ma")
    f = F(104, True)
    lines = wrap(title, f, W - 300)
    for i, ln in enumerate(lines):
        d.text((W / 2, 320 + i * 124), ln, font=f, fill=th.fg, anchor="ma")
    y = 320 + len(lines) * 124 + 20
    d.line([(W / 2 - 180, y), (W / 2 + 180, y)], fill=th.a1, width=5)
    txt(d, (W / 2, y + 40), sub, F(42), th.muted, anchor="ma")
    if badge:
        pill(d, (W / 2, y + 130), badge, F(30, True), th.bg2, th.a3, anchor="ct")


def chip_row(d, x, y, chips, shown, th, size=28):
    f = F(size, True)
    cx = x
    for i, (t, col) in enumerate(chips):
        on = i < shown
        bg = col if on else _mix(th.bg1, th.muted, 0.22)
        fg = th.bg1 if on else _mix(th.bg1, th.muted, 0.5)
        b = pill(d, (cx, y), t, f, fg, bg)
        cx = b[2] + 16
    return cx


def save(img, path):
    img.save(path, "PNG", optimize=False, compress_level=1)
