# controlroom

Personal commodity and supply-chain intelligence system. Free data in, vintage
history kept, slow decisions out. No execution, no agents, no models until the
data layer is proven.

Start with `CLAUDE.md`, then `docs/SCOPE.md`, then `docs/PLAN.md`.
`docs/CHARTER.md` (why this exists), `docs/PRD.md` (numbered requirements)
and `docs/ARCHITECTURE.md` (module layout and contracts) are read-once
background; the three named in the line above are the ones that change
week to week.

## Setup

Needs `uv` (which installs Python for you) and nothing else.

```bash
git clone https://github.com/cosmikparadox/investmentEDA.git
cd investmentEDA
uv sync                       # installs the six dependencies
cp .env.example .env          # then open .env and paste your two keys in
uv run python db/init.py      # builds data/controlroom.duckdb
```

`db/init.py` is safe to run again at any time. It re-creates anything missing and
never touches data an ingestor has already written.

Free API keys: EIA at <https://www.eia.gov/opendata/register.php>, FRED at
<https://fredaccount.stlouisfed.org/apikey>.

## Working model

Two sessions, one repo:

- **Coordination and research** (claude.ai chat): research feeds and methods,
  answer `docs/QUESTIONS.md`, review Claude Code's output, rewrite the plan at
  each milestone. Holds no state that is not in this repo.
- **Build** (Claude Code): works `docs/PLAN.md` top to bottom, writes to
  `docs/DECISIONS.md`, asks via `docs/QUESTIONS.md`, never expands scope.
- **Owner:** runs commands, reads every diff, hand-writes the first ingestor,
  explains the system back at each milestone.

If either session is being asked to remember something, write it down instead.

## Where things live

| Thing | Lives in | Why |
|---|---|---|
| Everything operational: scope, design, plan, decisions, questions, feed specs, code | **This repo** | Single source of truth. Claude Code and the owner work here. |
| Research reports, infonomics primer | `docs/research/` in this repo **and** the claude.ai Project knowledge | Reference. Doesn't change. The coordination session needs it in context. |
| Current state of the build | `docs/DECISIONS.md`, `docs/QUESTIONS.md`, `docs/PLAN.md` tick-boxes | The coordination session reads these when you upload them. It does not remember. |
| API keys | `.env` on your own machine, or the environment settings of a cloud session | Both set the same two variables, `EIA_API_KEY` and `FRED_API_KEY`; code reads whichever is present. Never committed, never pasted into a chat window. |
| Throwaway visuals from chats | Nowhere | Delete them. If one turns out to matter, rebuild it from data in this repo. |

## Session handoff protocol

Starting a coordination session: upload `docs/DECISIONS.md` and `docs/QUESTIONS.md`
(and `docs/RETRO.md` at milestones). That is the whole context transfer.

Starting a Claude Code session: it reads `CLAUDE.md` automatically. Tell it which
week of `docs/PLAN.md` you are on.
