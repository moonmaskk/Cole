# -*- coding: utf-8 -*-
"""Video 2 - Deutsch: Anglizismen, das idiotensichere System."""
from vlib import *

TH = LIGHT
T = TH
SHOTS = []


def shot(text):
    def deco(fn):
        SHOTS.append((text, fn))
        return fn
    return deco


def add(text, fn):
    SHOTS.append((text, fn))


# ---------------------------------------------------------------- Titel
def s_title(img, d):
    title_card(img, d, T, "Deutsch - Prüfungsvortrag", "Anglizismen",
               "Das idiotensichere System für Text + 3 Aufgaben",
               "30 Min Vorbereitung  -  10 Min Vortrag  -  3 Nachfragen")


add("Anglizismen. Hier kommt das komplette System: 30 Minuten Vorbereitung, "
    "zehn Minuten Vortrag an der Tafel, danach drei Nachfragen.", s_title)
add("Du bekommst einen unbekannten Text und etwa drei Aufgaben. Das Entscheidende: "
    "Du hältst keinen Aufgaben-Abarbeitungs-Vortrag, sondern baust einen roten Faden.", s_title)

# ---------------------------------------------------------------- Teil A
STATIONS = [
    ("E", "EINSTIEG", "Hook + Leitfrage + Mini-Gliederung"),
    ("T", "TEXT", "Wer sagt was? Kurz, im Konjunktiv I"),
    ("A", "ANALYSE", "Sprache, Argumenttypen, Mittel, Anglizismen im Text"),
    ("K", "KONTEXT", "Fachwissen: Typen, Ursachen, Funktionen, Zahlen"),
    ("U", "URTEIL", "mit K-F-Z"),
    ("F", "FAZIT", "zurück zur Leitfrage"),
]


def part_a(stage, leit=False):
    def fn(img, d):
        header(d, T, "Teil A", "Die Goldene Formel", 1, 8)
        if leit:
            card(d, [96, 210, W - 96, 420], T.panel, T.a1, r=22, width=4)
            txt(d, (140, 238), "SCHRITT 0 - LEITFRAGE BILDEN", F(28, True), T.a1)
            txt_block(d, 140, 282, "Aus: „Erörtern Sie, ob Anglizismen eine Bedrohung "
                      "darstellen“  →  wird:", F(30), T.muted, 1560)
            txt_block(d, 140, 330, "„Sind Anglizismen eine Bedrohung oder normaler "
                      "Sprachwandel? Dieser Frage gehe ich heute nach.“",
                      F(34, True), T.fg, 1560)
            return
        txt(d, (96, 206), "MERKSPRUCH", F(26, True), T.a1)
        txt(d, (96, 244), "„Ein Toller Auftritt Kriegt Unbedingt Fünfzehn“",
            F(46, True), T.fg)
        bw, bh, gap = 536, 196, 32
        for i, (L, name, sub) in enumerate(STATIONS):
            col, row = i % 3, i // 3
            x = 96 + col * (bw + gap)
            y = 340 + row * (bh + gap)
            on = i < stage
            card(d, [x, y, x + bw, y + bh], T.panel if on else T.panel2,
                 T.a1 if on else T.line, r=18, width=4 if on else 2)
            bc = T.a1 if on else T.line
            d.rounded_rectangle([x + 22, y + 22, x + 94, y + 94], radius=14, fill=bc)
            d.text((x + 58, y + 58), L, font=F(44, True),
                   fill=T.panel if on else T.muted, anchor="mm")
            d.text((x + 112, y + 30), name, font=F(32, True),
                   fill=T.fg if on else T.muted)
            txt_block(d, x + 112, y + 74, sub, F(23), T.muted if on else T.line, bw - 140)
    return fn


add("Zuerst Schritt 0, und der ist der wichtigste: Aus der schwersten Aufgabe, meistens "
    "Aufgabe drei, formst du eine Leitfrage.", part_a(0, True))
add("Aus „Erörtern Sie, ob Anglizismen eine Bedrohung darstellen“ wird: Sind "
    "Anglizismen eine Bedrohung oder normaler Sprachwandel? Dieser Frage gehe ich heute nach.",
    part_a(0, True))
add("Danach läufst du sechs Stationen ab. Merkspruch: Ein Toller Auftritt Kriegt "
    "Unbedingt Fünfzehn.", part_a(0))
add("E wie Einstieg: Hook, Leitfrage, Mini-Gliederung. Drei Sätze, nicht mehr.", part_a(1))
add("T wie Text: Wer sagt was? Kurze Wiedergabe im Konjunktiv eins.", part_a(2))
add("A wie Analyse: Sprache, Argumenttypen, rhetorische Mittel. Und ganz wichtig: Welche "
    "Anglizismen kommen im Text selbst vor?", part_a(3))
add("K wie Kontext: Hier kommt dein Fachwissen rein. Typen, Ursachen, Funktionen, Zahlen.",
    part_a(4))
add("U wie Urteil, immer mit K-F-Z. Und F wie Fazit: zurück zur Leitfrage.", part_a(6))
add("Die Aufgaben verteilst du einfach auf diese Stationen. Sag niemals „Aufgabe eins, "
    "Aufgabe zwei“, sondern führe durch einen Gedankengang.", part_a(6))

