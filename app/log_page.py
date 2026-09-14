"""The observation log, listed newest first. Read-only, on purpose.

Every note the owner writes is kept, including the ones that turned out to be
wrong. That is the point of it: remembering the hits and forgetting the misses
is the most reliable way to believe you are better at this than you are. So this
page shows and never edits — there is no delete button, no edit box, and no way
to change a note's status from here (PRD FR-43, UI-04).
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import queries  # noqa: E402  (must follow the path line above)

# What each status means, in plain words, so the page explains itself.
STATUS_HELP = {
    "noted": "written down, not tested",
    "testing": "being tested against the weeks nobody has looked at",
    "supported": "tested, and the data agreed",
    "rejected": "tested, and the data disagreed — kept deliberately",
}


def render_log() -> None:
    st.title("Observation log")
    st.caption(
        "Newest first. Nothing here can be edited or deleted, including the "
        "notes that turn out to be wrong."
    )

    try:
        conn = queries.connect()
    except FileNotFoundError as missing:
        st.error(
            f"No database at {missing}. Build it first:\n\n"
            f"    uv run python db/init.py"
        )
        return
    except queries.DatabaseBusy:
        st.info(
            "**The database is busy.** An ingest is probably still running in "
            "another window. Wait for it to finish, then reload this page."
        )
        return

    try:
        entries = queries.log_entries(conn)
    finally:
        conn.close()

    if entries.empty:
        st.info(
            "Nothing logged yet. Write a note under any chart on the dashboard — "
            "\"nothing moved\" counts, and a week of those is still a record of "
            "what you were watching."
        )
        return

    st.caption(" · ".join(f"**{name}**: {meaning}" for name, meaning in STATUS_HELP.items()))

    for entry in entries.itertuples():
        window = ""
        if entry.window_start is not None and entry.window_end is not None:
            # Dates, not timestamps: the window is which days were on screen.
            window = (f" · looking at {entry.window_start:%Y-%m-%d}"
                      f" to {entry.window_end:%Y-%m-%d}")
        series = ", ".join(entry.series_ids) if entry.series_ids is not None else "—"

        st.markdown(f"**{entry.noted_at:%Y-%m-%d %H:%M} UTC** · `{entry.status}`{window}")
        st.markdown(f"> {entry.note}")
        st.caption(f"on screen: {series}"
                   + (f" · tested in {entry.test_ref}" if entry.test_ref else ""))
        st.divider()
