# -*- coding: utf-8 -*-
"""Video 1 - Biologie: E605 (Parathion) und die Acetylcholinesterase."""
import math
from vlib import *
from vlib import _mix

TH = DARK
T = TH
SHOTS = []


def add(text, fn):
    SHOTS.append((text, fn))


# ================================================================ Bausteine
def hexagon(d, cx, cy, r, col, width=4, aromatic=True):
    pts = [(cx + r * math.cos(math.radians(60 * i - 30)),
            cy + r * math.sin(math.radians(60 * i - 30))) for i in range(6)]
    for i in range(6):
        d.line([pts[i], pts[(i + 1) % 6]], fill=col, width=width)
    if aromatic:
        d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55],
                  outline=col, width=3)
    return pts


def parathion(d, x, y, stage, col=None):
    """Skelettformel von Parathion, stufenweise."""
    col = col or T.fg
    dim = _mix(T.bg1, T.muted, 0.35)
    f = F(30, True)
    c1 = col if stage >= 1 else dim
    pts = hexagon(d, x + 130, y + 120, 92, c1)
    if stage >= 1:
        d.line([(x + 130, y + 28), (x + 130, y - 16)], fill=c1, width=4)
        d.text((x + 130, y - 50), "NO₂", font=f, fill=T.a3, anchor="ma")
    c2 = col if stage >= 2 else dim
    d.line([(x + 222, y + 120), (x + 292, y + 120)], fill=c2, width=4)
    d.text((x + 310, y + 100), "O", font=f, fill=c2)
    d.line([(x + 352, y + 120), (x + 420, y + 120)], fill=c2, width=4)
    c3 = col if stage >= 3 else dim
    d.text((x + 432, y + 98), "P", font=F(40, True), fill=c3)
    if stage >= 3:
        d.line([(x + 448, y + 90), (x + 448, y + 34)], fill=T.a2, width=4)
        d.line([(x + 462, y + 90), (x + 462, y + 34)], fill=T.a2, width=4)
        d.text((x + 455, y - 2), "S", font=F(40, True), fill=T.a2, anchor="ma")
        d.text((x + 500, y + 10), "Thion-Schwefel", font=F(24, True), fill=T.a2)
    c4 = col if stage >= 4 else dim
    d.line([(x + 486, y + 118), (x + 556, y + 118)], fill=c4, width=4)
    d.text((x + 568, y + 96), "O–C₂H₅", font=f, fill=c4)
    d.line([(x + 452, y + 148), (x + 452, y + 210)], fill=c4, width=4)
    d.text((x + 430, y + 218), "O–C₂H₅", font=f, fill=c4)


