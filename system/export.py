"""Export a run to Markdown + JSON so discoveries are version-control friendly
and survive outside the database (03: portable; CLINE_BUILD_INSTRUCTIONS: save
to GitHub, not just memory)."""

from __future__ import annotations

import json
from pathlib import Path

from . import models as M
from .db import DB


def _econ_md(e: M.Economics) -> str:
    lines = [
        f"- Who pays: {e.who_pays or '(unfilled)'}",
        f"- Mechanism: {e.mechanism or '(unfilled)'}",
        f"- Amount range: {e.amount_range or '(unfilled)'}",
        f"- Timing: {e.timing or '(unfilled)'}",
        f"- James's costs: {e.james_costs or '(unfilled)'}",
        f"- Net estimate: {e.net_estimate or '(unfilled)'}",
        f"- Basis: {e.basis or '(none given)'}",
        f"- Estimate (not confirmed): {e.estimate}",
    ]
    return "\n".join(lines)


def proposition_md(db: DB, prop: M.Proposition) -> str:
    ev = db.evidence_for(prop.id)
    out = [f"### {prop.title}  [{prop.status}]", ""]
    out += [
        f"- **Arrangement:** {prop.arrangement}",
        f"- **James's role:** {prop.james_role}",
        f"- **Value to them:** {prop.value_to_them}",
        f"- **Counterfactual (what changes if James removed):** {prop.counterfactual or '(MISSING)'}",
        "",
        "**Economics**",
        _econ_md(prop.economics),
        "",
        f"- **Uncertainties:** {prop.uncertainties or '(none stated)'}",
        f"- **What would invalidate it:** {prop.invalidators or '(none stated)'}",
        f"- **Smallest next step:** {prop.next_step or '(none stated)'}",
        "",
        f"**Evidence ({len(ev)} linked):**",
    ]
    if not ev:
        out.append("- (none linked)")
    for e in ev:
        out.append(
            f"- [{e['reliability']}] {e['source_type']} — {e['source_ref']} "
            f"(accessed {e['accessed_at']}): \"{e['excerpt']}\" "
            f"→ supports: {e['supports_claim']}"
        )
    out.append("")
    return "\n".join(out)


def run_md(db: DB, run_id: str) -> str:
    run = db.get_run(run_id)
    if run is None:
        raise ValueError(f"no run {run_id}")
    props = db.list_propositions(run_id=run_id)
    hyps = db.list_hypotheses(run_id)
    decs = db.list_decisions(run_id)
    out = [
        f"# Discovery Run: {run['id']}",
        "",
        f"**Question:** {run['question']}",
        f"**Lens:** {run['lens'] or '(none)'}",
        f"**Status:** {run['status']}",
        f"**Recorded:** {run['recorded_at']}",
        "",
    ]
    if run["summary"]:
        out += [f"**Summary:** {run['summary']}", ""]
    out += ["## Hypotheses", ""]
    for h in hyps:
        out.append(f"- [{h['status']}] {h['statement']}")
    if not hyps:
        out.append("- (none recorded)")
    out += ["", "## Propositions", ""]
    for p in props:
        out.append(proposition_md(db, p))
    if not props:
        out.append("- (none recorded)")
    out += ["## Decisions", ""]
    for d in decs:
        tag = d["proposition_id"] or "(run-level)"
        out.append(f"- [{d['decision']}] ({tag}) {d['reasoning']}")
    if not decs:
        out.append("- (none recorded)")
    out.append("")
    return "\n".join(out)


def run_json(db: DB, run_id: str) -> str:
    run = dict(db.get_run(run_id))
    data = {
        "run": run,
        "hypotheses": [dict(h) for h in db.list_hypotheses(run_id)],
        "propositions": [],
        "decisions": [dict(d) for d in db.list_decisions(run_id)],
    }
    for p in db.list_propositions(run_id=run_id):
        pd = M.asdict(p)
        pd["evidence"] = [dict(e) for e in db.evidence_for(p.id)]
        data["propositions"].append(pd)
    return json.dumps(data, indent=2, ensure_ascii=False)


def export_run(db: DB, run_id: str, outdir: str | Path = "runs") -> tuple[Path, Path]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / f"{run_id}.md"
    json_path = out / f"{run_id}.json"
    md_path.write_text(run_md(db, run_id), encoding="utf-8")
    json_path.write_text(run_json(db, run_id), encoding="utf-8")
    return md_path, json_path