# ---------------------------------------------------------------- Teil B
PLAN = [
    ("0-3", "Aufgaben lesen, Operatoren einkreisen, schwerste Aufgabe finden → LEITFRAGE"),
    ("3-10", "Text 1x ganz lesen, dann 2. Durchgang markieren: These, Argumente, "
             "Anglizismen (+ Typ), rhetorische Mittel, unbelegte Behauptungen"),
    ("10-14", "WWTZT-Steckbrief: Wer schreibt? Wann/Wo? Textsorte? Zielgruppe? These?"),
    ("14-22", "Stichpunkte auf die 6 Stationen verteilen, Zeilenangaben dazuschreiben"),
    ("22-26", "Tafelbild skizzieren (nur Gerüst) + Einstieg und Fazit WÖRTLICH"),
    ("26-30", "Einmal leise im Kopf durchgehen, Timing checken"),
]


def part_b(stage, scale=False):
    def fn(img, d):
        header(d, T, "Teil B", "Minutenplan: 30 Minuten Vorbereitung", 2, 8)
        d.line([(268, 230), (268, 820)], fill=T.line, width=4)
        y = 222
        for i, (t, s) in enumerate(PLAN):
            on = i < stage
            col = T.a1 if on else T.line
            dot(d, (268, y + 26), 17, col)
            d.text((268, y + 26), str(i + 1), font=F(22, True),
                   fill=T.panel if on else T.muted, anchor="mm")
            d.text((232, y + 10), f"Min {t}", font=F(27, True),
                   fill=T.fg if on else T.line, anchor="ra")
            if on:
                card(d, [304, y - 6, W - 96, y + 92], T.panel, T.a1, r=14, width=3)
            txt_block(d, 332, y + 12, s, F(29, True) if on else F(29),
                      T.fg if on else T.line, 1240)
            y += 100
        if scale:
            card(d, [304, 822, W - 96, 876], T.panel2, T.a3, r=12, width=3)
            txt(d, (332, 834), "Skalierung:  15 Min → alles halbieren   |   "
                "22,5 Min → Faktor 0,75", F(28, True), T.fg)
    return fn


add("Teil B, der Minutenplan. Minute null bis drei: Aufgaben lesen, Operatoren einkreisen, "
    "Leitfrage formulieren.", part_b(1))
add("Minute drei bis zehn: Text einmal ganz lesen. Im zweiten Durchgang markieren: These, "
    "Argumente, Anglizismen mit Typ dazugeschrieben, rhetorische Mittel, unbelegte "
    "Behauptungen.", part_b(2))
add("Minute zehn bis vierzehn: der Steckbrief. Wer schreibt? Wann und wo? Welche Textsorte? "
    "Welche Zielgruppe? Welche These?", part_b(3))
add("Minute vierzehn bis zweiundzwanzig: Stichpunkte auf die sechs Stationen verteilen, "
    "immer mit Zeilenangabe.", part_b(4))
add("Minute zweiundzwanzig bis sechsundzwanzig: Tafelbild skizzieren, nur das Gerüst. "
    "Einstiegssatz und Fazit formulierst du wörtlich aus.", part_b(5))
add("Die letzten vier Minuten gehst du alles leise im Kopf durch und checkst das Timing. "
    "Bei fünfzehn Minuten halbierst du einfach alles.", part_b(6, True))

# ---------------------------------------------------------------- Teil C
def part_c(stage):
    def fn(img, d):
        header(d, T, "Teil C", "Die drei Werkzeuge", 3, 8)
        boxes = [
            ("ZBB", "Material einbauen", T.a1,
             ["ZEILE – BEGRIFF – BEDEUTUNG",
              "„In Zeile X spricht der Autor von [Begriff].",
              "Damit meint er [Bedeutung].",
              "Fachlich ist das ein [Einordnung].“",
              "→ fremdes Material wird eigene Argumentation"]),
            ("KFZ", "für jedes Werturteil", T.a2,
             ["KONTEXT – FUNKTION – ZIELGRUPPE",
              "„Update“ in der Handy-Anleitung: angemessen",
              "„Service Point“ am Behördenschild: unangemessen",
              "„cringe“ im Gruppenchat: passt",
              "→ nicht OB, sondern WANN"]),
            ("K I", "Textwiedergabe", T.a3,
             ["Konjunktiv I statt Indikativ",
              "falsch: „der Autor sagt, sie sind ...“",
              "richtig: „er sei der Ansicht, sie SEIEN ...“",
              "ist→sei  hat→habe  kann→könne",
              "muss→müsse  gibt→gebe  wird→werde"]),
        ]
        bw, gap = 536, 32
        for i, (tag, sub, col, lines) in enumerate(boxes):
            x = 96 + i * (bw + gap)
            on = i < stage
            card(d, [x, 214, x + bw, 806], T.panel if on else T.panel2,
                 col if on else T.line, r=20, width=5 if on else 2)
            d.rounded_rectangle([x, 214, x + bw, 300], radius=20,
                                fill=col if on else T.line)
            d.rectangle([x, 276, x + bw, 300], fill=col if on else T.line)
            d.text((x + 34, 234), tag, font=F(46, True),
                   fill=T.panel if on else T.muted)
            d.text((x + bw - 34, 248), sub, font=F(24, True),
                   fill=T.panel if on else T.muted, anchor="ra")
            y = 330
            for j, ln in enumerate(lines):
                f = F(28, True) if j == 0 else F(26)
                c = (col if on else T.line) if j == 0 else (T.fg if on else T.line)
                if ln.startswith("→"):
                    c = col if on else T.line
                    f = F(27, True)
                y = txt_block(d, x + 30, y, ln, f, c, bw - 60) + 16
        if stage >= 4:
            card(d, [96, 824, W - 96, 876], T.panel2, T.a3, r=12, width=3)
            txt(d, (W / 2, 836), "Klingt der Konjunktiv I wie der Indikativ? "
                "→ hätte / würde nehmen", F(28, True), T.fg, anchor="ma")
    return fn


