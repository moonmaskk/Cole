"""Ausgabe: farbiges Terminal-Dashboard + automatisch aktualisierte HTML-Seite."""
from __future__ import annotations

import html
import os
import sys
import time
from typing import Dict, List, Optional

from .config import Config
from .data import interval_label
from .paper import Portfolio, stats
from .strategy import Signal

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
if os.name == "nt":
    os.system("")  # ANSI-Farben im Windows-Terminal aktivieren

DISCLAIMER = ("Nur Analyse & Paper-Trading mit Spielgeld - keine Anlageberatung. "
              "Krypto-Daytrading ist hochriskant; die meisten Daytrader verlieren Geld.")


def col(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t): return col(t, "32")
def red(t): return col(t, "31")
def yellow(t): return col(t, "33")
def bold(t): return col(t, "1")
def dim(t): return col(t, "2")


def fmt_price(p: Optional[float]) -> str:
    if p is None:
        return "-"
    if p >= 1000:
        return f"{p:.0f}"
    if p >= 1:
        return f"{p:.2f}"
    return f"{p:.5f}"


def action_label(sig: Signal) -> str:
    if sig.action == "BUY":
        return green("KAUFEN") if not sig.blockers else yellow("KAUFEN*")
    if sig.action == "SELL":
        return red("VERKAUFEN/MEIDEN")
    return dim("HALTEN/ABWARTEN")


def score_bar(score: float, width: int = 10) -> str:
    n = int(round(abs(score) / 100 * width))
    bar = ("█" * n).ljust(width, "·")
    return green(bar) if score > 0 else red(bar) if score < 0 else bar


def context_lines(ctx: dict) -> List[str]:
    out = []
    fg = ctx.get("fear_greed")
    if fg:
        prev = f" (vorher {fg['previous']})" if fg.get("previous") is not None else ""
        out.append(f"Fear & Greed: {bold(str(fg['value']))} {fg['label']}{prev}")
    g = ctx.get("global")
    if g and g.get("btc_dominance") is not None:
        chg = g.get("mcap_change_24h")
        out.append(f"BTC-Dominanz: {g['btc_dominance']:.1f}%  |  Marktkap. 24h: "
                   f"{chg:+.2f}%" if chg is not None else f"BTC-Dominanz: {g['btc_dominance']:.1f}%")
    tr = ctx.get("trending")
    if tr:
        out.append("Trending (CoinGecko): " + ", ".join(t["symbol"] for t in tr[:8]))
    fu = ctx.get("funding")
    if fu:
        out.append("Funding/8h: " + "  ".join(f"{k} {v['funding']*100:+.3f}%" for k, v in list(fu.items())[:8]))
    return out


def print_signals(signals: List[Signal], cfg: Config, pf: Optional[Portfolio] = None, prices=None) -> None:
    q = cfg.resolved_quote()
    print(bold(f"{'Coin':<6} {'Preis':>12} {'Score':>6} {'':10} {'Regime':<10} {'Empfehlung':<18} {'Stop':>11} {'Ziel':>11}"))
    for s in sorted(signals, key=lambda x: -x.score):
        print(f"{s.symbol:<6} {fmt_price(s.values.get('last_price', s.price)):>12} {s.score:>6.1f} {score_bar(s.score)} "
              f"{s.regime:<10} {action_label(s):<27} {fmt_price(s.stop):>11} {fmt_price(s.take_profit):>11}")
    buys = [s for s in signals if s.action == "BUY"]
    if buys:
        print()
        print(bold("Vorschläge im Detail:"))
    for s in sorted(buys, key=lambda x: -x.score):
        line = f"  ▶ {s.symbol}: Kauf bei ~{fmt_price(s.values.get('last_price', s.price))} {q}, Stop {fmt_price(s.stop)}, Ziel {fmt_price(s.take_profit)}"
        if pf is not None and prices:
            qty = pf.position_size(s.price, s.stop, prices, s.score)
            if qty > 0:
                line += (f" | Größe {qty:.6g} (~{qty*s.price:,.2f} {q}), Risiko ~{qty*(s.price-s.stop):,.2f} {q}")
        print(green(line))
        print(f"    Gründe: {'; '.join(s.reasons) or '-'}  (Konfidenz: {s.confidence})")
        if s.blockers:
            print(yellow(f"    * Achtung: {', '.join(s.blockers)}"))


