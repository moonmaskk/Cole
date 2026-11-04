import json
import os
import tempfile
import unittest
from unittest import mock

from cole import data as data_mod
from cole import indicators as ind
from cole.backtest import run_backtest, walk_forward
from cole.config import Config, load_config
from cole.data import Candle, KrakenSource, SimSource
from cole.paper import Portfolio
from cole.strategy import WARMUP, analyze, compute, entry_blockers, make_signal


def sim_candles(n=800, base="ETH", interval=60):
    return SimSource().candles(base, "EUR", interval, n)


class IndicatorTests(unittest.TestCase):
    def test_sma_ema(self):
        vals = [1, 2, 3, 4, 5, 6]
        self.assertEqual(ind.sma(vals, 3)[2], 2)
        self.assertIsNone(ind.sma(vals, 3)[1])
        e = ind.ema(vals, 3)
        self.assertEqual(e[2], 2)                      # Start = SMA
        self.assertAlmostEqual(e[3], 4 * 0.5 + 2 * 0.5)

    def test_rsi_extremes(self):
        up = [float(i) for i in range(1, 40)]
        self.assertEqual(ind.rsi(up)[-1], 100.0)
        down = list(reversed(up))
        self.assertAlmostEqual(ind.rsi(down)[-1], 0.0)

    def test_atr_constant_range(self):
        h = [11.0] * 30
        l = [9.0] * 30
        c = [10.0] * 30
        self.assertAlmostEqual(ind.atr(h, l, c)[-1], 2.0)

    def test_adx_strong_trend(self):
        h = [10 + i for i in range(80)]
        l = [9 + i for i in range(80)]
        c = [9.5 + i for i in range(80)]
        self.assertGreater(ind.adx(h, l, c)[-1], 50)


class NoLookaheadTests(unittest.TestCase):
    def test_signal_unchanged_by_future_candles(self):
        cs = sim_candles(700)
        cfg = Config(source="sim")
        i = 600
        a = make_signal("ETH", compute(cs[: i + 1]), i, cfg)
        b = make_signal("ETH", compute(cs), i, cfg)
        self.assertEqual(a.score, b.score)
        self.assertEqual(a.action, b.action)

    def test_analyze_ignores_running_candle(self):
        cs = sim_candles(400)
        cfg = Config(source="sim")
        s1 = analyze("ETH", cs, cfg)
        cs2 = cs[:-1] + [Candle(cs[-1].t, cs[-1].o, cs[-1].h * 5, cs[-1].l, cs[-1].c * 3, cs[-1].v * 9)]
        s2 = analyze("ETH", cs2, cfg)
        self.assertEqual(s1.score, s2.score)


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.cfg = Config(fee_pct=0.1, slippage_pct=0.0, risk_per_trade_pct=1.0, max_position_pct=100,
                          start_capital=10_000, trade_amount_min=0, min_order=10)
        self.pf = Portfolio(self.cfg)

    def test_risk_based_size(self):
        p = self.pf.open("BTC", 100.0, 5.0, 2.5, 0, {"BTC": 100.0})
        # 1 % von 10.000 = 100 Risiko / 5 Abstand = 20 Stück
        self.assertAlmostEqual(p.qty, 20.0)
        self.assertAlmostEqual(p.stop, 95.0)
        self.assertAlmostEqual(p.take_profit, 110.0)

    def test_stop_loss_costs_about_one_r(self):
        self.pf.open("BTC", 100.0, 5.0, 2.5, 0, {"BTC": 100.0})
        tr = self.pf.check_exits("BTC", 99, 99.5, 94, 3600, 1)
        self.assertEqual(tr.exit_reason, "Stop-Loss")
        self.assertAlmostEqual(tr.r_multiple, -1.0, delta=0.1)   # -1R plus Gebühren
        self.assertLess(tr.pnl, -100)

    def test_gap_fills_at_open(self):
        self.pf.open("BTC", 100.0, 5.0, 2.5, 0, {"BTC": 100.0})
        tr = self.pf.check_exits("BTC", 90, 91, 89, 3600, 1)
        self.assertEqual(tr.exit, 90)

    def test_take_profit_and_cash_accounting(self):
        self.pf.open("BTC", 100.0, 5.0, 2.5, 0, {"BTC": 100.0})
        tr = self.pf.check_exits("BTC", 101, 111, 100.5, 3600, 1)
        self.assertEqual(tr.exit_reason, "Take-Profit")
        self.assertAlmostEqual(self.pf.cash, 10_000 + tr.pnl, places=6)

    def test_limits(self):
        self.pf.open("BTC", 100.0, 5.0, 2.5, 0, {"BTC": 100.0})
        self.assertEqual(self.pf.can_open("BTC", 0, {}), "Position bereits offen")
        self.pf.day_start_equity = 20_000
        self.assertIn("Tagesverlust", self.pf.can_open("ETH", 0, {"BTC": 100.0}))

    def test_cooldown_after_loss(self):
        self.pf.open("BTC", 100.0, 5.0, 2.5, 0, {"BTC": 100.0})
        self.pf.check_exits("BTC", 99, 99, 90, 3600, 10)
        self.assertEqual(self.pf.can_open("BTC", 11, {}), "Cooldown nach Verlust")
        self.assertIsNone(self.pf.can_open("BTC", 10 + self.cfg.cooldown_bars, {}))

    def test_trailing_moves_stop_up(self):
        self.pf.open("BTC", 100.0, 5.0, 2.5, 0, {"BTC": 100.0})
        self.pf.update_trailing("BTC", 106)
        self.assertGreater(self.pf.positions["BTC"].stop, 100)

    def test_save_load_roundtrip(self):
        self.pf.open("BTC", 100.0, 5.0, 2.5, 0, {"BTC": 100.0})
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "s.json")
            self.pf.save(path)
            pf2 = Portfolio.load(self.cfg, path)
        self.assertAlmostEqual(pf2.cash, self.pf.cash)
        self.assertIn("BTC", pf2.positions)