add("Teil C, die drei Werkzeuge. Erstes Werkzeug, Z-B-B: Zeile, Begriff, Bedeutung.",
    part_c(1))
add("Du sagst: In Zeile X spricht der Autor von diesem Begriff, damit meint er das, "
    "fachlich ist das ein Pseudoanglizismus. So wird fremdes Material zu deiner eigenen "
    "Argumentation.", part_c(1))
add("Zweites Werkzeug, K-F-Z, für jedes Werturteil: Kontext, Funktion, Zielgruppe.",
    part_c(2))
add("„Update“ in einer Handy-Anleitung ist angemessen. „Service Point“ auf "
    "einem Behördenschild eher nicht. „cringe“ im Gruppenchat passt. Die Frage ist "
    "also nie OB Anglizismen angemessen sind, sondern WANN.", part_c(2))
add("Drittes Werkzeug: Konjunktiv eins für die Textwiedergabe. Nicht „der Autor sagt, "
    "Anglizismen sind überflüssig“, sondern „er sei der Ansicht, sie seien "
    "überflüssig“.", part_c(3))
add("Ist, sei. Hat, habe. Kann, könne. Muss, müsse. Gibt, gebe. Wird, werde. Und wenn es "
    "genauso klingt wie der Indikativ, nimm hätte oder würde.", part_c(4))

# ---------------------------------------------------------------- Teil D
TYPEN = [
    ("1", "Direkte Entlehnung", "Meeting, Feedback", "engl. Wort, fast unverändert"),
    ("2", "Lehnübersetzung", "herunterladen ← download", "Teil für Teil übersetzt"),
    ("3", "Lehnbedeutung", "realisieren = „bemerken“", "dt. Wort, engl. Bedeutung dazu"),
    ("4", "Pseudoanglizismus", "Handy, Homeoffice, Beamer", "klingt engl., gibt es so nicht"),
    ("5", "Hybridbildung", "Handyvertrag, Eventkultur", "englisch + deutsch gemischt"),
]


def d_begriff(img, d):
    header(d, T, "Teil D", "Fachwissen Anglizismen", 4, 8)
    card(d, [96, 240, W - 96, 470], T.panel, T.a1, r=22, width=4)
    txt(d, (140, 272), "DEFINITION", F(28, True), T.a1)
    txt_block(d, 140, 318, "Ein Anglizismus ist ein Wort oder eine Struktur, die aus dem "
              "Englischen übernommen wurde.", F(40, True), T.fg, 1560)
    card(d, [96, 520, W - 96, 700], T.panel2, T.a2, r=22, width=4)
    txt(d, (140, 548), "WICHTIG", F(28, True), T.a2)
    txt_block(d, 140, 592, "Anglizismen gehören danach ZUR deutschen Sprache – nicht "
              "mehr zum Englischen.", F(38, True), T.fg, 1560)


def d_typen(stage):
    def fn(img, d):
        header(d, T, "Teil D", "Die 5 Typen", 4, 8)
        y = 212
        for i, (n, name, bsp, erkl) in enumerate(TYPEN):
            on = i < stage
            card(d, [96, y, W - 96, y + 112], T.panel if on else T.panel2,
                 T.a1 if on else T.line, r=16, width=4 if on else 2)
            bc = T.a1 if on else T.line
            d.rounded_rectangle([118, y + 22, 186, y + 90], radius=12, fill=bc)
            d.text((152, y + 56), n, font=F(38, True),
                   fill=T.panel if on else T.muted, anchor="mm")
            d.text((210, y + 22), name, font=F(34, True), fill=T.fg if on else T.line)
            d.text((210, y + 68), erkl, font=F(24), fill=T.muted if on else T.line)
            if on:
                pill(d, (W - 130, y + 32), bsp, F(30, True), T.panel, T.a2, anchor="rt")
            y += 126
    return fn


def d_integration(img, d):
    header(d, T, "Teil D", "Integration in die Grammatik", 4, 8)
    card(d, [96, 230, W - 96, 560], T.panel, T.a1, r=22, width=4)
    txt(d, (140, 262), "DIE DEUTSCHE GRAMMATIK NIMMT DAS WORT AUF", F(28, True), T.a1)
    txt(d, (140, 320), "das Meeting", F(54, True), T.fg)
    txt(d, (520, 336), "→ Artikel + Großschreibung", F(30), T.muted)
    txt(d, (140, 410), "ich habe gedownloadet / downgeloadet", F(46, True), T.fg)
    txt(d, (140, 480), "→ das Schwanken zeigt: Das Wort ist im Deutschen angekommen.",
        F(30, True), T.a2)
    card(d, [96, 600, W - 96, 806], T.panel2, T.a3, r=22, width=3)
    txt(d, (140, 626), "URSACHEN", F(28, True), T.a3)
    chip_row(d, 140, 672, [("USA als Leitkultur nach 1945", T.a3), ("Technik & Internet", T.a3),
                           ("Globalisierung & Wirtschaft", T.a3)], 3, T, 26)
    chip_row(d, 140, 736, [("Popkultur & Social Media", T.a3), ("Prestige", T.a3)], 2, T, 26)


