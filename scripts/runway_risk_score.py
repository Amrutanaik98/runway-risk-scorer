#!/usr/bin/env python3
"""
runway_risk_score.py  —  AI-vendor runway-risk scorer (DRAFT prototype)

Snickerdoodle labor separation (P1):
  AI executes: fetch verified signals, compute five MECHANICAL metrics, draft a sourced brief.
  Human decides: whether the runway risk is acceptable for procurement.
The script therefore STOPS at an explicit human gate. It never prints a
buy/avoid verdict — that is a judgment, not a computation (P1).

Provenance (P3): every metric carries the signal_ids and source_urls it was
derived from. No number is invented; missing data is reported as missing.

Input: a JSON array of signals matching data/verified/ai_company_signals-schema.yaml
Output: a per-company risk brief (human-readable) written to stdout, plus a
        machine log line. Halts at the gate.

Usage:
    python3 runway_risk_score.py sample_signals.json
    python3 runway_risk_score.py sample_signals.json --company harbor-ai
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, datetime

# ---- The five mechanical metrics this recipe is responsible for -------------
# 1. total_raised            — sum of funding_round values, in $
# 2. months_since_last_raise — recency of the most recent funding event
# 3. funding_stage_trend     — ordered stage progression (or stall)
# 4. distress_indicators     — count of layoff / security_issue / exec-change signals
# 5. signal_freshness        — age of the most recent validated signal of any kind
# None of these decides anything. They are inputs a human weighs at the gate.

STAGE_ORDER = [
    "pre-seed", "seed", "series a", "series b",
    "series c", "series d", "series e", "series f",
]
DISTRESS_TYPES = {"layoff", "security_issue", "executive_change"}


def parse_money(value):
    """'$45M' -> 45_000_000. Returns (amount|None, note)."""
    if not value:
        return None, "no value field"
    v = value.strip().lower().replace("$", "").replace(",", "")
    mult = 1
    if v.endswith("b"):
        mult, v = 1_000_000_000, v[:-1]
    elif v.endswith("m"):
        mult, v = 1_000_000, v[:-1]
    elif v.endswith("k"):
        mult, v = 1_000, v[:-1]
    try:
        return float(v) * mult, "parsed"
    except ValueError:
        return None, f"unparseable value: {value!r}"


def months_between(d1, d2):
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def load_signals(path):
    with open(path) as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("expected a JSON array of signals")
    return data


def is_verified(sig):
    """P2/schema: only validated signals may inform the brief."""
    return sig.get("validated_by") not in (None, "")


def compute_metrics(company_id, signals, today):
    """Return a dict of the five metrics, each with provenance. No judgment."""
    used = [s for s in signals if is_verified(s)]
    dropped = [s for s in signals if not is_verified(s)]

    # 1. total_raised
    total = 0.0
    raise_prov = []
    parse_notes = []
    for s in used:
        if s.get("signal_type") == "funding_round":
            amt, note = parse_money(s.get("signal_value"))
            if amt is not None:
                total += amt
                raise_prov.append({"signal_id": s["signal_id"], "source_url": s["source_url"], "value": s["signal_value"]})
            else:
                parse_notes.append(f'{s["signal_id"]}: {note}')

    # 2. months_since_last_raise
    raise_dates = [
        (datetime.fromisoformat(s["occurred_date"]).date(), s)
        for s in used
        if s.get("signal_type") == "funding_round" and s.get("occurred_date")
    ]
    if raise_dates:
        last_dt, last_sig = max(raise_dates, key=lambda t: t[0])
        months_since = months_between(last_dt, today)
        recency_prov = {"signal_id": last_sig["signal_id"], "source_url": last_sig["source_url"], "date": last_dt.isoformat()}
    else:
        months_since, recency_prov = None, None

    # 3. funding_stage_trend
    stage_sigs = [s for s in used if s.get("signal_type") == "funding_stage" and s.get("signal_value")]
    stage_sigs.sort(key=lambda s: s.get("occurred_date") or "")
    stages = [s["signal_value"] for s in stage_sigs]
    stage_prov = [{"signal_id": s["signal_id"], "stage": s["signal_value"], "date": s.get("occurred_date")} for s in stage_sigs]

    # 4. distress_indicators
    distress = [s for s in used if s.get("signal_type") in DISTRESS_TYPES]
    distress_prov = [{"signal_id": s["signal_id"], "type": s["signal_type"], "title": s["signal_title"], "source_url": s["source_url"]} for s in distress]

    # 5. signal_freshness
    dated = [datetime.fromisoformat(s["occurred_date"]).date() for s in used if s.get("occurred_date")]
    freshness_days = (today - max(dated)).days if dated else None

    return {
        "company_id": company_id,
        "signals_used": len(used),
        "signals_dropped_unvalidated": len(dropped),
        "total_raised_usd": total if raise_prov else None,
        "total_raised_provenance": raise_prov,
        "parse_notes": parse_notes,
        "months_since_last_raise": months_since,
        "months_since_last_raise_provenance": recency_prov,
        "funding_stage_trend": stages,
        "funding_stage_provenance": stage_prov,
        "distress_indicator_count": len(distress),
        "distress_provenance": distress_prov,
        "signal_freshness_days": freshness_days,
    }


def render_brief(m):
    """Human-readable brief. Reports facts and provenance. Never a verdict."""
    L = []
    L.append(f"RUNWAY-RISK BRIEF — {m['company_id']}")
    L.append("=" * 52)
    L.append(f"Signals used (validated): {m['signals_used']}   dropped (unvalidated): {m['signals_dropped_unvalidated']}")
    L.append("")

    tr = m["total_raised_usd"]
    L.append(f"1. Total raised: {'$'+format(tr, ',.0f') if tr is not None else 'UNKNOWN (no validated funding_round signals)'}")
    for p in m["total_raised_provenance"]:
        L.append(f"     - {p['value']}  [{p['signal_id']}]  {p['source_url']}")
    for note in m["parse_notes"]:
        L.append(f"     ! {note}")

    ms = m["months_since_last_raise"]
    L.append(f"2. Months since last raise: {ms if ms is not None else 'UNKNOWN'}")
    if m["months_since_last_raise_provenance"]:
        p = m["months_since_last_raise_provenance"]
        L.append(f"     - last raise {p['date']}  [{p['signal_id']}]  {p['source_url']}")

    st = m["funding_stage_trend"]
    L.append(f"3. Funding-stage trend: {' -> '.join(st) if st else 'UNKNOWN'}")

    L.append(f"4. Distress indicators (layoff/security/exec-change): {m['distress_indicator_count']}")
    for p in m["distress_provenance"]:
        L.append(f"     - {p['type']}: {p['title']}  [{p['signal_id']}]  {p['source_url']}")

    fr = m["signal_freshness_days"]
    L.append(f"5. Most recent validated signal: {str(fr)+' days ago' if fr is not None else 'UNKNOWN'}")

    L.append("")
    L.append("-" * 52)
    L.append("HUMAN GATE (P1/P4) — not cleared by this script.")
    L.append("A named human must judge whether this runway risk is acceptable")
    L.append("for procurement and log the decision in logs/RUN_LOG.md.")
    L.append("This tool computed metrics. It did not decide anything.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("signals_path")
    ap.add_argument("--company", default=None, help="limit to one company_id")
    ap.add_argument("--today", default=date.today().isoformat(), help="override run date (ISO)")
    args = ap.parse_args()

    today = datetime.fromisoformat(args.today).date()
    signals = load_signals(args.signals_path)

    by_company = defaultdict(list)
    for s in signals:
        by_company[s.get("company_id")].append(s)

    targets = [args.company] if args.company else sorted(by_company)
    for c in targets:
        if c not in by_company:
            print(f"[skip] no signals for company_id={c!r}", file=sys.stderr)
            continue
        metrics = compute_metrics(c, by_company[c], today)
        print(render_brief(metrics))
        print()
        # machine log line (P5: log for agents, report for humans)
        print(f'[LOG] recipe=runway-risk company={c} used={metrics["signals_used"]} '
              f'dropped={metrics["signals_dropped_unvalidated"]} distress={metrics["distress_indicator_count"]} '
              f'gate=HALT-AWAITING-HUMAN', file=sys.stderr)


if __name__ == "__main__":
    main()
