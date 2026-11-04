"""Kommandozeile:  python -m cole <befehl> [optionen]"""
from __future__ import annotations

import argparse
import os
import signal
import sys
import time

from . import __version__
from .backtest import fmt_result, run_backtest, walk_forward
from .bot import ContextCache, run_cycle
from .config import load_config
from .dashboard import (bold, context_lines, dim, green, print_header, print_portfolio, print_signals, red,
                        write_html, yellow)
from .data import DataError, get_source, market_context
from .paper import Portfolio, stats
from .strategy import analyze

STABLES = {"USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDE", "PYUSD", "EUR", "EURC", "EURT", "USD", "GBP", "BUSD",
           "USDS", "RLUSD", "USD1", "AEUR", "EURI", "USDQ", "USDR", "USDG", "PAXG", "XAUT"}


def _cfg(args):
    over = {"source": args.source, "interval_min": args.interval, "quote": args.quote}
    if getattr(args, "symbols", None):
        over["watchlist"] = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    if getattr(args, "no_context", False):
        over["use_context"] = False
    return load_config(args.config, **over)


def _state_path(cfg):
    return os.path.join(cfg.data_dir, f"paper_{cfg.source}.json")


def _load_portfolio(cfg, path):
    if cfg.source == "sim":
        # Der Simulator erzeugt bei jedem Start einen neuen Markt -> altes Depot passt nicht dazu
        print(dim("Simulator: Paper-Depot startet bei jedem Programmstart neu."))
        return Portfolio(cfg)
    return Portfolio.load(cfg, path)


# ---------------------------------------------------------------- Befehle
def cmd_trends(args) -> int:
    cfg = _cfg(args)
    src = get_source(cfg.source)
    q = cfg.resolved_quote()
    print_header(cfg, "MARKT-TRENDS")
    ctx = market_context(cfg.source, [])
    for line in context_lines(ctx):
        print("  " + line)
    try:
        tick = [t for t in src.tickers(q) if t["base"] not in STABLES]
    except DataError as exc:
        print(red(f"Ticker konnten nicht geladen werden: {exc}"))
        return 1
    tick = [t for t in tick if t["quote_volume"] >= args.min_volume]
    if not tick:
        print(yellow("Keine Paare über dem Mindestvolumen."))
        return 0
    span = "seit 00:00 UTC" if cfg.source == "kraken" else "24h"
    def table(title, rows):
        print()
        print(bold(f"{title}"))
        for t in rows:
            chg = f"{t['change_pct']:+7.2f}%"
            print(f"  {t['base']:<8} {t['last']:>14.6g}  {green(chg) if t['change_pct'] >= 0 else red(chg)}"
                  f"  Vol {t['quote_volume']/1e6:8.2f} Mio {q}")
    table(f"Top-Gewinner ({span})", sorted(tick, key=lambda t: -t["change_pct"])[:args.top])
    table(f"Top-Verlierer ({span})", sorted(tick, key=lambda t: t["change_pct"])[:args.top])
    table("Höchstes Handelsvolumen", sorted(tick, key=lambda t: -t["quote_volume"])[:args.top])

    # Momentum-Kandidaten technisch prüfen
    movers = [t["base"] for t in sorted(tick, key=lambda t: -abs(t["change_pct"]) * (t["quote_volume"] ** 0.25))]
    candidates = list(dict.fromkeys(cfg.watchlist[:4] + movers))[: args.analyze]
    print()
    print(bold(f"Technische Analyse ({len(candidates)} Coins, {cfg.interval_min}m-Kerzen):"))
    pf = Portfolio(cfg)
    sigs = []
    for b in candidates:
        try:
            sigs.append(analyze(b, src.candles(b, q, cfg.interval_min, cfg.history), cfg))
        except (DataError, ValueError, StopIteration) as exc:
            print(dim(f"  {b}: übersprungen ({exc})"))
    print_signals(sigs, cfg, pf, {s.symbol: s.price for s in sigs})
    return 0


def cmd_scan(args) -> int:
    cfg = _cfg(args)
    src = get_source(cfg.source)
    pf = _load_portfolio(cfg, _state_path(cfg))
    rep = run_cycle(cfg, src, pf, ContextCache(), trade=False)
    print_header(cfg, "SCAN")
    for line in context_lines(rep.context):
        print("  " + line)
    print()
    print_signals(rep.signals, cfg, pf, rep.prices)
    for e in rep.errors:
        print(yellow("  ! " + e))
    return 0 if rep.signals else 1


