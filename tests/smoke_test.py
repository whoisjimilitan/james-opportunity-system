"""End-to-end smoke test for the prototype. Runs entirely in-process.

Exercises: init/seed, profile, a discovery run, evidence, competing hypotheses,
a proposition, the validation gate (refuse when incomplete, pass when complete),
export to Markdown + JSON, persistence across a fresh DB handle (restart), the
approval gate (SENT requires James approval), and the "no send" guarantee.

Run: PYTHONPATH=. python3 tests/smoke_test.py   (exit 0 = all passed)
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system import models as M
from system.db import DB
from system import export as X
from system import seed_profile as S


def check(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    print(f"ok: {msg}")


def main():
    tmp = tempfile.mkdtemp(prefix="jos_test_")
    dbpath = os.path.join(tmp, "test.db")

    with DB(dbpath) as db:
        n = S.seed(db)
        check(n >= 20, f"seeded profile ({n} facts)")
        facts = db.list_profile_facts()
        check(any("CPI" in f["claim"] or "brand" in f["claim"] for f in facts),
              "accuracy boundary present as a constraint")

        rid = db.add_run(M.ResearchRun(
            question="What arrangement could James become relevant to in West African "
                     "crisis-intervention training?",
            lens="training-market"))
        check(bool(rid), "run created")

        h1 = db.add_hypothesis(M.Hypothesis(
            statement="Org expanding to West Africa needs facilitator delivery quality.",
            run_id=rid))
        h2 = db.add_hypothesis(M.Hypothesis(
            statement="Org already has an in-house training program; no gap exists.",
            run_id=rid))
        check(len(db.list_hypotheses(rid)) == 2, "two competing hypotheses recorded")

        e1 = db.add_evidence(M.Evidence(
            source_type="hiring", source_ref="example-org.org/careers",
            excerpt="Regional Director, Africa (new role, Accra-based)",
            supports_claim="Org is committed to West Africa delivery",
            reliability="MEDIUM"))
        e2 = db.add_evidence(M.Evidence(
            source_type="case_study", source_ref="example-org.org/case-studies/ghana",
            excerpt="UK-Ghana partnership delivered with local facilitators",
            supports_claim="They rely on local facilitators for delivery",
            reliability="HIGH"))
        check(bool(e1) and bool(e2), "two evidence records created")

        # incomplete proposition (empty counterfactual + no economics)
        bad = M.Proposition(
            title="Facilitator for Ghana", arrangement="Deliver their curriculum in Ghana",
            james_role="Local facilitator", value_to_them="Local delivery capacity",
            counterfactual="", run_id=rid)
        bad_id = db.add_proposition(bad)
        db.link_evidence(bad_id, e1)

        ok, missing = M.validate_proposition(bad, len(db.evidence_for(bad_id)))
        check(not ok and any("counterfactual" in m for m in missing),
              "gate refuses incomplete proposition (counterfactual missing)")
        try:
            db.set_proposition_status(bad_id, "VALIDATED")
            check(False, "VALIDATED should have raised")
        except ValueError as e:
            check("cannot mark VALIDATED" in str(e), "set_proposition_status blocks VALIDATED")

        # complete proposition
        good = M.Proposition(
            title="Training-of-trainers lead for first Ghana cohort",
            arrangement="3-day structured prep for local facilitators before first live delivery",
            james_role="Designs and delivers facilitator preparation (UK training + West African context)",
            value_to_them="First market succeeds predictably instead of hit-or-miss",
            counterfactual="Without him, facilitators get materials only and delivery quality varies; with him, prep is systematic",
            run_id=rid,
            economics=M.Economics(
                who_pays="The expanding org (has expansion budget)",
                mechanism="retainer",
                amount_range="EUR 15-25K over 6 months (estimate)",
                timing="monthly retainer",
                james_costs="~EUR 5K travel/accommodation",
                net_estimate="EUR 15-20K net over 6 months",
                basis="comparable training-coordination rates in the region",
                estimate=True),
            uncertainties="Whether they have identified facilitator-prep as a gap",
            invalidators="They already run an in-house training program",
            next_step="30-min conversation with the Regional Director")
        good_id = db.add_proposition(good)
        db.link_evidence(good_id, e1)
        db.link_evidence(good_id, e2)

        ok, missing = M.validate_proposition(good, len(db.evidence_for(good_id)))
        check(ok, f"gate passes complete proposition (missing={missing})")
        db.set_proposition_status(good_id, "VALIDATED")
        check(db.get_proposition(good_id).status == "VALIDATED", "proposition is VALIDATED")

        db.add_decision(M.Decision(
            decision="PURSUE", reasoning="Evidence supports expansion + facilitator reliance; role credible.",
            run_id=rid, proposition_id=good_id))
        db.add_decision(M.Decision(
            decision="REJECT", reasoning="h2 (in-house program exists) kept as a live falsifier to test in conversation.",
            run_id=rid))

        # approval gate: SENT without approval must fail
        try:
            db.set_proposition_status(good_id, "SENT")
            check(False, "SENT should require approval")
        except ValueError as e:
            check("linked Approval" in str(e), "SENT blocked without approval")

        try:
            db.add_approval(M.Approval(
                approved_by="someone else", scope="x", proposition_id=good_id))
            check(False, "non-James approver should be rejected")
        except ValueError:
            check(True, "only James can approve")

        db.add_approval(M.Approval(
            approved_by="James", scope=f"proposition {good_id}, contact Regional Director",
            proposition_id=good_id, channel="email"))
        db.set_proposition_status(good_id, "SENT", "James approved 1:1 conversation ask")
        check(db.get_proposition(good_id).status == "SENT", "SENT works after James approval")

        md, js = X.export_run(db, rid, outdir=os.path.join(tmp, "runs"))
        md_text = md.read_text()
        check("Training-of-trainers" in md_text and "counterfactual" in md_text.lower(),
              "markdown export contains proposition + counterfactual")
        check("EUR 15-25K" in md_text, "markdown export contains researched economics")

    # persistence across restart
    with DB(dbpath) as db2:
        props = db2.list_propositions()
        check(len(props) == 2, "propositions survive restart")
        check(any(p.status == "SENT" for p in props), "status survives restart")
        check(len(db2.list_approvals()) == 1, "approval survives restart")

    print("\nALL SMOKE TESTS PASSED")
    print(f"(test db + exports under {tmp})")


if __name__ == "__main__":
    main()

