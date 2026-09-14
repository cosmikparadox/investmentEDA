# queries/

SQL that is run by hand, by a person, for research. Nothing in `app/` may reach
anything in here, and nothing in here runs on a schedule.

## Why this directory exists separately

These queries read `observations` directly — the base table, every vintage,
**including the holdout weeks**. The dashboard cannot: it reads
`observations_explore`, which does not contain them, and there is no control
anywhere in the app that changes that (PRD FR-44, FR-61, UI-08).

That split is the point of the whole exercise. A quarter of the weeks in history
are hidden from the app so that a pattern you notice by eye can later be tested
on data nobody has looked at. The moment the holdout becomes reachable from the
thing you browse every day, it stops being a test set and becomes more data to
form opinions from, and the opinions will fit it, because that is what opinions
do.

So: open one of these files when you are testing a logged observation, not when
you are curious. Write down what you expected before you run it — the note in
`observation_log` is supposed to exist before the test, not after.

## What is here

| file | question it answers |
|---|---|
| `asof.sql` | What did we know about series X on date D? Returns the vintage we held then, not the one we hold now. |