class SmallAmountTests(unittest.TestCase):
    def test_trade_between_5_and_7(self):
        cfg = Config(start_capital=50, trade_amount_min=5, trade_amount_max=7, fee_pct=0.1, slippage_pct=0)
        pf = Portfolio(cfg)
        weak = pf.open("BTC", 100.0, 2.0, 1.0, 0, {}, score=cfg.buy_threshold)
        strong = pf.open("ETH", 100.0, 2.0, 1.0, 0, {}, score=100)
        self.assertAlmostEqual(weak.qty * weak.entry, 5.0)
        self.assertAlmostEqual(strong.qty * strong.entry, 7.0)

    def test_fixed_fee_blocks_small_trades(self):
        cs = sim_candles(400)
        cfg = Config(source="sim", fee_pct=0, fee_fixed=1.0, trade_amount_min=6)
        self.assertTrue(any("Kosten" in b for b in entry_blockers(compute(cs), len(cs) - 1, cfg)))


class StrategyTests(unittest.TestCase):
    def test_cost_blocker_on_tiny_volatility(self):
        cs = sim_candles(400)
        cfg = Config(source="sim", fee_pct=2.0)
        d = compute(cs)
        self.assertTrue(any("Kosten" in b for b in entry_blockers(d, len(cs) - 1, cfg)))

    def test_score_bounds(self):
        cs = sim_candles(600)
        d = compute(cs)
        cfg = Config(source="sim")
        for i in range(WARMUP, len(cs)):
            s = make_signal("X", d, i, cfg, {"fear_greed": 10, "funding": 0.001, "btc_trend": -1})
            self.assertTrue(-100 <= s.score <= 100)
            self.assertLess(s.stop, s.price)
            self.assertGreater(s.take_profit, s.price)


class BacktestTests(unittest.TestCase):
    def test_backtest_runs_and_is_consistent(self):
        cs = sim_candles(1200)
        r = run_backtest(cs, Config(source="sim"), "ETH")
        net = sum(t.pnl for t in r["trades"])
        self.assertAlmostEqual(r["end_equity"], 50 + net, delta=0.01)
        self.assertLessEqual(r["max_drawdown_pct"], 0)

    def test_walk_forward(self):
        res = walk_forward(sim_candles(1500, "SOL"), Config(source="sim"), "SOL", min_trades=1)
        for r in res:
            self.assertIn("test", r)


class ConfigTests(unittest.TestCase):
    def test_unknown_key_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"risk_per_trade": 5}, fh)
        try:
            with self.assertRaises(ValueError):
                load_config(fh.name)
        finally:
            os.unlink(fh.name)

    def test_quote_defaults(self):
        self.assertEqual(Config(source="kraken").resolved_quote(), "EUR")
        self.assertEqual(Config(source="binance").resolved_quote(), "USDT")


class KrakenParsingTests(unittest.TestCase):
    def test_ohlc_parsing(self):
        fake = {"error": [], "result": {"XXBTZEUR": [[1700000000, "1", "2", "0.5", "1.5", "1.4", "10", 5]], "last": 1}}
        with mock.patch.object(data_mod, "http_json", return_value=fake) as m:
            cs = KrakenSource().candles("BTC", "EUR", 60, 10)
        self.assertEqual(m.call_args[0][1]["pair"], "XBTEUR")
        self.assertEqual(cs[0].c, 1.5)
        self.assertEqual(cs[0].v, 10.0)


if __name__ == "__main__":
    unittest.main()