def print_portfolio(pf: Portfolio, prices: Dict[str, float], cfg: Config) -> None:
    q = cfg.resolved_quote()
    eq = pf.equity(prices)
    pnl = eq - cfg.start_capital
    s = stats(pf.trades)
    pnl_txt = f"{pnl:+,.2f} {q} ({pnl/cfg.start_capital*100:+.2f}%)"
    print(bold(f"Paper-Depot: {eq:,.2f} {q}  ") + (green(pnl_txt) if pnl >= 0 else red(pnl_txt)) +
          f"  | Cash {pf.cash:,.2f} | Trades {s['n']} | Treffer {s['win_rate']:.0f}% | Gebühren {pf.fees_paid:,.2f}")
    for sym, p in pf.positions.items():
        px = prices.get(sym, p.entry)
        u = (px / p.entry - 1) * 100
        txt = f"  {sym:<6} {p.qty:.6g} @ {fmt_price(p.entry)} -> {fmt_price(px)} ({u:+.2f}%)  Stop {fmt_price(p.stop)}  Ziel {fmt_price(p.take_profit)}"
        print(green(txt) if u >= 0 else red(txt))


def print_header(cfg: Config, title: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(bold(f"═══ COLE · {title} · {cfg.source} · {interval_label(cfg.interval_min)} · {ts} ═══"))
    print(dim(DISCLAIMER))


# ---------------------------------------------------------------- HTML
def _spark(curve: List[list], w: int = 600, h: int = 120) -> str:
    pts = [e for _, e in curve[-500:]]
    if len(pts) < 2:
        return "<p class='muted'>Noch keine Equity-Daten.</p>"
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1
    path = " ".join(f"{i*w/(len(pts)-1):.1f},{h-(p-lo)/span*h:.1f}" for i, p in enumerate(pts))
    return (f"<svg viewBox='0 0 {w} {h}' preserveAspectRatio='none' class='spark' role='img' "
            f"aria-label='Equity-Verlauf'><polyline fill='none' stroke='currentColor' stroke-width='2' points='{path}'/></svg>")


def write_html(path: str, cfg: Config, signals: List[Signal], pf: Portfolio, prices: Dict[str, float],
               ctx: dict, events: List[str]) -> None:
    q = cfg.resolved_quote()
    e = html.escape
    eq = pf.equity(prices)
    s = stats(pf.trades)
    pnl = eq - cfg.start_capital
    rows = []
    for sg in sorted(signals, key=lambda x: -x.score):
        cls = "buy" if sg.action == "BUY" else "sell" if sg.action == "SELL" else ""
        label = {"BUY": "Kaufen", "SELL": "Verkaufen/Meiden"}.get(sg.action, "Abwarten")
        rows.append(f"<tr class='{cls}'><td>{e(sg.symbol)}</td><td>{fmt_price(sg.values.get('last_price', sg.price))}</td>"
                    f"<td>{sg.score:+.1f}</td><td>{e(sg.regime)}</td><td>{label}</td><td>{fmt_price(sg.stop)}</td>"
                    f"<td>{fmt_price(sg.take_profit)}</td><td class='why'>{e('; '.join(sg.reasons + sg.blockers))}</td></tr>")
    pos_rows = "".join(
        f"<tr><td>{e(k)}</td><td>{p.qty:.6g}</td><td>{fmt_price(p.entry)}</td><td>{fmt_price(prices.get(k, p.entry))}</td>"
        f"<td>{(prices.get(k, p.entry)/p.entry-1)*100:+.2f}%</td><td>{fmt_price(p.stop)}</td><td>{fmt_price(p.take_profit)}</td></tr>"
        for k, p in pf.positions.items()) or "<tr><td colspan='7' class='muted'>Keine offenen Positionen</td></tr>"
    trade_rows = "".join(
        f"<tr class='{'buy' if t.pnl > 0 else 'sell'}'><td>{time.strftime('%d.%m %H:%M', time.gmtime(t.closed_at))}</td>"
        f"<td>{e(t.symbol)}</td><td>{fmt_price(t.entry)}</td><td>{fmt_price(t.exit)}</td><td>{t.pnl:+.2f}</td>"
        f"<td>{t.r_multiple:+.2f}R</td><td>{e(t.exit_reason)}</td></tr>"
        for t in reversed(pf.trades[-30:])) or "<tr><td colspan='7' class='muted'>Noch keine Trades</td></tr>"
    ctx_html = "".join(f"<li>{e(_strip_ansi(l))}</li>" for l in context_lines(ctx)) or "<li class='muted'>Kein Kontext verfügbar</li>"
    ev_html = "".join(f"<li>{e(x)}</li>" for x in events[-15:]) or "<li class='muted'>Keine neuen Ereignisse</li>"
    doc = f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="{max(15, cfg.loop_seconds)}">
<title>Cole Paper-Bot</title>
<style>
:root{{--bg:#f7f7f5;--fg:#1c1c1a;--muted:#6b6b66;--card:#fff;--line:#e3e3de;--up:#1a7f37;--down:#c0392b;--upbg:#e8f5ec;--downbg:#fbeaea}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141413;--fg:#ececea;--muted:#9a9a94;--card:#1e1e1c;--line:#2e2e2b;--up:#4cc76a;--down:#ff6b5e;--upbg:#14301c;--downbg:#3a1714}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:16px}}
h1{{font-size:20px;margin:0 0 4px}} h2{{font-size:15px;margin:0 0 8px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0;overflow-x:auto}}
.kpis{{display:flex;flex-wrap:wrap;gap:20px}} .kpi b{{display:block;font-size:20px}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}}
td.why{{white-space:normal;min-width:240px;color:var(--muted)}}
tr.buy td:nth-child(5){{color:var(--up);font-weight:600}} tr.sell td:nth-child(5){{color:var(--down)}}
.pos{{color:var(--up)}} .neg{{color:var(--down)}} .muted{{color:var(--muted)}}
.spark{{width:100%;height:120px;color:var(--up)}} small{{color:var(--muted)}}
</style></head><body><main>
<h1>Cole · Krypto Paper-Trading</h1>
<small>{e(cfg.source)} · {interval_label(cfg.interval_min)} · aktualisiert {time.strftime('%d.%m.%Y %H:%M:%S')} · lädt alle {max(15, cfg.loop_seconds)} s neu</small>
<div class="card kpis">
<div class="kpi">Depotwert<b>{eq:,.2f} {q}</b></div>
<div class="kpi">Gewinn/Verlust<b class="{'pos' if pnl >= 0 else 'neg'}">{pnl:+,.2f} ({pnl/cfg.start_capital*100:+.2f}%)</b></div>
<div class="kpi">Trades<b>{s['n']}</b></div><div class="kpi">Trefferquote<b>{s['win_rate']:.0f}%</b></div>
<div class="kpi">Gebühren<b>{pf.fees_paid:,.2f}</b></div></div>
<div class="card"><h2>Equity-Verlauf</h2>{_spark(pf.equity_curve)}</div>
<div class="card"><h2>Signale & Vorschläge</h2><table><tr><th>Coin</th><th>Preis</th><th>Score</th><th>Regime</th><th>Empfehlung</th><th>Stop</th><th>Ziel</th><th>Begründung</th></tr>{''.join(rows)}</table></div>
<div class="card"><h2>Markt-Kontext</h2><ul>{ctx_html}</ul></div>
<div class="card"><h2>Offene Positionen</h2><table><tr><th>Coin</th><th>Menge</th><th>Einstieg</th><th>Aktuell</th><th>+/-</th><th>Stop</th><th>Ziel</th></tr>{pos_rows}</table></div>
<div class="card"><h2>Letzte Ereignisse</h2><ul>{ev_html}</ul></div>
<div class="card"><h2>Abgeschlossene Trades</h2><table><tr><th>Zeit</th><th>Coin</th><th>Einstieg</th><th>Ausstieg</th><th>G/V</th><th>R</th><th>Grund</th></tr>{trade_rows}</table></div>
<p><small>{e(DISCLAIMER)}</small></p>
</main></body></html>"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)


def _strip_ansi(s: str) -> str:
    import re
    return re.sub(r"\033\[[0-9;]*m", "", s)
