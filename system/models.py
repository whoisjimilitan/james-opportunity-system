"""Domain model for the James Opportunity System.

The primary unit of work is a *Proposition*: a possible arrangement with
evidence, a role for James, tested economics and an explicit counterfactual.
Everything else exists to support, evidence, or record the fate of a
proposition. Outreach (an email) is never a required output.

Truth boundaries (from 02_JAMES_PROFILE_AND_TRUTH_BOUNDARIES.md and 00):
- No invented facts. Every claim links to Evidence with provenance.
- Counterfactual is mandatory: what changes if James is removed.
- Economics must be researched, not guessed. Absent evidence => flag it.
- A Proposition cannot reach VALIDATED without evidence + counterfactual +
  an economics block. Fabrication is made structurally hard, not just
  discouraged.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# --- Status vocabularies (single source of truth) ---------------------------

PROPOSITION_STATUS = [
    "HYPOTHESIS",     # idea, evidence not yet sufficient
    "VALIDATED",      # evidence + counterfactual + economics all present
    "DEVELOP",        # real, but James must acquire a capability first
    "REJECTED",       # evidence contradicts it; reason recorded (kept forever)
    "PAUSED",         # real, timing wrong; awaiting a signal
    "SENT",           # requires a linked approval entry
    "REPLIED",
    "CONVERTED",
]

RUN_STATUS = ["OPEN", "CLOSED"]

DECISION_TYPES = [
    "PURSUE",         # evidence strong, proceed toward activation
    "DEVELOP",        # James needs a credential/relationship first
    "RESEARCH_MORE",  # hypothesis, missing critical evidence
    "REJECT",         # evidence contradicts; disconfirm kept
    "PAUSE",          # timing; monitor for a reopening signal
    "STOP",           # diminishing returns; a successful stop
]

RELIABILITY = ["HIGH", "MEDIUM", "LOW", "UNVERIFIED"]

SOURCE_TYPES = [
    "announcement", "hiring", "case_study", "annual_report", "news",
    "job_post", "rfp", "conversation", "org_website", "registry",
    "social_post", "other",
]


# --- Domain records ---------------------------------------------------------

@dataclass
class ProfileFact:
    """A durable, provenance-tracked fact about James.

    category: capability | credential | recognition | context | constraint |
              geography | preference | relationship | development | outcome
    """
    claim: str
    category: str
    source: str
    confidence: str = "MEDIUM"          # HIGH/MEDIUM/LOW
    provenance: str = "02_JAMES_PROFILE_AND_TRUTH_BOUNDARIES.md"
    active: bool = True
    id: str = field(default_factory=lambda: _id("pf"))
    recorded_at: str = field(default_factory=_now)


@dataclass
class Evidence:
    """An attributable, dated piece of evidence supporting (or against) a claim.

    Every claim in a Proposition must trace to one of these. reliability and
    accessed_at exist so the reader can judge how much to trust it.
    """
    source_type: str
    source_ref: str            # URL, document name, or 'conversation with X'
    excerpt: str               # what it actually says (short)
    supports_claim: str        # the specific claim this evidences
    reliability: str = "UNVERIFIED"
    accessed_at: str = field(default_factory=lambda: _now()[:10])
    notes: str = ""
    id: str = field(default_factory=lambda: _id("ev"))
    recorded_at: str = field(default_factory=_now)


@dataclass
class Hypothesis:
    """A competing, testable idea within a run. Multiple per run is the norm."""
    statement: str
    run_id: str
    status: str = "OPEN"       # OPEN | TESTING | SUPPORTED | REFUTED
    reasoning: str = ""
    id: str = field(default_factory=lambda: _id("hyp"))
    recorded_at: str = field(default_factory=_now)


@dataclass
class Economics:
    """Researched economics for a proposition (00: the financial north star).

    None of these may be guessed. If evidence is missing, set the field to a
    best-effort estimate AND set estimate=True with a basis note. A blank
    who_pays/mechanism keeps a proposition at HYPOTHESIS.
    """
    who_pays: str = ""
    mechanism: str = ""            # salary | day_rate | retainer | project_fee |
                                  # commission | revenue_share | referral | hybrid
    amount_range: str = ""         # e.g. "EUR 15-25K total"
    timing: str = ""               # when payment occurs
    james_costs: str = ""          # what James spends/risks
    net_estimate: str = ""         # gross minus costs
    basis: str = ""                # the evidence/method behind the numbers
    estimate: bool = True          # True until confirmed by a real source

    def complete(self) -> bool:
        return bool(self.who_pays.strip() and self.mechanism.strip())


@dataclass
class Proposition:
    """The primary unit of work. Cannot reach VALIDATED without evidence,
    a counterfactual, and a complete economics block (enforced in db.py)."""
    title: str
    arrangement: str               # what concretely happens
    james_role: str                # what James specifically does
    value_to_them: str             # the concrete gain for the other party
    counterfactual: str            # what changes if James is removed (mandatory)
    run_id: str
    economics: Economics = field(default_factory=Economics)
    uncertainties: str = ""        # known unknowns, explicit
    invalidators: str = ""         # what would disprove it
    next_step: str = ""            # smallest proportionate step
    status: str = "HYPOTHESIS"
    decision_reasoning: str = ""
    id: str = field(default_factory=lambda: _id("prop"))
    recorded_at: str = field(default_factory=_now)


@dataclass
class ResearchRun:
    """One discovery exercise. Holds many hypotheses and many propositions.
    A run's decision is recorded explicitly; stopping/REJECT is a success."""
    question: str
    lens: str = ""                 # the discovery lens used (from D2-style taxonomy)
    status: str = "OPEN"
    summary: str = ""              # what was newly discovered, what's speculative
    id: str = field(default_factory=lambda: _id("run"))
    recorded_at: str = field(default_factory=_now)