def d_zahlen(stage):
    def fn(img, d):
        header(d, T, "Teil D", "Zahlen & Studien", 4, 8)
        # 40/40/20
        card(d, [96, 206, 760, 560], T.panel, T.a1, r=20, width=4)
        txt(d, (126, 230), "MERKZAHL  40 / 40 / 20", F(30, True), T.a1)
        txt_block(d, 126, 272, "Kommunikativ relevante Neuwörter der 1990er",
                  F(23), T.muted, 600)
        bars = [("Anglizismen", 40, T.a1), ("deutsche Bildungen", 40, T.a2),
                ("Hybridbildungen", 20, T.a3)]
        y = 334
        for i, (lab, v, col) in enumerate(bars):
            on = stage >= 1
            d.rounded_rectangle([126, y, 126 + 440, y + 44], radius=10, fill=T.panel2)
            if on:
                d.rounded_rectangle([126, y, 126 + 440 * v / 40.0 * 0.999, y + 44],
                                    radius=10, fill=col)
            d.text((136, y + 8), lab, font=F(24, True), fill=T.panel if on else T.muted)
            d.text((600, y + 8), f"{v} %", font=F(30, True), fill=T.fg)
            y += 62
        txt(d, (126, 524), "Herberg, IDS Mannheim 2001", F(22, True), T.muted)
        studies = [
            ("Eisenberg 2013", "„Anglizismen im Deutschen“, Erster Bericht zur Lage "
             "der deutschen Sprache (DASD): Entwarnung – Wortschatz wächst, "
             "Grammatik bleibt deutsch."),
            ("ca. 10 %", "Anteil des Englischen am dt. Fremdwortschatz (nach Kluge, "
             "Etymologisches Wörterbuch) – Latein und Französisch liegen davor."),
            ("IDS-Erhebung 2022", "Adler/Rössel, 1.042 Befragte: meiste Nennungen zu "
             "Sprachwandel = Einfluss anderer Sprachen, vor allem Englisch. "
             "Merken heißt nicht ablehnen."),
            ("Zifonun 2021", "„Anglizismen in der Coronakrise“ (IDS Sprachreport): "
             "Lockdown, Social Distancing – aber auch Holistay, Mask-have. "
             "Sprecher spielen mit dem Material."),
        ]
        y = 206
        for i, (tag, body) in enumerate(studies):
            on = i < stage
            card(d, [800, y, W - 96, y + 148], T.panel if on else T.panel2,
                 T.a2 if on else T.line, r=16, width=4 if on else 2)
            d.text((830, y + 18), tag, font=F(30, True), fill=T.a2 if on else T.line)
            txt_block(d, 830, y + 62, body, F(23), T.fg if on else T.line, 950)
            y += 162
    return fn


def d_funktionen(stage):
    def fn(img, d):
        header(d, T, "Teil D", "Funktionen von Anglizismen", 4, 8)
        rows = [("Lücke füllen", "Software", T.a1),
                ("Sprachökonomie / Kürze", "Job statt Arbeitsstelle", T.a1),
                ("Prestige / Modernität", "Coffee to go", T.a2),
                ("Euphemismus", "Facility Manager statt Hausmeister", T.a2),
                ("Gruppenidentität / Jugendsprache", "cringe", T.a3)]
        y = 230
        for i, (f_, b, col) in enumerate(rows):
            on = i < stage
            card(d, [96, y, W - 96, y + 104], T.panel if on else T.panel2,
                 col if on else T.line, r=16, width=4 if on else 2)
            d.rectangle([96, y + 16, 106, y + 88], fill=col if on else T.line)
            d.text((150, y + 30), f_, font=F(36, True), fill=T.fg if on else T.line)
            if on:
                pill(d, (W - 130, y + 26), b, F(30, True), T.panel, col, anchor="rt")
            y += 120
    return fn


