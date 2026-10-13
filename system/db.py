"""SQLite persistence. Discoveries must survive restarts (03: persistent memory).

Design notes:
- JSON columns for the nested Economics block keep the schema small; the
  relational tables carry the audit trail (evidence links, approvals).
- evidence_links is a join table tying Evidence <-> Proposition so every claim
  in a proposition is traceable (00, 04).
- No table and no function sends anything. Approval is a record, not a trigger.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from . import models as M


SCHEMA = """
CREATE TABLE IF NOT EXISTS profile_facts (
    id TEXT PRIMARY KEY,
    claim TEXT NOT NULL,
    category TEXT NOT NULL,
    source TEXT NOT NULL,
    confidence TEXT NOT NULL,
    provenance TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_runs (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    lens TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN',
    summary TEXT,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    supports_claim TEXT NOT NULL,
    reliability TEXT NOT NULL,
    accessed_at TEXT NOT NULL,
    notes TEXT,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    statement TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    reasoning TEXT,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES research_runs(id)
);

CREATE TABLE IF NOT EXISTS propositions (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    title TEXT NOT NULL,
    arrangement TEXT NOT NULL,
    james_role TEXT NOT NULL,
    value_to_them TEXT NOT NULL,
    counterfactual TEXT NOT NULL,
    economics_json TEXT NOT NULL,
    uncertainties TEXT,
    invalidators TEXT,
    next_step TEXT,
    status TEXT NOT NULL DEFAULT 'HYPOTHESIS',
    decision_reasoning TEXT,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES research_runs(id)
);

CREATE TABLE IF NOT EXISTS evidence_links (
    proposition_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    PRIMARY KEY(proposition_id, evidence_id),
    FOREIGN KEY(proposition_id) REFERENCES propositions(id),
    FOREIGN KEY(evidence_id) REFERENCES evidence(id)
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    proposition_id TEXT,
    decision TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES research_runs(id)
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    proposition_id TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    scope TEXT NOT NULL,
    channel TEXT,
    notes TEXT,
    approved_at TEXT NOT NULL,
    FOREIGN KEY(proposition_id) REFERENCES propositions(id)
);
"""


class DB:
    def __init__(self, path: str | Path = "opportunities.db"):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.conn.close()

    # -- generic helpers ----------------------------------------------------
    def _insert(self, table: str, data: dict):
        cols = ", ".join(data.keys())
        ph = ", ".join("?" for _ in data)
        self.conn.execute(
            f"INSERT INTO {table} ({cols}) VALUES ({ph})", tuple(data.values())
        )
        self.conn.commit()

    def _rows(self, sql: str, args: tuple = ()):
        return self.conn.execute(sql, args).fetchall()

    # -- profile facts ------------------------------------------------------
    def add_profile_fact(self, pf: M.ProfileFact) -> str:
        self._insert("profile_facts", {
            "id": pf.id, "claim": pf.claim, "category": pf.category,
            "source": pf.source, "confidence": pf.confidence,
            "provenance": pf.provenance, "active": int(pf.active),
            "recorded_at": pf.recorded_at,
        })
        return pf.id

    def list_profile_facts(self, active_only: bool = True):
        sql = "SELECT * FROM profile_facts"
        if active_only:
            sql += " WHERE active = 1"
        return self._rows(sql + " ORDER BY category, recorded_at")

    # -- research runs ------------------------------------------------------
    def add_run(self, run: M.ResearchRun) -> str:
        self._insert("research_runs", {
            "id": run.id, "question": run.question, "lens": run.lens,
            "status": run.status, "summary": run.summary,
            "recorded_at": run.recorded_at,
        })
        return run.id

    def get_run(self, run_id: str):
        r = self._rows("SELECT * FROM research_runs WHERE id=?", (run_id,))
        return r[0] if r else None

    def list_runs(self):
        return self._rows("SELECT * FROM research_runs ORDER BY recorded_at DESC")

    def close_run(self, run_id: str, summary: str = ""):
        self.conn.execute(
            "UPDATE research_runs SET status='CLOSED', summary=? WHERE id=?",
            (summary, run_id),
        )
        self.conn.commit()

    # -- evidence -----------------------------------------------------------
    def add_evidence(self, ev: M.Evidence) -> str:
        if ev.reliability not in M.RELIABILITY:
            raise ValueError(f"reliability must be one of {M.RELIABILITY}")
        self._insert("evidence", {
            "id": ev.id, "source_type": ev.source_type, "source_ref": ev.source_ref,
            "excerpt": ev.excerpt, "supports_claim": ev.supports_claim,
            "reliability": ev.reliability, "accessed_at": ev.accessed_at,
            "notes": ev.notes, "recorded_at": ev.recorded_at,
        })
        return ev.id

    def get_evidence(self, ev_id: str):
        r = self._rows("SELECT * FROM evidence WHERE id=?", (ev_id,))
        return r[0] if r else None

    def list_evidence(self):
        return self._rows("SELECT * FROM evidence ORDER BY accessed_at DESC")

    # -- hypotheses ---------------------------------------------------------
    def add_hypothesis(self, h: M.Hypothesis) -> str:
        self._insert("hypotheses", {
            "id": h.id, "run_id": h.run_id, "statement": h.statement,
            "status": h.status, "reasoning": h.reasoning, "recorded_at": h.recorded_at,
        })
        return h.id

    def list_hypotheses(self, run_id: str):
        return self._rows(
            "SELECT * FROM hypotheses WHERE run_id=? ORDER BY recorded_at", (run_id,)
        )

    def set_hypothesis_status(self, hyp_id: str, status: str, reasoning: str = ""):
        self.conn.execute(
            "UPDATE hypotheses SET status=?, reasoning=? WHERE id=?",
            (status, reasoning, hyp_id),
        )
        self.conn.commit()

    # -- propositions -------------------------------------------------------
    def add_proposition(self, prop: M.Proposition) -> str:
        if prop.status not in M.PROPOSITION_STATUS:
            raise ValueError(f"status must be one of {M.PROPOSITION_STATUS}")
        self._insert("propositions", {
            "id": prop.id, "run_id": prop.run_id, "title": prop.title,
            "arrangement": prop.arrangement, "james_role": prop.james_role,
            "value_to_them": prop.value_to_them, "counterfactual": prop.counterfactual,
            "economics_json": json.dumps(M.asdict(prop.economics)),
            "uncertainties": prop.uncertainties, "invalidators": prop.invalidators,
            "next_step": prop.next_step, "status": prop.status,
            "decision_reasoning": prop.decision_reasoning, "recorded_at": prop.recorded_at,
        })
        return prop.id

    def link_evidence(self, prop_id: str, ev_id: str):
        self.conn.execute(
            "INSERT OR IGNORE INTO evidence_links VALUES (?,?)", (prop_id, ev_id)
        )
        self.conn.commit()

    def evidence_for(self, prop_id: str):
        return self._rows(
            """SELECT e.* FROM evidence e
               JOIN evidence_links l ON e.id = l.evidence_id
               WHERE l.proposition_id=? ORDER BY e.accessed_at DESC""",
            (prop_id,),
        )

    def _row_to_proposition(self, row) -> M.Proposition:
        econ = M.Economics(**json.loads(row["economics_json"]))
        return M.Proposition(
            title=row["title"], arrangement=row["arrangement"],
            james_role=row["james_role"], value_to_them=row["value_to_them"],
            counterfactual=row["counterfactual"], run_id=row["run_id"],
            economics=econ, uncertainties=row["uncertainties"] or "",
            invalidators=row["invalidators"] or "", next_step=row["next_step"] or "",
            status=row["status"], decision_reasoning=row["decision_reasoning"] or "",
            id=row["id"], recorded_at=row["recorded_at"],
        )

    def get_proposition(self, prop_id: str):
        r = self._rows("SELECT * FROM propositions WHERE id=?", (prop_id,))
        return self._row_to_proposition(r[0]) if r else None

    def list_propositions(self, run_id: str = "", status: str = ""):
        sql = "SELECT * FROM propositions"
        clauses, args = [], []
        if run_id:
            clauses.append("run_id=?"); args.append(run_id)
        if status:
            clauses.append("status=?"); args.append(status)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        rows = self._rows(sql + " ORDER BY recorded_at DESC", tuple(args))
        return [self._row_to_proposition(x) for x in rows]

    def set_proposition_status(self, prop_id: str, status: str, reasoning: str = ""):
        """Enforce the validation gate. VALIDATED requires evidence + counterfactual
        + economics (models.validate_proposition). SENT requires a linked Approval.
        This is where fabrication is blocked structurally (tests H, J, U)."""
        if status not in M.PROPOSITION_STATUS:
            raise ValueError(f"status must be one of {M.PROPOSITION_STATUS}")
        prop = self.get_proposition(prop_id)
        if prop is None:
            raise ValueError(f"no proposition {prop_id}")
        if status == "VALIDATED":
            ok, missing = M.validate_proposition(prop, len(self.evidence_for(prop_id)))
            if not ok:
                raise ValueError("cannot mark VALIDATED; missing: " + "; ".join(missing))
        if status == "SENT":
            n = self._rows(
                "SELECT COUNT(*) c FROM approvals WHERE proposition_id=?", (prop_id,)
            )[0]["c"]
            if n == 0:
                raise ValueError("cannot mark SENT without a linked Approval (James must approve)")
        self.conn.execute(
            "UPDATE propositions SET status=?, decision_reasoning=? WHERE id=?",
            (status, reasoning, prop_id),
        )
        self.conn.commit()

    # -- decisions ----------------------------------------------------------
    def add_decision(self, d: M.Decision) -> str:
        if d.decision not in M.DECISION_TYPES:
            raise ValueError(f"decision must be one of {M.DECISION_TYPES}")
        self._insert("decisions", {
            "id": d.id, "run_id": d.run_id, "proposition_id": d.proposition_id,
            "decision": d.decision, "reasoning": d.reasoning, "recorded_at": d.recorded_at,
        })
        return d.id

    def list_decisions(self, run_id: str = ""):
        sql = "SELECT * FROM decisions"
        args = ()
        if run_id:
            sql += " WHERE run_id=?"; args = (run_id,)
        return self._rows(sql + " ORDER BY recorded_at DESC", args)

    # -- approvals (the only path to SENT) ----------------------------------
    def add_approval(self, a: M.Approval) -> str:
        allowed = ("james", "james litan", "jimi", "james o. litan", "james olujimi litan")
        if a.approved_by.strip().lower() not in allowed:
            raise ValueError("approved_by must be James")
        self._insert("approvals", {
            "id": a.id, "proposition_id": a.proposition_id, "approved_by": a.approved_by,
            "scope": a.scope, "channel": a.channel, "notes": a.notes,
            "approved_at": a.approved_at,
        })
        return a.id

    def list_approvals(self, prop_id: str = ""):
        sql = "SELECT * FROM approvals"
        args = ()
        if prop_id:
            sql += " WHERE proposition_id=?"; args = (prop_id,)
        return self._rows(sql + " ORDER BY approved_at DESC", args)


