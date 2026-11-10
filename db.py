import sqlite3
from datetime import date, timedelta
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext

TABLES = ("festivals", "venues", "events", "participants", "registrations")


def get_db():
    """Return the current Flask context's database connection."""
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"], timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def is_initialized():
    """Check that the database file and all Sprint 5 tables exist."""
    if not current_app.config["DATABASE"].is_file():
        return False

    tables = {
        row["name"]
        for row in get_db().execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    return set(TABLES).issubset(tables)


def require_initialized():
    if not is_initialized():
        raise click.ClickException("Run python -m flask --app app init-db first.")


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create the Sprint 5 tables without clearing existing data."""
    database_path = current_app.config["DATABASE"]
    database_path.parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    get_db().executescript(schema)
    click.echo(f"Database initialized at {database_path}")


def parse_demo_date(_ctx, _parameter, value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() == value and parsed < date.max:
            return parsed
    except ValueError:
        pass
    raise click.BadParameter("Use YYYY-MM-DD, before 9999-12-31.")


@click.command("seed-demo")
@click.option(
    "--start-date",
    required=True,
    callback=parse_demo_date,
    help="First day of the demo festival in YYYY-MM-DD format.",
)
@with_appcontext
def seed_demo_command(start_date):
    """Add one linked sample record to each Sprint 5 table."""
    require_initialized()
    connection = get_db()
    festival_name = "CLE TechFest Demo"
    start = start_date.isoformat()
    end = (start_date + timedelta(days=1)).isoformat()

    with connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute(
            "SELECT id FROM festivals WHERE name = ? AND start_date = ? AND end_date = ?",
            (festival_name, start, end),
        ).fetchone()
        if existing is not None:
            click.echo("Demo festival already exists for those dates.")
            return

        festival_id = connection.execute(
            "INSERT INTO festivals (name, start_date, end_date) VALUES (?, ?, ?)",
            (festival_name, start, end),
        ).lastrowid
        venue_id = connection.execute(
            "INSERT INTO venues (name, capacity) VALUES (?, ?)",
            ("Demo Hall", 30),
        ).lastrowid
        participant_id = connection.execute(
            "INSERT INTO participants (name, contact_info, type) VALUES (?, ?, ?)",
            ("Demo Participant", "demo@example.com", "Student"),
        ).lastrowid
        event_id = connection.execute(
            """
            INSERT INTO events (
                festival_id, venue_id, title, description, starts_at, ends_at, capacity
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                festival_id, venue_id, "Intro to CLE TechFest", "Sample event",
                f"{start}T10:00:00", f"{start}T11:00:00", 20,
            ),
        ).lastrowid
        registration_id = connection.execute(
            """
            INSERT INTO registrations (participant_id, festival_id, event_id)
            VALUES (?, ?, ?)
            """,
            (participant_id, festival_id, event_id),
        ).lastrowid

    click.echo(f"Demo data saved. Registration ID: {registration_id}")


@click.command("check-db")
@with_appcontext
def check_db_command():
    """Verify table presence and foreign keys, then print row counts."""
    require_initialized()
    connection = get_db()
    violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise click.ClickException(f"Found {len(violations)} foreign key violation(s).")

    click.echo(f"Database: {current_app.config['DATABASE']}")
    for table in TABLES:
        # Table names come from the fixed TABLES constant.
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        click.echo(f"{table}: {count}")
    click.echo("Foreign key check passed.")


def init_app(app):
    """Attach database lifecycle handling and CLI commands to Flask."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_demo_command)
    app.cli.add_command(check_db_command)