def d_bewertung(stage):
    def fn(img, d):
        header(d, T, "Teil D", "Bewertung: deskriptiv vs. präskriptiv", 4, 8)
        card(d, [96, 206, 950, 470], T.panel, T.a1, r=20, width=4)
        txt(d, (126, 230), "DESKRIPTIV", F(34, True), T.a1)
        txt_block(d, 126, 282, "beschreibt, wie Sprache IST – so arbeitet die "
                  "Sprachwissenschaft", F(30), T.fg, 790)
        txt_block(d, 126, 376, "Historisch nichts Neues: Trottoir, Portemonnaie, "
                  "Fenster (lat. fenestra)", F(25), T.muted, 790)
        card(d, [970, 206, W - 96, 470], T.panel2 if stage < 2 else T.panel,
             T.a2 if stage >= 2 else T.line, r=20, width=4 if stage >= 2 else 2)
        txt(d, (1000, 230), "PRÄSKRIPTIV", F(34, True), T.a2 if stage >= 2 else T.line)
        txt_block(d, 1000, 282, "schreibt vor, wie Sprache sein SOLL",
                  F(30), T.fg if stage >= 2 else T.line, 790)
        txt_block(d, 1000, 348, "Verein Deutsche Sprache (1997, Walter Krämer): Kritik an "
                  "„Denglisch“, Anglizismen-Index mit Eindeutschungsvorschlägen",
                  F(25), T.muted if stage >= 2 else T.line, 800)
        if stage >= 3:
            card(d, [96, 500, 950, 680], T.panel, T.a3, r=20, width=4)
            txt(d, (126, 522), "ERNST NEHMEN", F(28, True), T.a3)
            txt(d, (126, 566), "VERSTÄNDLICHKEIT", F(32, True), T.fg)
            txt(d, (126, 606), "Aeltere, Behördenschilder", F(24), T.muted)
            txt(d, (560, 566), "DOMÄNENVERLUST", F(32, True), T.fg)
            txt(d, (560, 606), "wenn z.B. Wissenschaft nur", F(24), T.muted)
            txt(d, (560, 634), "noch auf Englisch läuft", F(24), T.muted)
        if stage >= 4:
            card(d, [970, 500, W - 96, 680], T.panel, T.a2, r=20, width=4)
            txt(d, (1000, 522), "VERGLEICH FRANKREICH", F(28, True), T.a2)
            txt(d, (1000, 566), "Loi Toubon, 4. August 1994", F(32, True), T.fg)
            txt_block(d, 1000, 610, "Französisch vorgeschrieben in amtlichen "
                      "Veröffentlichungen, Werbung, am Arbeitsplatz", F(24), T.muted, 800)
    return fn


add("Teil D, das Fachwissen. Ein Anglizismus ist ein Wort oder eine Struktur, die aus dem "
    "Englischen übernommen wurde.", d_begriff)
add("Ganz wichtig für dein Urteil: Anglizismen gehören danach ZUR deutschen Sprache, "
    "nicht mehr zum Englischen.", d_begriff)
add("Es gibt fünf Typen. Erstens die direkte Entlehnung: Meeting, Feedback. Das englische "
    "Wort wandert fast unverändert ein.", d_typen(1))
add("Zweitens die Lehnübersetzung: herunterladen, aus download, Teil für Teil übersetzt.",
    d_typen(2))
add("Drittens die Lehnbedeutung: realisieren hieß im Deutschen verwirklichen und bekam die "
    "englische Bedeutung bemerken dazu.", d_typen(3))
add("Viertens der Pseudoanglizismus, dein Glanzpunkt im Vortrag: Handy, Homeoffice, Beamer "
    "klingen englisch, gibt es im Englischen aber so nicht.", d_typen(4))
add("Fünftens die Hybridbildung: Handyvertrag, Eventkultur. Englischer und deutscher "
    "Bestandteil gemischt.", d_typen(5))
add("Dann die Integration: das Meeting bekommt Artikel und Großschreibung, und wir streiten, "
    "ob es gedownloadet oder downgeloadet heißt. Genau dieses Schwanken zeigt, dass das Wort "
    "im Deutschen angekommen ist.", d_integration)
add("Ursachen: die USA als Leitkultur nach 1945, Technik und Internet, Globalisierung und "
    "Wirtschaft, Popkultur, Social Media und Prestige.", d_integration)
add("Jetzt die Zahlen, damit behaupten andere und du belegst. Merkzahl vierzig, vierzig, "
    "zwanzig: Bei den kommunikativ relevanten Neuwörtern der neunziger Jahre waren rund "
    "vierzig Prozent Anglizismen, vierzig Prozent deutsche Bildungen und zwanzig Prozent "
    "Hybridbildungen. Herberg, Institut für Deutsche Sprache, 2001.", d_zahlen(1))
add("Eisenberg, zweitausenddreizehn, im Ersten Bericht zur Lage der deutschen Sprache: "
    "Entwarnung. Der Wortschatz wächst, die Grammatik bleibt deutsch.", d_zahlen(2))
add("Englisch liegt beim deutschen Fremdwortschatz bei nur etwa zehn Prozent. Latein und "
    "Französisch liegen davor. Englisch ist also nicht die Hauptquelle.", d_zahlen(2))
add("Die Erhebung des Instituts für Deutsche Sprache von zweitausendzweiundzwanzig, "
    "eintausendzweiundvierzig Befragte: Die meisten Nennungen zum Sprachwandel betrafen den "
    "Einfluss anderer Sprachen, vor allem des Englischen. Die Leute merken den Wandel. "
    "Merken heißt aber nicht ablehnen.", d_zahlen(3))
add("Und Zifonun, zweitausendeinundzwanzig, zu den Anglizismen in der Coronakrise: In der "
    "Neologismen-Liste stehen Lockdown und Social Distancing, aber auch Sprachspiele wie "
    "Holistay und Mask-have. Deutsche Sprecher spielen mit dem Material, sie übernehmen "
    "es nicht passiv.", d_zahlen(4))
add("Funktionen, falls du Anglizismen im Text einordnen musst: Lücken füllen, wie Software. "
    "Sprachökonomie, Job statt Arbeitsstelle.", d_funktionen(2))
add("Prestige und Modernität, Coffee to go. Euphemismus, Facility Manager statt Hausmeister. "
    "Und Gruppenidentität in der Jugendsprache, cringe.", d_funktionen(5))
add("Für die Bewertung brauchst du ein Begriffspaar: Deskriptiv beschreibt, wie Sprache ist, "
    "so arbeitet die Sprachwissenschaft. Präskriptiv schreibt vor, wie Sprache sein soll.",
    d_bewertung(1))
