## 2026-08-21 — Week 2 sample run (step-split + JSON output)
- command: python scripts\runway_risk_score.py data\samples\sample_signals.json --json-out reports
- result: 4 companies scored. harbor-ai used 3 signals (1 distress, 93 days fresh);
  lumen-labs used 2 (0 distress, 1684 days fresh — stale); vela-systems used 3
  (0 distress, 37 days fresh); orphan-co used 0, dropped 1 unvalidated signal.
  JSON written to reports\ (4 files). All briefs halted at the human gate. Exit 0.
- steps confirmed: ingest -> validate_shape (drops unvalidated) -> score -> report(human + JSON).
- gate decision: acting-reviewer SOLO — run confirms the step-split produces the
  same briefs as Week 1 and the JSON carries full provenance. Adequate to mark SPECIFIED.
- could NOT verify (solo): real-world accuracy of the signals, whether the 5 metrics
  match actual procurement needs, independent adequacy review.