def cmd_paper(args) -> int:
    cfg = _cfg(args)
    if args.seconds:
        cfg.loop_seconds = args.seconds
    src = get_source(cfg.source)
    path = _state_path(cfg)
    pf = _load_portfolio(cfg, path)
    cache = ContextCache()
    html_path = os.path.join(cfg.data_dir, "dashboard.html")
    events_log = []
    n = 0
    print(dim(f"Paper-Trading gestartet. Depot: {path} | Dashboard: {os.path.abspath(html_path)}"))
    print(dim("Beenden mit Strg+C. Neue Einstiege pausieren: Datei 'STOP' anlegen."))
    try:
        while True:
            n += 1
            rep = run_cycle(cfg, src, pf, cache, trade=True)
            pf.save(path)
            events_log.extend(f"{time.strftime('%H:%M:%S')} {e}" for e in rep.events)
            write_html(html_path, cfg, rep.signals, pf, rep.prices, rep.context, events_log)
            if not args.quiet:
                if sys.stdout.isatty() and not args.once:
                    print("\033[2J\033[H", end="")
                print_header(cfg, f"PAPER-TRADING · Zyklus {n}")
                for line in context_lines(rep.context):
                    print("  " + line)
                print()
                print_signals(rep.signals, cfg, pf, rep.prices)
                print()
                print_portfolio(pf, rep.prices, cfg)
                if events_log:
                    print()
                    print(bold("Ereignisse:"))
                    for e in events_log[-8:]:
                        print("  " + e)
                for e in rep.errors:
                    print(yellow("  ! " + e))
            if args.once or (args.cycles and n >= args.cycles):
                break
            time.sleep(0 if cfg.source == "sim" and args.fast else cfg.loop_seconds)
    except KeyboardInterrupt:
        print("\nGestoppt. Depot gespeichert.")
    pf.save(path)
    return 0


def cmd_status(args) -> int:
    cfg = _cfg(args)
    pf = Portfolio.load(cfg, _state_path(cfg))
    prices = {k: p.entry for k, p in pf.positions.items()}
    print_header(cfg, "DEPOT-STATUS (Preise = Einstieg, für Live-Preise 'scan' nutzen)")
    print_portfolio(pf, prices, cfg)
    s = stats(pf.trades)
    if s["n"]:
        pf_txt = "∞" if s["profit_factor"] == float("inf") else f"{s['profit_factor']:.2f}"
        print(f"  Netto {s['net']:+.2f} | Profit-Faktor {pf_txt} | Ø {s['avg_r']:+.2f}R | "
              f"bester {s['best']:+.2f} | schlechtester {s['worst']:+.2f}")
    for t in pf.trades[-15:]:
        txt = (f"  {time.strftime('%d.%m %H:%M', time.gmtime(t.closed_at))} {t.symbol:<6} {t.pnl:+10.2f} "
               f"({t.r_multiple:+.2f}R) {t.exit_reason}")
        print(green(txt) if t.pnl > 0 else red(txt))
    return 0


def cmd_reset(args) -> int:
    cfg = _cfg(args)
    path = _state_path(cfg)
    if os.path.exists(path):
        os.replace(path, path + f".backup-{int(time.time())}")
    print(f"Paper-Depot zurückgesetzt auf {cfg.start_capital:,.2f} {cfg.resolved_quote()} (Backup angelegt).")
    return 0


def _load_history(cfg, symbol, bars):
    src = get_source(cfg.source)
    candles = src.candles(symbol, cfg.resolved_quote(), cfg.interval_min, bars)
    if cfg.source == "kraken" and len(candles) < bars:
        print(yellow(f"Hinweis: Kraken liefert max. 720 Kerzen. Für längere Backtests: --source binance"))
    return candles[:-1]  # laufende Kerze weglassen


def cmd_backtest(args) -> int:
    cfg = _cfg(args)
    symbols = cfg.watchlist if args.all else [args.symbol.upper()]
    print_header(cfg, "BACKTEST")
    for sym in symbols:
        try:
            candles = _load_history(cfg, sym, args.bars)
            r = run_backtest(candles, cfg, sym)
        except (DataError, ValueError, StopIteration) as exc:
            print(red(f"{sym}: {exc}"))
            continue
        days = len(candles) * cfg.interval_min / 1440
        print(bold(f"\n{sym}/{cfg.resolved_quote()} · {len(candles)} Kerzen (~{days:.0f} Tage)"))
        for k, v in fmt_result(r).items():
            print(f"  {k:<16} {v}")
        if r["t_n"] < 30:
            print(yellow("  Wenige Trades - statistisch kaum aussagekräftig (Faustregel: 100+)."))
        if args.trades:
            for t in r["trades"]:
                txt = f"    {time.strftime('%d.%m %H:%M', time.gmtime(t.opened_at))} {t.pnl:+9.2f} ({t.r_multiple:+.2f}R) {t.exit_reason}"
                print(green(txt) if t.pnl > 0 else red(txt))
    return 0