add("Nimm die Gegenposition ernst: Der Verein Deutsche Sprache, gegründet 1997 von Walter "
    "Krämer, kritisiert Denglisch und gibt einen Anglizismen-Index heraus.", d_bewertung(2))
add("Zwei Punkte solltest du wirklich ernst nehmen: Verständlichkeit, etwa für Aeltere und "
    "auf Behördenschildern, und Domänenverlust, wenn ganze Bereiche wie die Wissenschaft "
    "nur noch auf Englisch laufen.", d_bewertung(3))
add("Und als Vergleich Frankreich: Die Loi Toubon vom vierten August 1994 schreibt "
    "Französisch unter anderem in amtlichen Veröffentlichungen, in der Werbung und am "
    "Arbeitsplatz vor. Sprachpolitik per Gesetz ist also möglich. Die Frage ist, ob sie den "
    "Sprachgebrauch wirklich steuert.", d_bewertung(4))

# ---------------------------------------------------------------- Teil E
def part_e(stage):
    def fn(img, d):
        header(d, T, "Teil E", "Das Tafelbild", 5, 8)
        BX, BY, BW_, BH_ = 96, 212, W - 192, 480
        card(d, [BX, BY, BX + BW_, BY + BH_], (38, 50, 44), (24, 32, 28), r=14, width=6)
        d.text((BX + BW_ / 2, BY + 24), "LEITFRAGE:  Bedrohung oder normaler Sprachwandel?",
               font=F(34, True), fill=(248, 246, 238), anchor="ma")
        d.line([(BX + 40, BY + 80), (BX + BW_ - 40, BY + 80)], fill=(140, 160, 148), width=3)
        cols = [("TEXT", ["Autor", "Textsorte", "These"]),
                ("BEFUND", ["die 5 Typen", "2-3 Beispiele", "aus dem Text"]),
                ("URTEIL", ["K  Kontext", "F  Funktion", "Z  Zielgruppe"])]
        cw = (BW_ - 80) / 3
        for i, (t, items) in enumerate(cols):
            x = BX + 40 + i * cw
            on = i < stage
            c = (248, 246, 238) if on else (96, 112, 102)
            d.text((x, BY + 104), t, font=F(32, True), fill=c)
            for j, it in enumerate(items):
                d.text((x, BY + 158 + j * 44), it, font=F(27),
                       fill=c if on else (84, 98, 90))
            if i < 2:
                d.line([(x + cw - 24, BY + 96), (x + cw - 24, BY + BH_ - 110)],
                       fill=(120, 140, 128), width=2)
        if stage >= 4:
            d.line([(BX + 40, BY + BH_ - 96), (BX + BW_ - 40, BY + BH_ - 96)],
                   fill=(140, 160, 148), width=3)
            d.text((BX + BW_ / 2, BY + BH_ - 76), "FAZIT: Nicht ob, sondern wann – "
                   "Kontext, Funktion, Zielgruppe entscheiden.",
                   font=F(30, True), fill=(252, 214, 140), anchor="ma")
        rules = ["Nur das GERÜST vorher anschreiben, Details während des Vortrags",
                 "Beim Schreiben nicht reden – danach kurz zur Klasse drehen",
                 "Max. 7 Zeilen pro Spalte, Druckschrift, GROSS"]
        y = 724
        for i, r in enumerate(rules):
            dot(d, (118, y + 16), 9, T.a1)
            d.text((146, y), r, font=F(27, True), fill=T.fg)
            y += 46
        if stage >= 5:
            card(d, [1180, 712, W - 96, 860], T.panel, T.a2, r=16, width=4)
            txt(d, (1210, 730), "ALTERNATIVE: PRO / CONTRA", F(26, True), T.a2)
            txt(d, (1210, 772), "2 Spalten  PRO | CONTRA", F(28, True), T.fg)
            txt(d, (1210, 812), "darunter Strich + eigenes Urteil", F(24), T.muted)
    return fn


add("Teil E, das Tafelbild. Oben mittig steht die Leitfrage. Links die Spalte Text: Autor, "
    "Textsorte, These.", part_e(1))
add("In der Mitte der Befund: die fünf Typen und zwei bis drei Beispiele aus dem Text. "
    "Rechts das Urteil, mit K, F und Z untereinander.", part_e(3))
add("Unten quer das Fazit in einem Satz. Nur das Gerüst schreibst du vorher an. Beim "
    "Schreiben nicht reden, danach kurz zur Klasse drehen. Maximal sieben Zeilen pro Spalte, "
    "Druckschrift, groß.", part_e(5))

# ---------------------------------------------------------------- Teil F
WENN = [
    ("Text ist GEGEN Anglizismen", "berechtigten Kern nennen (Verständlichkeit), dann mit "
     "Zahlen gegenhalten"),
    ("Text ist FÜR Anglizismen", "nicht blind zustimmen – Domänenverlust als "
     "Einschränkung"),
    ("„nennen / zusammenfassen“", "Station T – kurz halten"),
    ("„analysieren / untersuchen“", "Station A"),
    ("„erläutern / in Zusammenhang setzen“", "Station K"),
    ("„eroertern / beurteilen“", "Station U – das wird die Leitfrage"),
    ("nur 2 Aufgaben", "Station K ausbauen – dort kommt Eigenwissen rein"),
    ("Statistik / Grafik im Text", "Was wird gemessen? Wortschatz oder Verwendung? "
     "Großer Unterschied!"),
    ("Zeit wird knapp", "Station A kürzen – NIEMALS das Fazit streichen"),
    ("Blackout", "zur Tafel drehen, Gliederung lesen: „Zusammengefasst heißt das ...“"),
    ("Wort unbekannt", "aus dem Kontext erschließen und offen sagen: „Aus dem "
     "Zusammenhang verstehe ich darunter ...“"),
]


