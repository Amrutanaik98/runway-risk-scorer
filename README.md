# runway-risk-scorer

A financial-signal recipe for the Mycroft system. It reads a company's
**validated** funding/financial signals and produces a **sourced runway-risk
brief**, then **halts at a human gate**. It computes the inputs to a judgment;
a human makes the judgment.

## Status
`DRAFT` → working toward `RUNNABLE-SAMPLE`. See `recipes/runway-risk-scorer.md`.

## Run the sample
```bash
python3 scripts/runway_risk_score.py data/samples/sample_signals.json
# single company:
python3 scripts/runway_risk_score.py data/samples/sample_signals.json --company harbor-ai
```
Output: a human-readable brief on stdout and a machine log line on stderr. The
script halts at the human gate and never issues a verdict.

## Layout
- `recipes/` — the recipe spec (frontmatter + steps + gate)
- `scripts/` — the runway scorer
- `data/samples/` — schema-matched synthetic signals (safe, offline)
- `data/verified/` — schema reference (the real schema lives upstream; see SCHEMA_REFERENCE.md)
- `logs/RUN_LOG.md` — run history (lifecycle evidence)
- `reports/` — generated briefs

## Relationship to upstream Mycroft
This is developed as a contribution to the Mycroft project. The upstream repo is
**all-rights-reserved**; this repo references its schema and governance rather
than redistributing them. Intended delivery is **fork + pull request** into the
upstream repo, not standalone publication. See `GOVERNANCE.md`.