def synapse(d, box, stage, poisoned=False, scale=1.0, mini=False):
    """Cholinerge Synapse. stage 1..5 (normal) bzw. Gift-Darstellung."""
    x0, y0, x1, y1 = box
    w = x1 - x0
    pre = [x0 + w * 0.06, y0, x0 + w * 0.62, y0 + (y1 - y0) * 0.42]
    cleft_t = pre[3] + 14 * scale
    cleft_b = cleft_t + (y1 - y0) * 0.21
    post_t = cleft_b
    fs = max(int(26 * scale), 15)
    card(d, pre, T.panel, T.a1, r=int(24 * scale), width=int(4 * scale) or 2)
    if not mini:
        d.text((pre[0] + 20, pre[1] + 12), "Präsynapse", font=F(fs, True), fill=T.a1)
    # Vesikel
    vn = 4 if stage < 2 else 3
    for i in range(vn):
        vx = pre[0] + 90 * scale + i * 110 * scale
        vy = pre[1] + (pre[3] - pre[1]) * 0.42
        dot(d, (vx, vy), 34 * scale, T.panel2, T.a1, max(int(3 * scale), 2))
        for k in range(5):
            a = k * 1.26
            dot(d, (vx + 16 * scale * math.cos(a), vy + 16 * scale * math.sin(a)),
                5 * scale, T.a1)
    # Fusionierendes Vesikel
    if stage >= 2:
        fx = pre[2] - 150 * scale
        d.arc([fx - 36 * scale, pre[3] - 36 * scale, fx + 36 * scale, pre[3] + 36 * scale],
              180, 360, fill=T.a1, width=max(int(4 * scale), 2))
    # Ca-Kanal
    if stage >= 1:
        cx = pre[0] + 40 * scale
        d.rectangle([cx, pre[3] - 12 * scale, cx + 30 * scale, pre[3] + 12 * scale],
                    fill=T.a3)
        arrow(d, (cx + 15 * scale, pre[3] + 86 * scale), (cx + 15 * scale, pre[3] - 20 * scale),
              T.a3, max(int(4 * scale), 2), int(14 * scale))
        if not mini:
            d.text((cx + 40 * scale, pre[3] + 40 * scale), "Ca²⁺",
                   font=F(fs, True), fill=T.a3)
    # Spalt
    d.rectangle([x0, cleft_t, x1, cleft_b], fill=_mix(T.bg1, T.panel, 0.4))
    if not mini:
        d.text((x1 - 16, cleft_t + 8), "synaptischer Spalt", font=F(fs), fill=T.muted,
               anchor="ra")
    # Postsynapse
    d.rectangle([x0, post_t, x1, y1], fill=T.panel)
    d.line([(x0, post_t), (x1, post_t)], fill=T.a1 if not poisoned else T.a2,
           width=max(int(5 * scale), 2))
    if not mini:
        d.text((x0 + 20, y1 - 46 * scale), "Postsynapse", font=F(fs, True),
               fill=T.a1 if not poisoned else T.a2)
    # Rezeptoren
    rxs = [x0 + w * 0.3, x0 + w * 0.52, x0 + w * 0.74]
    for i, rx in enumerate(rxs):
        bound = (stage >= 3 and not poisoned) or poisoned
        col = T.a2 if (poisoned and stage >= 3) else (T.a1 if bound else T.muted)
        d.polygon([(rx - 34 * scale, post_t + 44 * scale), (rx - 22 * scale, post_t - 6),
                   (rx + 22 * scale, post_t - 6), (rx + 34 * scale, post_t + 44 * scale)],
                  fill=T.panel2, outline=col, width=max(int(4 * scale), 2))
        if bound:
            dot(d, (rx, post_t + 2), 11 * scale, T.a1 if not poisoned else T.a2)
        if stage >= 4 and not poisoned:
            arrow(d, (rx, post_t + 10 * scale), (rx, post_t + 110 * scale), T.a3,
                  max(int(4 * scale), 2), int(13 * scale))
            if not mini:
                d.text((rx + 16 * scale, post_t + 58 * scale), "Na⁺",
                       font=F(fs, True), fill=T.a3)
    # ACh im Spalt
    cy = (cleft_t + cleft_b) / 2
    if poisoned:
        n = 26
        for i in range(n):
            ax = x0 + 50 + (i * 71) % (w - 100)
            ay = cleft_t + 14 + (i * 37) % max(int(cleft_b - cleft_t - 24), 10)
            dot(d, (ax, ay), 10 * scale, T.a2)
    elif stage == 2:
        for i in range(6):
            dot(d, (pre[2] - 190 * scale + i * 26 * scale, cy + (i % 2) * 14), 10 * scale, T.a1)
    elif stage == 3:
        for i in range(8):
            dot(d, (x0 + w * 0.22 + i * w * 0.07, cy + (i % 3 - 1) * 12), 10 * scale, T.a1)
    elif stage == 4:
        for i in range(5):
            dot(d, (x0 + w * 0.36 + i * w * 0.09, cy), 10 * scale, T.a1)
    # AChE
    if stage >= 5 and not poisoned:
        ex = x0 + w * 0.86
        dot(d, (ex, cy), 30 * scale, T.panel2, T.a3, max(int(4 * scale), 2))
        d.line([(ex - 16 * scale, cy - 14 * scale), (ex + 16 * scale, cy + 14 * scale)],
               fill=T.a3, width=max(int(4 * scale), 2))
        d.line([(ex - 16 * scale, cy + 14 * scale), (ex + 16 * scale, cy - 14 * scale)],
               fill=T.a3, width=max(int(4 * scale), 2))
        if not mini:
            d.text((ex, cy + 46 * scale), "AChE", font=F(fs, True), fill=T.a3, anchor="ma")
            d.text((ex - 120 * scale, cy - 52 * scale), "→ Acetat + Cholin",
                   font=F(fs), fill=T.a3)
    if poisoned:
        ex = x0 + w * 0.86
        dot(d, (ex, cy), 30 * scale, T.panel2, T.a2, max(int(4 * scale), 2))
        d.line([(ex - 20 * scale, cy - 20 * scale), (ex + 20 * scale, cy + 20 * scale)],
               fill=T.a2, width=max(int(5 * scale), 2))
        if not mini:
            d.text((ex, cy + 46 * scale), "AChE blockiert", font=F(fs, True),
                   fill=T.a2, anchor="ma")