@dataclass
class Decision:
    """The explicit outcome of a run or a proposition. Preserved forever,
    including REJECT/STOP, so the learning compounds (00 rule 14)."""
    decision: str                  # PURSUE | DEVELOP | RESEARCH_MORE | REJECT | PAUSE | STOP
    reasoning: str
    run_id: str
    proposition_id: str = ""
    id: str = field(default_factory=lambda: _id("dec"))
    recorded_at: str = field(default_factory=_now)


@dataclass
class Approval:
    """The ONLY thing that permits a SENT status. A proposition cannot be
    marked SENT without a linked Approval naming who approved and when.
    There is no code path that sends anything (03X, 00 rule 13, 07)."""
    approved_by: str               # must be James
    scope: str                     # what exactly was approved (prop + contact)
    proposition_id: str
    channel: str = ""              # email | linkedin | intro | other
    notes: str = ""
    id: str = field(default_factory=lambda: _id("appr"))
    approved_at: str = field(default_factory=_now)


# --- Validation gate (the anti-fabrication enforcement) ---------------------

def validate_proposition(prop: Proposition, evidence_count: int) -> tuple[bool, list[str]]:
    """Return (ok, missing). A proposition may reach VALIDATED only if it has
    at least one linked evidence record, a real counterfactual, and a complete
    economics block. Missing items are named so the gap is explicit (test H,
    U). This makes fabrication structurally hard rather than discouraged."""
    missing: list[str] = []
    if evidence_count < 1:
        missing.append("at least one linked Evidence record")
    if not prop.counterfactual.strip():
        missing.append("a counterfactual (what changes if James is removed)")
    if not prop.economics.complete():
        missing.append("a complete economics block (who_pays + mechanism)")
    if not prop.value_to_them.strip():
        missing.append("the concrete value to the other party")
    if not prop.james_role.strip():
        missing.append("James's specific, credible role")
    return (len(missing) == 0), missing


def to_json(obj) -> str:
    return json.dumps(asdict(obj), indent=2, ensure_ascii=False)


