"""Text-based CLI for the James Opportunity System.

Commands mirror the domain: start a run, record evidence and hypotheses, build a
proposition, run the validation gate, decide, and export. There is deliberately
NO send command. Approval is recorded here; sending happens outside this engine,
by a human, after James approves (03X, 00 rule 13, 07).

Usage:
    python -m system.cli <command> [args]
    python -m system.cli --help
"""

from __future__ import annotations

import argparse
import sys

from . import models as M
from .db import DB
from . import export as X
from . import seed_profile as S


def _db(args) -> DB:
    return DB(args.db)


def cmd_init(args):
    with _db(args) as db:
        n = S.seed(db)
        facts = db.list_profile_facts()
        print(f"Database ready at {args.db}")
        print(f"Seeded {n} new profile facts; {len(facts)} active total.")


def cmd_profile(args):
    with _db(args) as db:
        for r in db.list_profile_facts():
            print(f"[{r['confidence']:6}] ({r['category']:11}) {r['claim']}")


def cmd_new_run(args):
    with _db(args) as db:
        rid = db.add_run(M.ResearchRun(question=args.question, lens=args.lens or ""))
        print(f"run_id={rid}")


def cmd_list_runs(args):
    with _db(args) as db:
        for r in db.list_runs():
            print(f"{r['id']}  [{r['status']}]  {r['question']}")


def cmd_evidence(args):
    with _db(args) as db:
        ev = M.Evidence(
            source_type=args.type, source_ref=args.ref, excerpt=args.excerpt,
            supports_claim=args.supports, reliability=args.reliability,
            accessed_at=args.accessed or M._now()[:10], notes=args.notes or "",
        )
        eid = db.add_evidence(ev)
        print(f"evidence_id={eid}")


def cmd_hypothesis(args):
    with _db(args) as db:
        hid = db.add_hypothesis(M.Hypothesis(statement=args.statement, run_id=args.run))
        print(f"hypothesis_id={hid}")


def cmd_proposition(args):
    """Add a proposition. Always starts at HYPOTHESIS. Use `validate` to attempt
    VALIDATED (the gate refuses if evidence/counterfactual/economics missing)."""
    econ = M.Economics(
        who_pays=args.who_pays or "", mechanism=args.mechanism or "",
        amount_range=args.amount or "", timing=args.timing or "",
        james_costs=args.costs or "", net_estimate=args.net or "",
        basis=args.basis or "", estimate=not args.confirmed,
    )
    with _db(args) as db:
        prop = M.Proposition(
            title=args.title, arrangement=args.arrangement, james_role=args.role,
            value_to_them=args.value, counterfactual=args.counterfactual,
            run_id=args.run, economics=econ,
            uncertainties=args.uncertainties or "", invalidators=args.invalidators or "",
            next_step=args.next_step or "",
        )
        pid = db.add_proposition(prop)
        for eid in (args.evidence or []):
            db.link_evidence(pid, eid)
        print(f"proposition_id={pid}  status=HYPOTHESIS")
        if args.evidence:
            print(f"linked {len(args.evidence)} evidence record(s).")


def cmd_link(args):
    with _db(args) as db:
        db.link_evidence(args.proposition, args.evidence)
        print(f"linked {args.evidence} -> {args.proposition}")


def cmd_validate(args):
    """Attempt VALIDATED. Prints what's missing if the gate refuses. This is the
    anti-fabrication check made visible (tests H, J, U)."""
    with _db(args) as db:
        prop = db.get_proposition(args.proposition)
        if prop is None:
            print(f"no proposition {args.proposition}"); sys.exit(1)
        ok, missing = M.validate_proposition(prop, len(db.evidence_for(prop.id)))
        if ok:
            db.set_proposition_status(prop.id, "VALIDATED")
            print(f"VALIDATED: {prop.id} - {prop.title}")
        else:
            print(f"NOT VALIDATED: {prop.id}")
            print("Missing:")
            for m in missing:
                print(f"  - {m}")


def cmd_decide(args):
    with _db(args) as db:
        did = db.add_decision(M.Decision(
            decision=args.decision, reasoning=args.reasoning, run_id=args.run,
            proposition_id=args.proposition or "",
        ))
        if args.proposition:
            status = {
                "PURSUE": "VALIDATED", "DEVELOP": "DEVELOP",
                "RESEARCH_MORE": "HYPOTHESIS", "REJECT": "REJECTED",
                "PAUSE": "PAUSED", "STOP": "REJECTED",
            }.get(args.decision)
            if status:
                try:
                    db.set_proposition_status(args.proposition, status, args.reasoning)
                except ValueError as e:
                    print(f"note: status not changed ({e})")
        print(f"decision_id={did}")


