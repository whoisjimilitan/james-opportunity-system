# 03 — System Behaviour and Autonomy

## Intended behaviour
Build a persistent system that can undertake meaningful discovery runs, retain learning, resume work, and eventually operate on a schedule if the necessary infrastructure and permissions exist. A prompt alone is not a continuously running agent. Persistence, research tools, scheduling, credentials, logs and external integrations must be implemented explicitly.

The system should:
- Select or generate research directions based on current knowledge, uncertainty, prior findings and possible value.
- Investigate several materially different possibilities when the search space is broad.
- Use external research to find current, attributable evidence.
- Generate competing hypotheses and deal structures, including unexpected ones.
- Use specialist subagents when parallel work genuinely helps; avoid spawning agents for theatre.
- Compare candidate propositions, not merely organisations.
- Decide whether to continue researching, reframe, test, develop James, prepare a proposal, pause or abandon.
- Preserve a clear audit trail of sources, assumptions, decisions and outcomes.
- Return concise human-readable findings with links to underlying evidence.
- Learn from responses and real outcomes without overgeneralising from a single result.

## Adaptive, not rigid
There is no mandatory sequence of stages. Research, invention, validation, James-profile updates, positioning and communication can send work backwards, branch, overlap or stop. The system must not be forced to produce an email after each run.

Methods, decision questions, checklists and scores are optional aids. They must never become substitutes for judgement. A numerical score must not conceal a fatal flaw such as no credible demand, no legitimate route to act, or no plausible role for James.

## Persistent memory
Store durable knowledge separately from transient reasoning. Keep:
- James profile, constraints, preferences and provenance.
- Opportunity hypotheses and their status.
- Evidence records with source, date accessed, relevant excerpt/summary, reliability and what claim they support.
- Rejected hypotheses and reasons, to avoid repeating failed work.
- Relationships, contact history and authorisation status.
- Experiments, actions, replies, outcomes and lessons.
- Current research frontier: what is promising, what is unknown and what should be investigated next.

Distinguish durable facts from run-specific conclusions. Avoid silently overwriting a fact with an inference. Keep changes traceable.

## Autonomy levels
Implement in stages:
1. **Manual research assistant:** user starts a run; system researches and reports.
2. **Persistent workbench:** saves propositions, evidence, profile and outcomes.
3. **Assisted action:** drafts contact, plans experiments and prepares actions for approval.
4. **Scheduled research:** runs within explicit budgets, scope and time limits.
5. **Bounded external autonomy:** only after tested reliability and explicit permissions; narrowly scoped, logged and reversible where possible.

Default to human approval before sending messages, spending money, making commitments, representing James, submitting applications/bids, or disclosing personal information. Do not bypass platform permissions or use deceptive identity practices. The system may prepare actions without executing them.

## Stopping and resource allocation
Research should stop or pivot when:
- Evidence repeatedly fails to support the central hypothesis.
- The next useful step depends on information only a person or organisation can provide.
- The likely value is too small relative to time, money or risk.
- James lacks a credible role and no realistic development path exists.
- The idea requires unsupported claims, improper access or a questionable arrangement.
- A more promising direction deserves the available research budget.

Stopping is a successful system action when it prevents wasted effort. Record why.

## Human-readable results
A run should make clear:
- What was newly discovered.
- What is genuinely promising and why.
- What remains speculative.
- What the system tried to disprove.
- What it recommends doing next and why.
- Whether James needs to decide something.
- What was saved for future runs.

Do not present a polished report as if the underlying work were more certain than it is.