# ================================================================ Szene 1
def s1(stage):
    def fn(img, d):
        d.rectangle([0, 0, W, CAP_Y], fill=(18, 18, 20))
        d.rectangle([110, 60, W - 110, CAP_Y - 50], fill=(228, 223, 210))
        ink = (30, 28, 26)
        d.text((W / 2, 96), "WORMS · FEBRUAR 1954", font=F(30, True),
               fill=(120, 40, 36), anchor="ma")
        d.line([(160, 140), (W - 160, 140)], fill=ink, width=3)
        d.text((W / 2, 168), "Der Pralinenmord", font=F(96, True, serif=True),
               fill=ink, anchor="ma")
        d.line([(160, 286), (W - 160, 286)], fill=ink, width=2)
        if stage >= 1:
            txt_block(d, 180, 318, "Eine Frau bringt bei einem Besuch Schnapspralinen mit. "
                      "Kurz darauf ist eine Frau tot.", F(42, True, serif=True), ink, 1000)
        if stage >= 2:
            txt_block(d, 180, 430, "Das Gift darin war ein Pflanzenschutzmittel. Die "
                      "Boulevardpresse nannte es bald das „Schwiegermuttergift“.",
                      F(36, serif=True), (70, 66, 62), 1000)
        if stage >= 3:
            d.rectangle([180, 556, 1180, 560], fill=(120, 40, 36))
            txt_block(d, 180, 582, "Der erste Giftmordprozess dieser Art – es gab noch "
                      "keinen etablierten forensischen Nachweis. Der Toxikologe musste ihn "
                      "erst entwickeln.", F(34, True, serif=True), (120, 40, 36), 1000)
        # Pralinenschachtel
        bx, by = 1280, 330
        d.rounded_rectangle([bx, by, bx + 330, by + 210], radius=14,
                            fill=(118, 42, 40), outline=(70, 24, 22), width=5)
        d.rounded_rectangle([bx, by, bx + 330, by + 56], radius=14, fill=(150, 56, 52))
        for r in range(2):
            for c in range(3):
                dot(d, (bx + 70 + c * 100, by + 110 + r * 72), 28, (58, 36, 28),
                    (92, 62, 46), 3)
        d.text((1445, 580), "1954", font=F(120, True, serif=True),
               fill=(120, 40, 36), anchor="ma")
    return fn


add("Worms, Februar 1954. Eine Frau bringt bei einem Besuch Schnapspralinen mit. "
    "Kurz darauf ist eine Frau tot.", s1(1))
add("Das Gift darin war ein ganz normales Pflanzenschutzmittel. Die Boulevardpresse "
    "nannte es bald das Schwiegermuttergift.", s1(2))
add("Der Fall wurde als Pralinenmord bekannt, der erste Giftmordprozess dieser Art. Einen "
    "etablierten forensischen Nachweis für diesen Stoff gab es damals noch nicht – der "
    "Toxikologe musste ihn erst entwickeln.", s1(3))

# ================================================================ Szene 2
STECK = [
    ("E 605 = Parathion", "ein Organophosphat (Thiophosphorsäureester)"),
    ("1944 von Gerhard Schrader entwickelt", "deutscher Chemiker, Insektizidforschung"),
    ("„E“ = Ester, 605 = Laborzahl", "ursprünglich reines Insektizid"),
    ("Wirkt bei Insekt UND Mensch gleich", "dasselbe Prinzip – genau das ist das Problem"),
    ("EU-Zulassung 2002 entzogen", "später blau eingefärbt gegen Verwechslung"),
    ("Aufnahme über Haut, Atemwege, Magen-Darm", "lipophil → passiert Membranen leicht"),
]


def s2(stage, formel=0):
    def fn(img, d):
        header(d, T, "Szene 2", "Steckbrief: Was ist E 605?", 2, 7)
        bullets(d, 110, 212, STECK, stage, T, T.a1, size=32, maxw=900, gap=14)
        card(d, [1080, 210, W - 96, 560], T.panel, T.line, r=20, width=2)
        txt(d, (1112, 232), "STRUKTURFORMEL PARATHION", F(24, True), T.a1)
        parathion(d, 1130, 300, formel)
        if formel >= 4:
            card(d, [1080, 592, W - 96, 800], T.panel2, T.a2, r=20, width=3)
            txt(d, (1112, 614), "MERKE", F(24, True), T.a2)
            txt_block(d, 1112, 654, "Der Schwefel am Phosphor (P=S) macht das Molekül noch "
                      "harmlos. Er wird später im Körper getauscht.", F(28, True), T.fg, 660)
    return fn


add("Der Steckbrief. E 605 heißt eigentlich Parathion und gehört zu den Organophosphaten, "
    "genauer: ein Thiophosphorsäureester.", s2(1, 1))
add("Entwickelt hat es 1944 der deutsche Chemiker Gerhard Schrader. Das E steht für Ester, "
    "605 war schlicht die Laborzahl.", s2(3, 2))
add("Es war als Insektizid gedacht. Das Problem: Es wirkt bei Insekt und Mensch nach genau "
    "demselben Prinzip.", s2(4, 3))
add("2002 wurde die EU-Zulassung entzogen. Aufgenommen wird es über Haut, Atemwege und "
    "Magen-Darm-Trakt, denn es ist lipophil und passiert Membranen mühelos. Später färbte "
    "man es blau, damit man es nicht mit Lebensmitteln verwechselt.", s2(6, 4))

