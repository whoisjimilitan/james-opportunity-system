"""Seed the profile table from 02_JAMES_PROFILE_AND_TRUTH_BOUNDARIES.md.

Every fact carries provenance and confidence. The hard accuracy boundaries from
that doc are encoded here as *constraints the discovery must respect*, not as
claims. Run once; re-run is idempotent per claim text."""

from __future__ import annotations

from .db import DB
from . import models as M

SRC = "02_JAMES_PROFILE_AND_TRUTH_BOUNDARIES.md"

# (category, claim, confidence)
PROFILE = [
    ("identity", "James Olujimi Litan (James O. Litan).", "HIGH"),
    ("geography", "Based in Accra, Ghana.", "HIGH"),
    ("geography", "Canadian citizen.", "HIGH"),
    ("context", "Raised primarily in Nigeria, with time across several African countries; trained and worked in the UK; now in Ghana.", "HIGH"),
    ("constraint", "Willing to travel internationally for suitable opportunities; do not assume remote-only or Ghana-only.", "HIGH"),
    ("outcome", "Overriding objective: opportunities producing real income/revenue and profitable financial outcomes.", "HIGH"),
    ("capability", "Crisis intervention, safeguarding, therapeutic education, SEN support, family support, staff training.", "HIGH"),
    ("capability", "~4 years frontline UK therapeutic/educational experience: de-escalation, risk assessment, disclosure management.", "HIGH"),
    ("recognition", "CEO Award for Therapeutic Education, TCES 2025; selected company-wide across four TCES schools.", "HIGH"),
    ("context", "Therapeutic Education Practitioner, TCES London, 2023-2025.", "HIGH"),
    ("context", "Pastoral Support and Deputy Safeguarding Lead, TCES Create Learning Primary, 2022-2023 (disclosures, risk assessment, coordinated referrals).", "HIGH"),
    ("context", "Family Support Worker, TCES London, 2022-2023.", "HIGH"),
    ("context", "Higher Level Teaching Assistant SEN, Eko Pathways London, 2020-2022.", "HIGH"),
    ("capability", "Trained internally as Safety Intervention Facilitator at TCES 2024-2025; delivered crisis-prevention/de-escalation training to staff.", "HIGH"),
    ("credential", "Ofqual Level 3 Diploma in Therapeutic Childcare and Developmental Trauma, Crossfields Institute, Nov 2024.", "HIGH"),
    ("credential", "Diploma in Emotional Intelligence, Alison, July 2023.", "HIGH"),
    ("credential", "National Tutoring Programme, UK DfE/EDT, April 2022.", "HIGH"),
    # Boundaries encoded as constraints, so discovery treats them as limits:
    ("constraint", "Do NOT claim external certification from CPI, Mandt, Maybo, FranklinCovey, RedR or any brand unless newly verified.", "HIGH"),
    ("constraint", "Only defensible facilitator claim: trained internally at TCES and delivered to staff.", "HIGH"),
    ("constraint", "Do not name specific languages unless James confirms them.", "HIGH"),
    ("constraint", "Do not invent target-org facts, demand, relationships, buyer intent, budgets, or James's prior actions.", "HIGH"),
    ("constraint", "Canadian passport may ease entry; visitor entry is NOT permission to work/contract/earn. Verify destination rules.", "HIGH"),
]

CONTACT = ("relationship", "Email: whoisjimi.today@gmail.com. Use only with James's authority.", "MEDIUM")


def seed(db: DB) -> int:
    existing = {r["claim"] for r in db.list_profile_facts(active_only=False)}
    added = 0
    for category, claim, conf in PROFILE + [CONTACT]:
        if claim in existing:
            continue
        db.add_profile_fact(M.ProfileFact(
            claim=claim, category=category, source=SRC,
            confidence=conf, provenance=SRC,
        ))
        added += 1
    return added


if __name__ == "__main__":
    with DB() as db:
        n = seed(db)
        print(f"Seeded {n} profile facts "
              f"({len(db.list_profile_facts())} active total).")
