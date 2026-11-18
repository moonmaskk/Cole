"""Start: python -m clipfabrik   (oder ClipFabrik.exe)"""
import argparse

from . import db
from .pipeline import Pipeline
from .server import serve


def main() -> None:
    ap = argparse.ArgumentParser(prog="clipfabrik")
    ap.add_argument("--no-browser", action="store_true", help="Browser nicht automatisch öffnen")
    ap.add_argument("--demo", action="store_true", help="einen Testclip ohne Twitch erzeugen und beenden")
    args = ap.parse_args()

    p = Pipeline()
    if args.demo:
        cid = p.demo()
        print("Demo-Kandidat:", cid)
        for step in (p._cut_one, p._judge_one, p._render_one):
            step()
        print(db.get(cid)["status"] if cid else "kein Trigger", db.get(cid)["error"] if cid else "")
        return
    p.start()
    serve(p, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
