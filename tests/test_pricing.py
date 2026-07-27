"""Tests for rate resolution and per-entry cost.

This is money math driving a halt, so it gets tests. It shipped without them, and the defect
that hid in the gap was expensive in the most literal sense: rates were resolved by matching
`opus` as a substring of the model id, which priced every `claude-opus-5` session at Opus 4.1
rates. On a real 239-turn session that read $276.16 instead of $74.91 — a 3.69x over-estimate,
so a $10 session cap halted at roughly $2.71 of actual spend.

Run: python -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    """Import bin/cost-guard, which has no .py extension."""
    loader = importlib.machinery.SourceFileLoader("cost_guard", str(ROOT / "bin" / "cost-guard"))
    spec = importlib.util.spec_from_loader("cost_guard", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


cg = load()


def rates(model, **kw):
    return cg.model_rates(model, **kw)


class TestPerModelResolution(unittest.TestCase):
    def test_opus_5_is_not_priced_as_opus_4_1(self):
        """The regression. These two are 3x apart and used to share a tier."""
        self.assertEqual(rates("claude-opus-5")["input"], 5.0)
        self.assertEqual(rates("claude-opus-5")["output"], 25.0)
        self.assertEqual(rates("claude-opus-4-1")["input"], 15.0)

    def test_the_model_table_beats_the_tier_fallback(self):
        self.assertTrue(rates("claude-opus-5")["priced_by"].startswith("model:"))

    def test_a_dated_release_id_matches_its_family(self):
        r = rates("claude-haiku-4-5-20251001")
        self.assertEqual((r["input"], r["output"]), (1.0, 5.0))
        self.assertEqual(r["priced_by"], "model:claude-haiku-4-5")

    def test_the_longest_prefix_wins(self):
        """`claude-opus-4` must not capture `claude-opus-4-5-...`, or a $5 model bills at $15."""
        r = rates("claude-opus-4-5-20251101")
        self.assertEqual(r["priced_by"], "model:claude-opus-4-5")
        self.assertEqual(r["input"], 5.0)

    def test_an_unknown_model_falls_back_and_says_it_is_a_guess(self):
        r = rates("claude-opus-99")
        self.assertTrue(r["priced_by"].startswith("tier:"))
        self.assertIn("guess", r["priced_by"])

    def test_the_unknown_fallback_is_the_expensive_direction(self):
        """For a halt guard, over-estimating an unknown model fails safe; under-estimating lets
        a runaway loop through."""
        self.assertGreaterEqual(rates("claude-opus-99")["input"], rates("claude-opus-5")["input"])


class TestEffectiveDates(unittest.TestCase):
    """Pricing changes on dates, so a session must be priced by ITS OWN date — otherwise every
    historical report silently changes overnight."""

    def test_sonnet_5_introductory_pricing_before_september(self):
        r = rates("claude-sonnet-5", when=date(2026, 8, 31))
        self.assertEqual((r["input"], r["output"]), (2.0, 10.0))

    def test_sonnet_5_standard_pricing_from_september(self):
        r = rates("claude-sonnet-5", when=date(2026, 9, 1))
        self.assertEqual((r["input"], r["output"]), (3.0, 15.0))

    def test_an_open_ended_period_covers_any_date(self):
        for when in (date(2026, 1, 1), date(2027, 6, 30)):
            with self.subTest(when=when):
                self.assertEqual(rates("claude-opus-5", when=when)["input"], 5.0)


class TestFastMode(unittest.TestCase):
    def test_fast_mode_costs_double(self):
        self.assertEqual(rates("claude-opus-5", fast=True)["input"], 10.0)
        self.assertEqual(rates("claude-opus-5", fast=True)["output"], 50.0)

    def test_a_model_without_fast_pricing_ignores_the_flag(self):
        self.assertEqual(rates("claude-opus-4-7", fast=True)["input"],
                         rates("claude-opus-4-7")["input"])

    def test_speed_fast_in_usage_is_applied(self):
        usage = {"input_tokens": 1_000_000, "output_tokens": 0, "speed": "fast"}
        self.assertAlmostEqual(cg.entry_cost_usd(usage, "claude-opus-5"), 10.0, places=6)


class TestDerivedCacheRates(unittest.TestCase):
    """Cache prices are documented multipliers on base input, so only input+output are stored."""

    def test_multipliers_match_the_published_ratios(self):
        r = rates("claude-opus-5")
        self.assertAlmostEqual(r["cache_write_5m"], 5.0 * 1.25)
        self.assertAlmostEqual(r["cache_write_1h"], 5.0 * 2.0)
        self.assertAlmostEqual(r["cache_read"], 5.0 * 0.1)

    def test_a_cache_read_is_a_tenth_of_input(self):
        usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 1_000_000}
        self.assertAlmostEqual(cg.entry_cost_usd(usage, "claude-opus-5"), 0.5, places=6)

    def test_the_5m_and_1h_split_is_honoured(self):
        usage = {"cache_creation": {"ephemeral_5m_input_tokens": 1_000_000,
                                    "ephemeral_1h_input_tokens": 1_000_000}}
        self.assertAlmostEqual(cg.entry_cost_usd(usage, "claude-opus-5"), 6.25 + 10.0, places=6)


class TestModifiers(unittest.TestCase):
    """All three live in `usage` and were previously ignored — in both directions."""

    def test_us_inference_geo_adds_ten_percent(self):
        usage = {"input_tokens": 1_000_000, "inference_geo": "us"}
        self.assertAlmostEqual(cg.entry_cost_usd(usage, "claude-opus-5"), 5.5, places=6)

    def test_global_inference_geo_is_unmodified(self):
        usage = {"input_tokens": 1_000_000, "inference_geo": "global"}
        self.assertAlmostEqual(cg.entry_cost_usd(usage, "claude-opus-5"), 5.0, places=6)

    def test_web_search_is_billed_per_request_not_per_token(self):
        usage = {"server_tool_use": {"web_search_requests": 100}}
        self.assertAlmostEqual(cg.entry_cost_usd(usage, "claude-opus-5"), 1.0, places=6)

    def test_an_empty_usage_costs_nothing(self):
        self.assertEqual(cg.entry_cost_usd({}, "claude-opus-5"), 0.0)


class TestStaleness(unittest.TestCase):
    def test_the_committed_table_is_not_stale(self):
        self.assertFalse(cg.pricing_is_stale(),
                         "pricing.json is past max_age_days — run refresh-pricing")

    def test_age_is_reported_in_days(self):
        self.assertIsNotNone(cg.pricing_age_days())
        self.assertGreaterEqual(cg.pricing_age_days(), 0)

    def test_an_old_last_verified_reads_as_stale(self):
        original = cg._PRICING
        try:
            old = (datetime.now().date() - timedelta(days=999)).isoformat()
            cg._PRICING = {"_metadata": {"last_verified": old, "max_age_days": 45}}
            self.assertTrue(cg.pricing_is_stale())
        finally:
            cg._PRICING = original


class TestTableIntegrity(unittest.TestCase):
    def test_every_model_has_at_least_one_period_with_both_rates(self):
        table = json.loads((ROOT / "pricing.json").read_text(encoding="utf-8"))
        for name, entry in table["models"].items():
            with self.subTest(model=name):
                periods = entry.get("periods") or []
                self.assertTrue(periods, "%s has no periods" % name)
                for p in periods:
                    self.assertIn("input", p)
                    self.assertIn("output", p)

    def test_output_is_never_cheaper_than_input(self):
        """A transposed pair would silently under-bill the expensive half of every turn."""
        table = json.loads((ROOT / "pricing.json").read_text(encoding="utf-8"))
        for name, entry in table["models"].items():
            for p in entry.get("periods") or []:
                with self.subTest(model=name):
                    self.assertGreater(p["output"], p["input"])

    def test_dated_periods_do_not_overlap(self):
        table = json.loads((ROOT / "pricing.json").read_text(encoding="utf-8"))
        for name, entry in table["models"].items():
            periods = [p for p in entry.get("periods") or [] if p.get("from") or p.get("to")]
            if len(periods) < 2:
                continue
            with self.subTest(model=name):
                # Every date in a wide window must resolve to exactly one period.
                for offset in range(0, 800, 7):
                    when = date(2026, 1, 1) + timedelta(days=offset)
                    hits = [p for p in entry["periods"] if cg._period_for([p], when)]
                    self.assertLessEqual(len(hits), 1,
                                         "%s: %s matches %d periods" % (name, when, len(hits)))


if __name__ == "__main__":
    unittest.main()