# ================================================================ Szene 3
S3_STEPS = [
    "Aktionspotential → Ca²⁺-Kanäle öffnen, Ca²⁺ strömt ein",
    "Vesikel fusionieren → Acetylcholin per Exozytose in den Spalt",
    "ACh diffundiert und bindet an die Rezeptoren",
    "Ligandengesteuerte Kanäle öffnen → Na⁺ ein → Depolarisation (EPSP)",
    "AChE spaltet ACh → Acetat + Cholin → Signal endet",
]


def s3(stage, rez=False):
    def fn(img, d):
        header(d, T, "Szene 3", "Die normale cholinerge Synapse", 3, 7)
        synapse(d, [96, 206, W - 96, 646], stage)
        y = 686
        for i, s in enumerate(S3_STEPS):
            on = i < stage
            col = T.a1 if on else _mix(T.bg1, T.muted, 0.3)
            dot(d, (118, y + 14), 14, col)
            d.text((118, y + 14), str(i + 1), font=F(19, True),
                   fill=T.bg1 if on else T.muted, anchor="mm")
            d.text((146, y - 2), s, font=F(27, True) if on else F(27),
                   fill=T.fg if on else _mix(T.bg1, T.muted, 0.35))
            y += 40
        if rez:
            card(d, [1180, 676, W - 96, 806], T.panel, T.a3, r=16, width=3)
            txt(d, (1210, 694), "ZWEI REZEPTORTYPEN", F(24, True), T.a3)
            txt(d, (1210, 734), "nicotinisch → Skelettmuskel", F(27, True), T.fg)
            txt(d, (1210, 768), "muscarinisch → innere Organe", F(27, True), T.fg)
    return fn


def s3_merk(img, d):
    big_statement(img, d, T, "Die Acetylcholinesterase ist der AUS-Schalter der Synapse.",
                  T.a3, "Fällt sie aus, bleibt das Signal an.")


add("Um das Gift zu verstehen, brauchen wir erst die normale Synapse. Schritt eins: Das "
    "Aktionspotential erreicht das Endknöpfchen, spannungsgesteuerte Calcium-Kanäle öffnen "
    "sich, Calcium strömt ein.", s3(1))
add("Schritt zwei: Die Vesikel fusionieren mit der präsynaptischen Membran und schütten "
    "Acetylcholin per Exozytose in den synaptischen Spalt.", s3(2))
add("Schritt drei: Acetylcholin diffundiert durch den Spalt und bindet an die Rezeptoren der "
    "postsynaptischen Membran. Nicotinische Rezeptoren sitzen am Skelettmuskel, muscarinische "
    "an den inneren Organen.", s3(3, True))
add("Schritt vier: Die ligandengesteuerten Ionenkanäle öffnen, Natrium strömt ein, die "
    "Membran depolarisiert. Es entsteht ein erregendes postsynaptisches Potential.", s3(4))
add("Schritt fünf, der entscheidende: Die Acetylcholinesterase im Spalt spaltet Acetylcholin "
    "in Acetat und Cholin. Das Signal endet, das Cholin wird wiederaufgenommen und recycelt.",
    s3(5))
add("Merke dir diesen einen Satz: Die Acetylcholinesterase ist der Aus-Schalter der Synapse. "
    "Fällt sie aus, bleibt das Signal an.", s3_merk)

# ================================================================ Szene 4
def s4_giftung(stage):
    def fn(img, d):
        header(d, T, "Szene 4", "Giftung: E 605 ist selbst kaum aktiv", 4, 7)
        boxes = [("E 605 / Parathion", "P = S  (Thion)", T.muted, "kaum aktiv"),
                 ("Leber: Cytochrom P450", "S → O  Austausch", T.a3, "Bioaktivierung"),
                 ("PARAOXON", "P = O  (Oxon)", T.a2, "der eigentliche Hemmstoff")]
        bw = 480
        for i, (t, f2, col, sub) in enumerate(boxes):
            x = 130 + i * (bw + 130)
            on = i < stage
            card(d, [x, 280, x + bw, 560], T.panel if on else T.panel2,
                 col if on else T.line, r=20, width=5 if on else 2)
            d.text((x + bw / 2, 310), t, font=F(34, True),
                   fill=T.fg if on else T.line, anchor="ma")
            d.text((x + bw / 2, 382), f2, font=F(46, True),
                   fill=col if on else T.line, anchor="ma")
            d.text((x + bw / 2, 470), sub, font=F(27),
                   fill=T.muted if on else T.line, anchor="ma")
            if i < 2:
                arrow(d, (x + bw + 20, 420), (x + bw + 110, 420),
                      T.a3 if i < stage - 1 else T.line, 6, 22)
        if stage >= 3:
            card(d, [130, 620, W - 130, 800], T.panel2, T.a2, r=20, width=4)
            txt(d, (170, 646), "FACHBEGRIFF", F(26, True), T.a2)
            txt(d, (170, 690), "Giftung  /  Bioaktivierung", F(46, True), T.fg)
            txt_block(d, 170, 752, "Erst der Stoffwechsel macht aus dem Pflanzenschutzmittel "
                      "das eigentliche Nervengift.", F(28), T.muted, 1500)
    return fn