def cmd_optimize(args) -> int:
    cfg = _cfg(args)
    sym = args.symbol.upper()
    print_header(cfg, f"WALK-FORWARD-OPTIMIERUNG {sym}")
    try:
        candles = _load_history(cfg, sym, args.bars)
        res = walk_forward(candles, cfg, sym)
    except (DataError, ValueError) as exc:
        print(red(str(exc)))
        return 1
    if not res:
        print(yellow("Keine Parameter-Kombination mit genug Trades."))
        return 0
    print(dim("Optimiert auf den ersten 70 % der Daten, geprüft auf den letzten 30 % (ungesehen)."))
    print(bold(f"{'Parameter':<44} {'Train':>9} {'Test':>9} {'Test-DD':>8} {'Test-Trades':>11}"))
    for r in res[:8]:
        p = r["params"]
        ptxt = f"Schwelle {p['buy_threshold']:.0f}, Stop {p['atr_stop_mult']}xATR, RR {p['reward_risk']}"
        te = r["test"]
        tt = f"{te['return_pct']:+.2f}%"
        print(f"{ptxt:<44} {r['train']['return_pct']:+8.2f}% {green(tt) if te['return_pct'] > 0 else red(tt):>9} "
              f"{te['max_drawdown_pct']:7.2f}% {te['t_n']:>11}")
    print(yellow("\nWenn Train gut und Test schlecht ist = Überanpassung. Nur Parameter übernehmen, die in BEIDEN "
                 "Phasen stabil sind - und auch Nachbarwerte funktionieren."))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cole", description="Krypto-Daytrading-Analyse & Paper-Trading (nur Spielgeld).")
    p.add_argument("--version", action="version", version=__version__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", help="Pfad zur config.json (Standard: ./config.json)")
    common.add_argument("--source", choices=["kraken", "binance", "sim"], help="Datenquelle")
    common.add_argument("--interval", type=int, help="Kerzen in Minuten (1,5,15,30,60,240,1440)")
    common.add_argument("--quote", help="Quote-Währung, z.B. EUR oder USDT")
    common.add_argument("--symbols", help="Watchlist überschreiben, z.B. BTC,ETH,SOL")
    common.add_argument("--no-context", action="store_true", help="Fear&Greed/Funding/BTC-Filter aus")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("trends", parents=[common], help="Markt-Überblick: Top-Mover, Trending, Stimmung + Analyse")
    s.add_argument("--top", type=int, default=8)
    s.add_argument("--analyze", type=int, default=10, help="Wie viele Coins technisch analysiert werden")
    s.add_argument("--min-volume", type=float, default=1_000_000, help="Min. 24h-Volumen in Quote-Währung")
    s.set_defaults(func=cmd_trends)

    s = sub.add_parser("scan", parents=[common], help="Einmalige Analyse der Watchlist mit Vorschlägen")
    s.set_defaults(func=cmd_scan)

    s = sub.add_parser("paper", parents=[common], help="Live-Testmodus: handelt laufend mit virtuellem Geld")
    s.add_argument("--once", action="store_true", help="Nur ein Zyklus")
    s.add_argument("--cycles", type=int, default=0, help="Nach N Zyklen beenden")
    s.add_argument("--seconds", type=int, help="Sekunden zwischen Zyklen")
    s.add_argument("--fast", action="store_true", help="Simulator ohne Pause laufen lassen")
    s.add_argument("--quiet", action="store_true")
    s.set_defaults(func=cmd_paper)

    s = sub.add_parser("status", parents=[common], help="Paper-Depot und Trade-Historie anzeigen")
    s.set_defaults(func=cmd_status)
    s = sub.add_parser("reset", parents=[common], help="Paper-Depot zurücksetzen (mit Backup)")
    s.set_defaults(func=cmd_reset)

    s = sub.add_parser("backtest", parents=[common], help="Strategie auf historischen Daten testen")
    s.add_argument("--symbol", default="BTC")
    s.add_argument("--all", action="store_true", help="Ganze Watchlist testen")
    s.add_argument("--bars", type=int, default=3000)
    s.add_argument("--trades", action="store_true", help="Einzelne Trades auflisten")
    s.set_defaults(func=cmd_backtest)

    s = sub.add_parser("optimize", parents=[common], help="Walk-Forward-Parameteroptimierung (gegen Überanpassung)")
    s.add_argument("--symbol", default="BTC")
    s.add_argument("--bars", type=int, default=4000)
    s.set_defaults(func=cmd_optimize)
    return p


def main(argv=None) -> int:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # sauber beenden bei "| head"
    args = build_parser().parse_args(argv)
    return args.func(args)
