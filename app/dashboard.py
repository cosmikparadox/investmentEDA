"""The one page. Three charts, what is fresh, and somewhere to write a note.

Run it with:

    make dashboard          (or: uv run streamlit run app/dashboard.py)

What this page deliberately cannot do:

**It cannot show you the holdout.** A quarter of the weeks in history are held
back so that a pattern you spot here can later be tested on data nobody has
looked at. The page reads a view of the database that does not contain them, so
there is no filter to relax and no toggle to find. The gaps in the lines are
those weeks. They are supposed to be visible — a chart that looked continuous
would mean the app was reading the wrong view (PRD UI-01, UI-08).

**It cannot change anything.** The connection it reads through is read-only. The
one thing it writes is a note, which is appended and never edited.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import queries  # noqa: E402  (must follow the path line above)
from app.log_page import render_log  # noqa: E402

# How far back each option looks. "Everything" is everything the app may see,
# which is not everything there is.
WINDOWS = {
    "Last 90 days": 90,
    "Last year": 365,
    "Last 3 years": 365 * 3,
    "Everything we may look at": None,
}


@st.cache_data(ttl=60)
def load_catalogue() -> pd.DataFrame:
    conn = queries.connect()
    try:
        return queries.series_catalogue(conn)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_series(series_id: str, since: date) -> pd.DataFrame:
    conn = queries.connect()
    try:
        return queries.series_values(conn, series_id, since)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_panels() -> tuple[pd.DataFrame, pd.DataFrame]:
    conn = queries.connect()
    try:
        return queries.last_received(conn), queries.recent_runs(conn)
    finally:
        conn.close()


def break_the_line_at_missing_weeks(frame: pd.DataFrame) -> pd.DataFrame:
    """Put an empty point into any ISO week that has no data at all.

    Without this, a chart joins the last point before a hidden week straight to
    the first point after it, drawing a clean line across the gap — which is
    exactly the illusion the holdout exists to prevent. An empty value makes the
    line stop and start again, so the missing week is something you can see.

    Whole missing weeks only. Weekends and market holidays are absences too, but
    they are normal ones, and breaking the line at every Saturday would make the
    charts unreadable and the real gaps invisible.
    """
    if frame.empty:
        return frame

    periods = pd.to_datetime(frame["period_start"])
    weeks_present = set(periods.dt.strftime("%G-W%V"))

    # Every Monday between the first and last point we hold.
    first_monday = periods.min() - pd.Timedelta(days=periods.min().weekday())
    all_mondays = pd.date_range(first_monday, periods.max(), freq="W-MON")
    missing = [
        monday for monday in all_mondays
        if monday.strftime("%G-W%V") not in weeks_present
    ]
    if not missing:
        return frame

    gaps = pd.DataFrame({"period_start": missing, "value": [None] * len(missing)})
    combined = pd.concat([frame.assign(period_start=periods), gaps], ignore_index=True)
    return combined.sort_values("period_start").reset_index(drop=True)


def chart(frame: pd.DataFrame, unit: str) -> alt.Chart:
    """One line, with the gaps left as gaps."""
    return (
        alt.Chart(break_the_line_at_missing_weeks(frame))
        .mark_line(point=False)
        .encode(
            x=alt.X("period_start:T", title=None),
            y=alt.Y("value:Q", title=unit, scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("period_start:T", title="period"),
                alt.Tooltip("value:Q", title=unit),
            ],
        )
        .properties(height=260)
    )


def render_one_series(row: pd.Series, since: date, window_end: date) -> None:
    """A chart, its provenance, and a box to write what you notice."""
    st.caption(
        f"**{row.series_id}** · {row.unit} · {row.entity_name} · "
        f"via {row.feed_id} ({row.provider}, {row.cadence}) · "
        f"last received {row.last_received:%Y-%m-%d %H:%M} UTC"
    )

    frame = load_series(row.series_id, since)
    if frame.empty:
        st.info("Nothing in this window.")
        return

    st.altair_chart(chart(frame, row.unit), use_container_width=True)

    # "Note this" — one box, one button, nothing else (PRD UI-03).
    with st.form(f"note_{row.series_id}", clear_on_submit=True):
        note = st.text_input(
            "Note this",
            placeholder="What do you notice? \"Nothing moved\" is a note.",
            label_visibility="collapsed",
        )
        if st.form_submit_button("Save note") and note.strip():
            queries.write_note(note, [row.series_id], since, window_end)
            st.cache_data.clear()
            st.success("Saved. It is on the Log page, and it cannot be edited.")


def render_dashboard() -> None:
    st.title("controlroom")
    st.caption(
        "Three feeds, five series. A quarter of the weeks are held back for "
        "testing and are not on this page — the gaps in the lines are those weeks."
    )

    try:
        catalogue = load_catalogue()
    except FileNotFoundError as missing:
        st.error(
            f"No database at {missing}. Build it and pull the feeds first:\n\n"
            f"    make init\n    make ingest"
        )
        return

    if catalogue.empty:
        st.warning("The database is built but empty. Run `make ingest`.")
        return

    choice = st.radio("Window", list(WINDOWS), horizontal=True, index=1)
    days = WINDOWS[choice]
    window_end = date.today()
    since = date(2015, 1, 1) if days is None else window_end - timedelta(days=days)

    for feed_id, feed_rows in catalogue.groupby("feed_id", sort=True):
        st.subheader(feed_id)
        options = list(feed_rows["series_id"])
        chosen = (
            options[0] if len(options) == 1
            else st.radio(
                "Series", options, horizontal=True, key=f"pick_{feed_id}",
                label_visibility="collapsed",
            )
        )
        render_one_series(
            feed_rows[feed_rows["series_id"] == chosen].iloc[0], since, window_end
        )
        st.divider()

    freshness, runs = load_panels()

    st.subheader("Last received")
    st.caption("Our own clock: when we last had this feed, not when it was published.")
    st.dataframe(freshness, hide_index=True, use_container_width=True)

    st.subheader("Recent runs")
    st.caption(
        "Every attempt to pull a feed, successful or not. If a chart has stopped "
        "moving, look here first."
    )
    if not runs.empty:
        stale = runs[runs["status"] == "failed"]
        if not stale.empty:
            st.warning(
                f"{len(stale)} of the last {len(runs)} runs failed. "
                f"The error is in the table below."
            )
    st.dataframe(runs, hide_index=True, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="controlroom", page_icon="🛢", layout="wide")
    pages = [
        st.Page(render_dashboard, title="Dashboard", url_path="dashboard", default=True),
        st.Page(render_log, title="Log", url_path="log"),
    ]
    st.navigation(pages).run()


main()