def cmd_approve(args):
    """Record James's approval. The ONLY thing that later permits SENT. Sends
    nothing."""
    with _db(args) as db:
        aid = db.add_approval(M.Approval(
            approved_by=args.by, scope=args.scope, proposition_id=args.proposition,
            channel=args.channel or "", notes=args.notes or "",
        ))
        print(f"approval_id={aid} (recorded; nothing sent)")


def cmd_show(args):
    with _db(args) as db:
        if args.run:
            print(X.run_md(db, args.run))


def cmd_export(args):
    with _db(args) as db:
        md, js = X.export_run(db, args.run, outdir=args.outdir)
        print(f"wrote {md}")
        print(f"wrote {js}")


def cmd_list_props(args):
    with _db(args) as db:
        for p in db.list_propositions(run_id=args.run or "", status=args.status or ""):
            print(f"{p.id}  [{p.status:10}]  {p.title}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="james-opportunity-system",
                                description="Opportunity Intelligence Engine (no send).")
    p.add_argument("--db", default="opportunities.db", help="SQLite path")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("profile").set_defaults(func=cmd_profile)

    sp = sub.add_parser("new-run"); sp.add_argument("question"); sp.add_argument("--lens", default="")
    sp.set_defaults(func=cmd_new_run)

    sub.add_parser("list-runs").set_defaults(func=cmd_list_runs)

    sp = sub.add_parser("evidence")
    sp.add_argument("--type", required=True); sp.add_argument("--ref", required=True)
    sp.add_argument("--excerpt", required=True); sp.add_argument("--supports", required=True)
    sp.add_argument("--reliability", default="UNVERIFIED", choices=M.RELIABILITY)
    sp.add_argument("--accessed", default=""); sp.add_argument("--notes", default="")
    sp.set_defaults(func=cmd_evidence)

    sp = sub.add_parser("hypothesis"); sp.add_argument("--run", required=True); sp.add_argument("statement")
    sp.set_defaults(func=cmd_hypothesis)

    sp = sub.add_parser("proposition")
    sp.add_argument("--run", required=True); sp.add_argument("--title", required=True)
    sp.add_argument("--arrangement", required=True); sp.add_argument("--role", required=True)
    sp.add_argument("--value", required=True); sp.add_argument("--counterfactual", required=True)
    sp.add_argument("--who-pays", default=""); sp.add_argument("--mechanism", default="")
    sp.add_argument("--amount", default=""); sp.add_argument("--timing", default="")
    sp.add_argument("--costs", default=""); sp.add_argument("--net", default="")
    sp.add_argument("--basis", default=""); sp.add_argument("--confirmed", action="store_true")
    sp.add_argument("--uncertainties", default=""); sp.add_argument("--invalidators", default="")
    sp.add_argument("--next-step", default=""); sp.add_argument("--evidence", nargs="*", default=[])
    sp.set_defaults(func=cmd_proposition)

    sp = sub.add_parser("link"); sp.add_argument("--proposition", required=True); sp.add_argument("--evidence", required=True)
    sp.set_defaults(func=cmd_link)

    sp = sub.add_parser("validate"); sp.add_argument("--proposition", required=True)
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser("decide"); sp.add_argument("--run", required=True)
    sp.add_argument("--decision", required=True, choices=M.DECISION_TYPES)
    sp.add_argument("--reasoning", required=True); sp.add_argument("--proposition", default="")
    sp.set_defaults(func=cmd_decide)

    sp = sub.add_parser("approve"); sp.add_argument("--proposition", required=True)
    sp.add_argument("--by", default="James"); sp.add_argument("--scope", required=True)
    sp.add_argument("--channel", default=""); sp.add_argument("--notes", default="")
    sp.set_defaults(func=cmd_approve)

    sp = sub.add_parser("show"); sp.add_argument("--run", required=True)
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("export"); sp.add_argument("--run", required=True); sp.add_argument("--outdir", default="runs")
    sp.set_defaults(func=cmd_export)

    sp = sub.add_parser("list-props"); sp.add_argument("--run", default=""); sp.add_argument("--status", default="")
    sp.set_defaults(func=cmd_list_props)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