def s4_bindung(stage):
    def fn(img, d):
        header(d, T, "Szene 4", "Bindung am aktiven Zentrum", 4, 7)
        # Enzymtasche
        d.rounded_rectangle([160, 250, 980, 740], radius=40, fill=T.panel,
                            outline=T.a1, width=4)
        d.text((190, 274), "Acetylcholinesterase", font=F(30, True), fill=T.a1)
        d.pieslice([360, 380, 780, 800], 180, 360, fill=T.bg2, outline=T.a1, width=4)
        d.text((570, 700), "aktives Zentrum", font=F(26), fill=T.muted, anchor="ma")
        serc = T.a2 if stage >= 1 else T.muted
        d.text((570, 470), "Serin – OH", font=F(38, True), fill=serc, anchor="ma")
        if stage >= 1:
            d.ellipse([470, 440, 670, 530], outline=T.a2, width=4)
        if stage >= 2:
            px, py = 1240, 450
            card(d, [1060, 330, W - 96, 600], T.panel, T.a2, r=20, width=4)
            d.text((1280, 356), "PARAOXON", font=F(34, True), fill=T.a2, anchor="ma")
            d.text((1280, 424), "P = O", font=F(52, True), fill=T.a2, anchor="ma")
            arrow(d, (1050, 480), (700, 480), T.a2, 7, 24)
            d.text((1280, 510), "phosphoryliert das Serin", font=F(26),
                   fill=T.muted, anchor="ma")
        if stage >= 3:
            card(d, [160, 780, 980, 872], T.panel2, T.a2, r=16, width=4)
            txt(d, (190, 798), "KOVALENTE BINDUNG – praktisch irreversibel",
                F(32, True), T.a2)
            txt(d, (190, 838), "im Gegensatz zu reversiblen Hemmern wie Neostigmin",
                F(24), T.muted)
    return fn


def s4_split(img, d):
    header(d, T, "Szene 4", "Normal vs. vergiftet", 4, 7)
    d.line([(W / 2, 200), (W / 2, 860)], fill=T.line, width=3)
    txt(d, (W / 4, 208), "NORMAL", F(32, True), T.a1, anchor="ma")
    txt(d, (W * 3 / 4, 208), "VERGIFTET", F(32, True), T.a2, anchor="ma")
    synapse(d, [96, 270, W / 2 - 40, 640], 5, scale=0.62, mini=True)
    synapse(d, [W / 2 + 40, 270, W - 96, 640], 3, poisoned=True, scale=0.62, mini=True)
    txt_block(d, 110, 680, "AChE spaltet ACh sofort. Der Spalt wird leer, das Signal endet "
              "sauber.", F(28), T.fg, 760)
    txt_block(d, W / 2 + 54, 680, "ACh wird nicht mehr abgebaut, staut sich im Spalt und "
              "erregt die Rezeptoren dauerhaft.", F(28), T.fg, 760)


def s4_block(stage):
    def fn(img, d):
        header(d, T, "Szene 4", "Vom Dauersignal zur Lähmung", 4, 7)
        steps = [("Dauererregung", "ACh bleibt am Rezeptor", T.a2),
                 ("Desensibilisierung", "Rezeptoren sprechen nicht mehr an", T.a2),
                 ("Depolarisationsblock", "Membran bleibt depolarisiert", T.a3),
                 ("LÄHMUNG statt Erregung", "zu viel Signal = kein Signal", T.a2)]
        y = 230
        for i, (t, s, col) in enumerate(steps):
            on = i < stage
            card(d, [200, y, W - 200, y + 120], T.panel if on else T.panel2,
                 col if on else T.line, r=18, width=5 if on else 2)
            d.text((250, y + 26), t, font=F(40, True), fill=T.fg if on else T.line)
            d.text((250, y + 76), s, font=F(26), fill=T.muted if on else T.line)
            if i < 3:
                arrow(d, (W / 2, y + 124), (W / 2, y + 152),
                      col if i < stage - 1 else T.line, 5, 16)
            y += 156
    return fn


