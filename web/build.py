"""Erzeugt docs/index.html (GitHub Pages / beliebiger Webspace) aus web/app.html."""
import pathlib, shutil

root = pathlib.Path(__file__).resolve().parent.parent
app = (root / "web" / "app.html").read_text(encoding="utf-8")
head = """<!doctype html>
<html lang="de"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#2f4fd8">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Cole">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icon-180.png">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>
</head><body>
"""
out = root / "docs"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(head + app + "\n</body></html>\n", encoding="utf-8")
for f in ("manifest.webmanifest", "icon.svg", "icon-180.png", "icon-512.png"):
    src = root / "web" / f
    if src.exists():
        shutil.copy(src, out / f)
(out / ".nojekyll").write_text("")
print("docs/index.html erzeugt")