def part_f(stage):
    def fn(img, d):
        header(d, T, "Teil F", "Wenn-Dann-Regeln", 6, 8)
        txt(d, (120, 196), "WENN", F(26, True), T.a1)
        txt(d, (780, 196), "DANN", F(26, True), T.a2)
        y = 234
        rh = 58
        for i, (w, dn) in enumerate(WENN):
            on = i < stage
            if on:
                d.rounded_rectangle([96, y - 6, W - 96, y + rh - 12],
                                    radius=10, fill=T.panel)
            txt_block(d, 120, y, w, F(27, True), T.fg if on else T.line, 620)
            arrow(d, (742, y + 16), (776, y + 16), T.a2 if on else T.line, 4, 12)
            txt_block(d, 800, y, dn, F(26), T.fg if on else T.line, 1010)
            y += rh
    return fn


add("Teil F, die Wenn-Dann-Regeln. Ist der Text gegen Anglizismen, benenne den berechtigten "
    "Kern, die Verständlichkeit, und halte dann mit Zahlen gegen. Ist er dafür, stimm nicht "
    "blind zu, sondern nenne den Domänenverlust als Einschränkung.", part_f(2))
add("Die Operatoren steuern die Stationen: nennen und zusammenfassen gehen in Station T, "
    "analysieren in Station A, erläutern in Station K, und eroertern oder beurteilen in "
    "Station U. Das wird deine Leitfrage.", part_f(6))
add("Hast du nur zwei Aufgaben, baue Station K aus, da kommt dein Eigenwissen rein. Steht "
    "eine Statistik im Text, frag immer: Was wird eigentlich gemessen, Wortschatz oder "
    "tatsächliche Verwendung? Das ist ein großer Unterschied.", part_f(8))
add("Wird die Zeit knapp, kürze Station A, aber streiche niemals das Fazit. Beim Blackout "
    "drehst du dich zur Tafel, liest deine Gliederung und sagst: Zusammengefasst heißt das. "
    "Und ein unbekanntes Wort erschließt du offen aus dem Zusammenhang.", part_f(11))

# ---------------------------------------------------------------- Teil G
def part_g(stage):
    def fn(img, d):
        header(d, T, "Teil G", "Satzbausteine", 7, 8)
        card(d, [96, 206, 930, 520], T.panel, T.a1, r=20, width=4)
        txt(d, (126, 228), "EINSTIEGE – einen auswählen", F(26, True), T.a1)
        ein = [("Alltag", "„Heute Morgen habe ich im Bus mein Handy gecheckt, ein Update "
                "geladen und einen Post geliked. Vier Anglizismen in einem Satz – und "
                "keiner kam mir fremd vor.“"),
               ("Zahl", "„Nur etwa jedes zweihundertste Wort in deutschen Texten ist ein "
                "Anglizismus. Ist das viel oder wenig?“"),
               ("Provokation", "„Sprechen wir bald nur noch Denglisch?“")]
        y = 272
        for i, (tag, s) in enumerate(ein):
            on = i < max(stage, 1)
            d.text((126, y), tag, font=F(24, True), fill=T.a1 if on else T.line)
            y = txt_block(d, 126, y + 30, s, F(25), T.fg if on else T.line, 770) + 14
        card(d, [950, 206, W - 96, 660], T.panel if stage >= 2 else T.panel2,
             T.a2 if stage >= 2 else T.line, r=20, width=4 if stage >= 2 else 2)
        txt(d, (980, 228), "ÜBERGÄNGE", F(26, True), T.a2 if stage >= 2 else T.line)
        ue = [("E→T", "„Schauen wir uns zunächst an, was der Autor genau "
               "behauptet.“"),
              ("T→A", "„Interessant ist aber nicht nur, WAS er sagt, sondern WIE er "
               "argumentiert.“"),
              ("A→K", "„Um zu verstehen, warum gerade diese Wörter ins Deutsche "
               "gelangt sind, lohnt ein Blick auf die Hintergründe.“"),
              ("K→U", "„Damit stellt sich die entscheidende Frage: Ist diese "
               "Entwicklung ein Problem?“"),
              ("U→F", "„Was heißt das nun für meine Ausgangsfrage?“")]
        y = 272
        for tag, s in ue:
            on = stage >= 2
            pill(d, (980, y), tag, F(22, True), T.panel if on else T.muted,
                 T.a2 if on else T.line, pad=(12, 6))
            y = txt_block(d, 1080, y + 2, s, F(25), T.fg if on else T.line, 700) + 16
        if stage >= 3:
            card(d, [96, 560, 930, 866], T.panel, T.a3, r=20, width=4)
            txt(d, (126, 582), "FAZIT-FORMEL", F(26, True), T.a3)
            txt_block(d, 126, 622, "„Meine Ausgangsfrage war ... Mein Ergebnis: "
                      "Anglizismen sind weder automatisch eine Bereicherung noch ein Verfall. "
                      "Entscheidend sind Kontext, Funktion und Zielgruppe. Sprache wandelt "
                      "sich – das zeigt schon der Blick auf das Französische um 1900. "
                      "Wichtig bleibt, bewusst und verständlich zu formulieren.“",
                      F(25), T.fg, 770)
        if stage >= 3:
            card(d, [950, 700, W - 96, 866], T.panel2, T.a1, r=20, width=3)
            txt(d, (980, 722), "ANTWORT-FORMEL FÜR NACHFRAGEN", F(26, True), T.a1)
            steps = ["These", "Begründung", "Beispiel", "Einschränkung"]
            x = 980
            for i, s in enumerate(steps):
                b = pill(d, (x, 776), s, F(27, True), T.panel, T.a1)
                x = b[2] + 10
                if i < 3:
                    arrow(d, (x - 4, 792), (x + 22, 792), T.a1, 4, 12)
                    x += 30
    return fn