def s4_aging(img, d):
    header(d, T, "Szene 4", "Aging: der Punkt ohne Rückkehr", 4, 7)
    cx, cy, r = 480, 500, 190
    dot(d, (cx, cy), r, T.panel, T.a3, 6)
    for i in range(12):
        a = math.radians(i * 30 - 90)
        d.line([(cx + (r - 26) * math.cos(a), cy + (r - 26) * math.sin(a)),
                (cx + (r - 8) * math.cos(a), cy + (r - 8) * math.sin(a))],
               fill=T.muted, width=4)
    d.line([(cx, cy), (cx + 90, cy - 70)], fill=T.a3, width=9)
    d.line([(cx, cy), (cx - 40, cy + 120)], fill=T.a2, width=7)
    dot(d, (cx, cy), 14, T.a3)
    d.text((cx, cy + r + 34), "Stunden nach der Vergiftung", font=F(28), fill=T.muted,
           anchor="ma")
    card(d, [800, 280, W - 96, 720], T.panel, T.a2, r=22, width=5)
    txt(d, (840, 310), "AGING", F(52, True), T.a2)
    txt_block(d, 840, 390, "Vom Phosphor-Rest am Enzym spaltet sich eine Alkylgruppe ab.",
              F(34, True), T.fg, 940)
    txt_block(d, 840, 490, "Die Bindung wird dadurch endgültig stabil.", F(34, True), T.fg, 940)
    d.line([(840, 570), (W - 140, 570)], fill=T.line, width=2)
    txt_block(d, 840, 600, "Danach ist das Enzym nicht mehr zu retten – auch ein "
              "Reaktivator hilft dann nicht mehr.", F(32, True), T.a2, 940)


add("Jetzt der Kern. Und hier kommt der entscheidende Punkt: E 605 selbst ist kaum aktiv.",
    s4_giftung(1))
add("Erst in der Leber wandeln Cytochrom-P450-Enzyme das Thion, also P gleich S, in das Oxon "
    "um: Paraoxon, P gleich O. Erst Paraoxon ist der eigentliche Hemmstoff.", s4_giftung(3))
add("Der Fachbegriff dafür ist Bioaktivierung oder Giftung: Erst der Stoffwechsel macht aus "
    "dem Pflanzenschutzmittel das Nervengift.", s4_giftung(3))
add("Paraoxon phosphoryliert dann den Serin-Rest im aktiven Zentrum der "
    "Acetylcholinesterase.", s4_bindung(2))
add("Das ist eine kovalente Bindung, praktisch irreversibel – im Gegensatz zu "
    "reversiblen Hemmern wie Neostigmin. Das Enzym ist blockiert.", s4_bindung(3))
add("Die Folge siehst du im Vergleich: Acetylcholin wird nicht mehr abgebaut, es reichert "
    "sich im Spalt an, die Rezeptoren werden dauererregt.", s4_split)
add("Und jetzt kommt das Paradoxe. Die Rezeptoren desensibilisieren, die Membran bleibt "
    "depolarisiert. Das nennt man Depolarisationsblock.", s4_block(3))
add("Das Ergebnis ist Lähmung statt Erregung: Zu viel Signal führt am Ende zu gar keinem "
    "Signal mehr.", s4_block(4))
add("Nach Stunden spaltet sich zusätzlich eine Alkylgruppe vom Phosphor-Rest ab. Dieses "
    "Aging macht die Bindung endgültig stabil – danach ist das Enzym nicht mehr zu "
    "retten.", s4_aging)

