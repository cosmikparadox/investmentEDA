"""Write the entities that have coordinates to a CSV for Kepler.gl.

    make map        (or: uv run python app/export_map.py)

Kepler.gl is a free map tool that runs in a browser at https://kepler.gl/demo.
You drag a CSV onto it and it draws the points. There is no account, no upload
to anyone's server in the demo, and no library to install — which is why v0 uses
it instead of building a map into the dashboard.

What it exports is the entity registry, not observations: where the things we
track *are*. In v0 that is one point, the Strait of Hormuz. The other two
entities have no coordinates on purpose — a country is not a point, and a price
benchmark is not a place at all — so they are left out rather than given a
plausible-looking centroid.

The file lands under data/, which is not in git: it is derived, and it can be
rebuilt any time from the registry.
"""

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import paths  # noqa: E402  (must follow the path line above)
from core.config import settings  # noqa: E402
from core.logging import get_logger  # noqa: E402

OUTPUT = paths.DATA_DIR / "export" / "entities.csv"

log = get_logger(__name__)


def export(destination: Path = OUTPUT) -> Path:
    """Write one row per entity that has a location, and return where it went.

    The columns are named `latitude` and `longitude` because Kepler.gl finds
    those automatically and draws the points without being configured.
    """
    if not settings.db_path.exists():
        raise SystemExit(
            f"{settings.db_path} does not exist. Build it first:\n    make init"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(settings.db_path), read_only=True)
    try:
        rows = conn.execute(
            """
            SELECT entity_id, entity_type, display_name,
                   lat AS latitude, lon AS longitude,
                   id_scheme, notes
            FROM entity_registry
            WHERE lat IS NOT NULL AND lon IS NOT NULL
            ORDER BY entity_id
            """
        ).df()
    finally:
        conn.close()

    rows.to_csv(destination, index=False)
    log.info("wrote %d entities to %s", len(rows), paths.relative_to_repo(destination))
    return destination


def main() -> None:
    written = export()
    print(f"Wrote {paths.relative_to_repo(written)}")
    print()
    print(written.read_text())
    print("Open https://kepler.gl/demo and drag that file onto the page.")


if __name__ == "__main__":
    main()
