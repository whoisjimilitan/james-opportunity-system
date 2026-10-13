# Instructions for Cline: Build the James Opportunity System

You are taking over the build from Claude. The handoff documents are complete. Your job is to build the actual system and test it immediately.

## What This System Is

**Not:** A job finder, lead generator, or email writer.

**Is:** An Opportunity Intelligence Engine that discovers, constructs, and positions opportunities for James. It may use outreach as a tool, but outreach is optional—discovery is non-negotiable.

## Critical Documents to Read First

1. `README_FIRST.md` — Overview
2. `08_CLAUDE_CODE_KICKOFF_PROMPT_REFINED.md` — What the system should be
3. `03X_OUTREACH_IS_OPTIONAL.md` — Core principle: outreach is optional
4. `04A_DISCOVERY_IN_ACTION_EXAMPLE.md` — Model of what strong discovery looks like
5. `04B_WHAT_FABRICATION_REVEALS.md` — What weak discovery looks like
6. All other numbered docs (they form the complete spec)

## Your Build Tasks

### Phase 1: Understand & Propose (Do This First)

Read all documents. Then write a proposal that explains:
1. What the system actually does in your own words
2. How this is different from a job finder
3. The core intelligence (hint: it's about judgment, not procedures)
4. Smallest possible prototype that tests discovery quality
5. Architecture with only what's needed to start
6. Any genuine blocking questions

Don't build yet. Just explain your understanding.

### Phase 2: Build the Prototype (After Approval)

Build:
- **Core domain model**: JamesProfile, ResearchRun, Hypothesis, Proposition, Evidence
- **Persistent storage**: SQLite locally (discoveries must survive restarts)
- **Simple CLI or interface**: User can start a discovery run, see results, save findings
- **Evidence tracking**: Every claim must link to source with provenance

Build it small. No fancy UI yet. Text-based is fine.

### Phase 3: Run Discovery (Immediately After Build Works)

Test with 2-3 real discovery runs:

**Run 1: Ghana Training Market**
- Question: "What arrangement could James become relevant to in West African crisis intervention training?"
- System researches signals, organizations, possibilities
- System produces: hypothesis, evidence, proposed arrangements, decision (pursue/develop/reject)
- Does NOT need to produce email. Success = documented reasoning.

**Run 2: International Platform Expansion**
- Question: "Where are UK institutions expanding into new markets and need local expertise?"
- System discovers, constructs, positions
- Output: validated opportunity with clear James role

**Run 3: Unexpected Connection**
- System uses discovery to find something nobody expected
- Proof of concept: system can invent, not just find

### Phase 4: Test with Real Outreach (If Discoveries Are Strong)

Once you have 1-2 strong discoveries from Phases 1-3:
- Generate outreach emails that are human-level real (no AI fingerprints)
- Send them (actually send, don't just draft)
- Track responses
- Learn from what works

## What Success Looks Like

**Not:** "System ran without errors"

**Is:** "System discovered something real about a possible arrangement that James wouldn't have seen otherwise, and communicated it clearly enough to get a response"

## Critical Rules

- Don't force email generation. If discovery is weak, stop.
- Don't optimize for volume. One strong discovery beats 100 weak ones.
- Don't use persuasion techniques. Lead with what's real about their benefit.
- Don't invent facts. Distinguish evidence from inference.
- Do test the counterfactual: "What changes if James is involved?"
- Do make discoveries portable (save to GitHub, not just memory)

## James's Profile (For Discovery)

Read: `02_JAMES_PROFILE_AND_TRUTH_BOUNDARIES.md` and the memory file in `/memory/james_litan_cv_and_strengths.md`

Key: He's not a fixed profile. He's a rare combination (Western institutional knowledge + African context understanding + training capability + crisis credibility). Discoveries will position him differently based on what each opportunity needs.

## Tech Stack (Recommended)

- **Language**: Python (simple, testable)
- **Database**: SQLite (local, portable)
- **Storage**: JSON/Markdown exports (version-control friendly)
- **Research**: Web search API or manual research (see 04_EVIDENCE_AND_VALIDATION.md for standards)
- **Testing**: Against acceptance tests in `07_ACCEPTANCE_TESTS.md`

## Success Metrics

- Can you read all the docs and explain the system to someone who hasn't seen them?
- Does your prototype store and retrieve discoveries reliably?
- Do 2-3 test discovery runs produce clear propositions (not vague suggestions)?
- Can you generate an email that sounds like a real person wrote it?
- If you send those emails, do you get responses?

## GitHub

This folder is already initialized as a git repo and committed. Push changes frequently.

Commit after each phase:
- Phase 1 commit: "Proposal: System Architecture"
- Phase 2 commit: "Prototype: Core Discovery System"
- Phase 3 commit: "Test Runs: Discovery Results"
- Phase 4 commit: "Live Outreach: Results and Learning"

## Questions?

If you hit a genuine blocker (not a "should we also add...?" but "the spec contradicts itself on...?"), flag it. But aim to build with what you have. The docs will evolve as the system discovers.

## Start Now

1. Read the docs
2. Write your understanding/proposal
3. Show it to the user
4. Get approval
5. Build
6. Test
7. Discover

Go.