# ================================================================ Szene 5
def s5(stage):
    def fn(img, d):
        header(d, T, "Szene 5", "Wirkung am Menschen", 5, 7)
        # Silhouette
        cx = W / 2
        d.ellipse([cx - 56, 226, cx + 56, 338], fill=T.panel2, outline=T.line, width=3)
        d.rounded_rectangle([cx - 110, 348, cx + 110, 650], radius=40, fill=T.panel2,
                            outline=T.line, width=3)
        d.line([(cx - 110, 400), (cx - 190, 560)], fill=T.line, width=16)
        d.line([(cx + 110, 400), (cx + 190, 560)], fill=T.line, width=16)
        d.line([(cx - 50, 650), (cx - 70, 820)], fill=T.line, width=18)
        d.line([(cx + 50, 650), (cx + 70, 820)], fill=T.line, width=18)
        lung = T.a2 if stage >= 4 else T.line
        d.rounded_rectangle([cx - 86, 390, cx - 10, 500], radius=22, fill=T.panel,
                            outline=lung, width=4)
        d.rounded_rectangle([cx + 10, 390, cx + 86, 500], radius=22, fill=T.panel,
                            outline=lung, width=4)
        # Spalten
        musc = ["Miosis (enge Pupillen)", "Tränen- und Speichelfluss",
                "Bronchokonstriktion + Schleim", "Bradykardie", "Erbrechen, Durchfall",
                "Harndrang"]
        nic = ["Faszikulationen (Muskelzucken)", "zunehmende Schwäche",
               "schlaffe Lähmung"]
        zns = ["Unruhe, Verwirrung", "Krampfanfälle", "Hemmung des Atemzentrums"]
        if stage >= 1:
            card(d, [96, 212, 712, 648], T.panel, T.a1, r=18, width=4)
            txt(d, (126, 230), "MUSCARINISCH – innere Organe", F(25, True), T.a1)
            y = 268
            for s in musc:
                dot(d, (136, y + 12), 7, T.a1)
                d.text((156, y), s, font=F(26), fill=T.fg); y += 40
            d.rounded_rectangle([126, 516, 682, 622], radius=14, fill=T.a1)
            d.text((146, 526), "SLUDGE", font=F(28, True), fill=T.bg1)
            txt_block(d, 146, 564, "Salivation \u00b7 Lacrimation \u00b7 Urination \u00b7 Defecation \u00b7 GI distress \u00b7 Emesis", F(21, True), T.bg1, 520, lh=26)
        if stage >= 2:
            card(d, [1260, 212, W - 96, 412], T.panel, T.a2, r=18, width=4)
            txt(d, (1290, 230), "NICOTINISCH – Skelettmuskel", F(25, True), T.a2)
            y = 272
            for s in nic:
                dot(d, (1300, y + 12), 7, T.a2)
                d.text((1320, y), s, font=F(27), fill=T.fg); y += 44
        if stage >= 3:
            card(d, [1260, 440, W - 96, 640], T.panel, T.a3, r=18, width=4)
            txt(d, (1290, 458), "ZENTRAL – ZNS", F(25, True), T.a3)
            y = 500
            for s in zns:
                dot(d, (1300, y + 12), 7, T.a3)
                d.text((1320, y), s, font=F(27), fill=T.fg); y += 44
        if stage >= 4:
            arrow(d, (670, 480), (cx - 96, 452), T.a1, 6, 20)
            arrow(d, (1250, 380), (cx + 96, 430), T.a2, 6, 20)
            arrow(d, (1250, 530), (cx + 96, 470), T.a3, 6, 20)
            card(d, [96, 700, 1180, 858], T.panel2, T.a2, r=18, width=5)
            txt(d, (130, 718), "TODESURSACHE: ATEMVERSAGEN", F(38, True), T.a2)
            txt_block(d, 130, 772, "gelähmte Atemmuskulatur  +  verengte und verschleimte "
                      "Atemwege  +  ausgefallenes Atemzentrum", F(28, True), T.fg, 1020)
    return fn


add("Was macht das im Menschen? Weil Acetylcholin an zwei Rezeptortypen wirkt, gibt es zwei "
    "Symptomgruppen plus das Zentralnervensystem. Muscarinisch, also der Parasympathikus im "
    "Overdrive: enge Pupillen, Tränen- und Speichelfluss, verengte Bronchien mit massiver "
    "Schleimproduktion, langsamer Puls, Erbrechen, Durchfall, Harndrang.", s5(1))
add("Die Merkhilfe aus der Notfallmedizin dafür heißt SLUDGE: Salivation, Lacrimation, "
    "Urination, Defecation, Gastrointestinal distress, Emesis.", s5(1))
add("Nicotinisch, an der Skelettmuskulatur: erst Faszikulationen, also Muskelzucken, dann "
    "Schwäche, dann schlaffe Lähmung.", s5(2))
add("Und zentral: Unruhe, Verwirrung, Krampfanfälle und die Hemmung des Atemzentrums.", s5(3))
add("Gestorben wird am Atemversagen – durch die Dreifachkombination aus gelähmter "
    "Atemmuskulatur, verengten und verschleimten Atemwegen und ausgefallenem Atemzentrum.",
    s5(4))

# ================================================================ Szene 6
def s6(stage):
    def fn(img, d):
        header(d, T, "Szene 6", "Gegengift – zweigleisig", 6, 7)
        card(d, [96, 212, 940, 620], T.panel if stage >= 1 else T.panel2,
             T.a1 if stage >= 1 else T.line, r=22, width=5 if stage >= 1 else 2)
        txt(d, (130, 234), "SYMPTOMATISCH", F(26, True), T.a1)
        txt(d, (130, 278), "ATROPIN", F(52, True), T.fg)
        txt_block(d, 130, 350, "kompetitiver Antagonist an muscarinischen Rezeptoren – "
                  "besetzt den Rezeptor, ACh kann nicht mehr andocken",
                  F(28), T.fg if stage >= 1 else T.line, 760)
        txt_block(d, 130, 440, "✓ trocknet die Bronchien, hebt den Puls",
                  F(28, True), T.a1 if stage >= 1 else T.line, 760)
        txt_block(d, 130, 490, "✗ wirkt NICHT nicotinisch – die Muskellähmung "
                  "bleibt", F(28, True), T.a2 if stage >= 1 else T.line, 760)
        card(d, [980, 212, W - 96, 620], T.panel if stage >= 2 else T.panel2,
             T.a3 if stage >= 2 else T.line, r=22, width=5 if stage >= 2 else 2)
        txt(d, (1014, 234), "KAUSAL", F(26, True), T.a3)
        txt(d, (1014, 278), "OBIDOXIM / PRALIDOXIM", F(42, True),
            T.fg if stage >= 2 else T.line)
        txt_block(d, 1014, 350, "Reaktivator: löst den Phosphat-Rest von der AChE ab und "
                  "stellt das Enzym wieder her", F(28), T.fg if stage >= 2 else T.line, 760)
        txt_block(d, 1014, 440, "✓ echte kausale Therapie",
                  F(28, True), T.a3 if stage >= 2 else T.line, 760)
        txt_block(d, 1014, 490, "✗ nur VOR dem Aging wirksam – Zeitfenster!",
                  F(28, True), T.a2 if stage >= 2 else T.line, 760)
        if stage >= 3:
            card(d, [96, 650, 940, 790], T.panel2, T.a1, r=18, width=3)
            txt(d, (130, 668), "BEGLEITTHERAPIE", F(24, True), T.a1)
            txt_block(d, 130, 708, "Benzodiazepine gegen Krämpfe  ·  Beatmung  ·  "
                      "Dekontamination (Kleidung entfernen, Haut waschen)",
                      F(27, True), T.fg, 780)
        if stage >= 4:
            card(d, [980, 650, W - 96, 820], T.panel2, T.a2, r=18, width=4)
            txt(d, (1014, 668), "EHRLICH DAZUSAGEN", F(24, True), T.a2)
            txt_block(d, 1014, 708, "Der klinische Nutzen der Oxime beim Menschen ist bis "
                      "heute umstritten (Cochrane-Review 2011: kein klarer Wirksamkeits"
                      "nachweis). Tragende Säulen sind Atropin und Beatmung.",
                      F(25), T.fg, 780)
    return fn