add("Teil G, Satzbausteine. Nimm einen Einstieg: Heute Morgen habe ich im Bus mein Handy "
    "gecheckt, ein Update geladen und einen Post geliked. Vier Anglizismen in einem Satz, "
    "und keiner kam mir fremd vor.", part_g(1))
add("Oder mit einer Zahl: Nur etwa jedes zweihundertste Wort in deutschen Texten ist ein "
    "Anglizismus. Ist das viel oder wenig? Die Übergänge zwischen den Stationen lernst du "
    "wörtlich.", part_g(2))
add("Und die Fazit-Formel: Anglizismen sind weder automatisch eine Bereicherung noch ein "
    "Verfall. Entscheidend sind Kontext, Funktion und Zielgruppe.", part_g(3))

# ---------------------------------------------------------------- Teil H
def part_h(stage):
    def fn(img, d):
        header(d, T, "Teil H", "Die Nachfragen", 8, 8)
        qs = [("„Wie sind Sie vorgegangen?“",
               "Operatoren markiert, Leitfrage aus der schwersten Aufgabe gebildet, Text auf "
               "These, Argumente und Anglizismen markiert, in sechs Stationen von der "
               "Beschreibung zur Bewertung geordnet – das Tafelbild zeigt genau diesen "
               "roten Faden."),
              ("„Benutzen Sie selbst Anglizismen?“",
               "Ja, vor allem digital und unter Freunden – aber angepasst: In einer "
               "Bewerbung formuliere ich anders. Das ist Adressatenorientierung."),
              ("„Gesetzlich regeln wie in Frankreich?“",
               "Loi Toubon 1994 nennen, dann abwägen: Behörden und Werbung lassen sich "
               "regulieren, Alltagssprache kaum."),
              ("„Ist das nicht Sprachverfall?“",
               "Deskriptiv und präskriptiv unterscheiden, Entwarnung aus dem Bericht von "
               "2013, historische Parallele Französisch.")]
        y = 206
        for i, (q, a) in enumerate(qs):
            on = i < stage
            card(d, [96, y, W - 96, y + 158], T.panel if on else T.panel2,
                 T.a1 if on else T.line, r=18, width=4 if on else 2)
            d.text((130, y + 20), q, font=F(34, True), fill=T.fg if on else T.line)
            txt_block(d, 130, y + 70, a, F(25), T.muted if on else T.line, 1660)
            y += 172
    return fn


def s_end(img, d):
    big_statement(img, d, T, "Ein Toller Auftritt Kriegt Unbedingt Fünfzehn",
                  T.a1, "Einstieg · Text · Analyse · Kontext · "
                  "Urteil · Fazit")
    y = 660
    txt(d, (W / 2, y), "Leitfrage zuerst  ·  ZBB für Material  ·  "
        "KFZ für jedes Urteil  ·  Konjunktiv I in der Wiedergabe",
        F(30, True), T.fg, anchor="ma")
    txt(d, (W / 2, y + 60), "Nicht OB Anglizismen angemessen sind, sondern WANN.",
        F(36, True), T.a2, anchor="ma")


add("Teil H, die Nachfragen. Antworte immer in vier Schritten: These, Begründung, Beispiel, "
    "Einschränkung. Fragt der Lehrer, wie du vorgegangen bist, beschreibst du genau dieses "
    "System.", part_h(1))
add("Benutzen Sie selbst Anglizismen? Ja, vor allem digital und unter Freunden, aber "
    "angepasst: In einer Bewerbung formuliere ich anders. Das ist Adressatenorientierung.",
    part_h(2))
add("Sollte man das gesetzlich regeln wie in Frankreich? Nenne die Loi Toubon von 1994 und "
    "wäge ab: Behörden und Werbung lassen sich regulieren, die Alltagssprache kaum.",
    part_h(3))
add("Und ist das nicht Sprachverfall? Unterscheide deskriptiv und präskriptiv, nenne die "
    "Entwarnung aus dem Bericht von 2013 und die historische Parallele zum Französischen.",
    part_h(4))
add("Merke dir: Ein Toller Auftritt Kriegt Unbedingt Fünfzehn. Leitfrage zuerst, Z-B-B für "
    "das Material, K-F-Z für jedes Urteil. Die Frage ist nicht, ob Anglizismen angemessen "
    "sind, sondern wann. Viel Erfolg.", s_end)
