# James Opportunity System — Prototype (Phase 2)

An **Opportunity Intelligence Engine** for James Litan. It discovers, constructs,
validates and positions opportunities, and works out how James could credibly
earn from them. It is **not** a job finder, lead generator, or email writer.

**Outreach is optional; discovery is non-negotiable. This engine contains no code
path that sends anything.** Recording an approval is the furthest it goes. Sending
is a human action, after James explicitly approves (docs `03X`, `00` rule 13,
`03`, `07`).

## The one rule the code enforces

A proposition cannot reach `VALIDATED` unless it has (1) at least one linked
evidence record, (2) a real counterfactual, and (3) a complete economics block
(who pays + mechanism). It cannot reach `SENT` without a linked Approval from
James. Fabrication is made structurally hard, not just discouraged.

## Layout

```
system/
  models.py        # domain: ProfileFact, Evidence, Hypothesis, Economics,
                   #   Proposition, ResearchRun, Decision, Approval + the gate
  db.py            # SQLite persistence + CRUD; enforces the validation gate
  cli.py           # text interface (no send command exists)
  export.py        # Markdown + JSON export per run (version-control friendly)
  seed_profile.py  # loads James's profile from doc 02 with provenance
tests/
  smoke_test.py    # end-to-end test (17 assertions)
```

## Run it

All commands need `PYTHONPATH=.` (the package is not installed).

```bash
PYTHONPATH=. python3 -m system.cli --db opportunities.db init      # create + seed profile
PYTHONPATH=. python3 -m system.cli --db opportunities.db profile   # view James's facts
PYTHONPATH=. python3 -m system.cli --db opportunities.db new-run "Your research question" --lens some-lens
PYTHONPATH=. python3 -m system.cli --db opportunities.db evidence --type hiring --ref URL \
    --excerpt "what it says" --supports "the claim it supports" --reliability HIGH
PYTHONPATH=. python3 -m system.cli --db opportunities.db hypothesis --run RUN_ID "a testable idea"
PYTHONPATH=. python3 -m system.cli --db opportunities.db proposition --run RUN_ID \
    --title "..." --arrangement "..." --role "..." --value "..." --counterfactual "..." \
    --who-pays "..." --mechanism retainer --amount "..." --evidence EV_ID [EV_ID ...]
PYTHONPATH=. python3 -m system.cli --db opportunities.db validate --proposition PROP_ID
PYTHONPATH=. python3 -m system.cli --db opportunities.db decide --run RUN_ID --decision PURSUE --reasoning "..." --proposition PROP_ID
PYTHONPATH=. python3 -m system.cli --db opportunities.db export --run RUN_ID --outdir runs
```

`approve` records James's approval (the only thing that later permits `SENT`). It
sends nothing. There is no send command.

## Test it

```bash
PYTHONPATH=. python3 tests/smoke_test.py
```

Expected: 17 `ok:` lines, then `ALL SMOKE TESTS PASSED`.

## What "good" looks like

See `04A_DISCOVERY_IN_ACTION_EXAMPLE.md` (a model of strong discovery) and
`04B_WHAT_FABRICATION_REVEALS.md` (the anti-patterns to catch). A strong run
produces an evidence-backed proposition with a tested counterfactual and
researched economics. A run that ends in a reasoned REJECT or STOP is a success.