add("Gibt es ein Gegengift? Ja, aber zweigleisig. Atropin ist ein kompetitiver Antagonist an "
    "den muscarinischen Rezeptoren: Es besetzt den Rezeptor, sodass Acetylcholin nicht mehr "
    "andocken kann. Es trocknet die Bronchien und hebt den Puls – wirkt aber nur "
    "symptomatisch und nicht an den nicotinischen Rezeptoren. Die Muskellähmung bleibt.",
    s6(1))
add("Der zweite Weg ist Obidoxim, beziehungsweise Pralidoxim. Dieser Reaktivator löst den "
    "Phosphat-Rest von der Acetylcholinesterase ab und stellt das Enzym wieder her. Das ist "
    "eine echte kausale Therapie – aber nur vor dem Aging.", s6(2))
add("Dazu kommen Benzodiazepine gegen die Krämpfe, Beatmung und die Dekontamination: Kleidung "
    "entfernen, Haut waschen.", s6(3))
add("Und ein ehrlicher Zusatz, mit dem du bei einem Arzt punktest: Der klinische Nutzen der "
    "Oxime beim Menschen ist bis heute fachlich umstritten. Ein Cochrane-Review von 2011 kam "
    "zu keinem klaren Wirksamkeitsnachweis. Als tragende Säulen gelten Atropin und Beatmung.",
    s6(4))

# ================================================================ Szene 7
def s7(img, d):
    header(d, T, "Szene 7", "Die Verbindung zu den Nervenkampfstoffen", 7, 7)
    boxes = [("Gerhard Schrader", "derselbe Chemiker, dieselbe Forschungslinie", T.muted),
             ("E 605 / Parathion", "Insektizid – 1944", T.a1),
             ("Tabun", "Nervenkampfstoff – gleiches Prinzip,\nein Vielfaches potenter",
              T.a2)]
    x = 130
    for i, (t, s, col) in enumerate(boxes):
        card(d, [x, 280, x + 480, 560], T.panel, col, r=20, width=5)
        d.text((x + 240, 316), t, font=F(36, True), fill=T.fg, anchor="ma")
        txt_block(d, x + 30, 392, s.replace("\n", " "), F(26), T.muted, 420)
        if i < 2:
            arrow(d, (x + 500, 420), (x + 590, 420), T.a3, 6, 22)
        x += 610
    card(d, [130, 620, W - 130, 800], T.panel2, T.a3, r=20, width=4)
    txt_block(d, 170, 652, "Nervenkampfstoffe hemmen dieselbe Acetylcholinesterase – "
              "nur schneller, stärker und mit noch kürzerem Zeitfenster bis zum Aging.",
              F(32, True), T.fg, 1500)


def s7_end(img, d):
    big_statement(img, d, T, "Ein einziges Enzym – die Acetylcholinesterase – "
                  "entscheidet über Leben und Tod.", T.a2)


add("Zum Schluss die Verbindung, die das Thema groß macht: Derselbe Chemiker, Gerhard "
    "Schrader, entwickelte in derselben Forschungslinie auch Tabun. Nervenkampfstoffe wirken "
    "nach genau demselben Prinzip, nur um ein Vielfaches potenter.", s7)
add("Ein einziges Enzym, die Acetylcholinesterase, entscheidet über Leben und Tod.", s7_end)
