"""SQLite-backed CLE TechFest team workspace."""

import hmac
import sqlite3

from flask import Blueprint, current_app, redirect, request, send_from_directory, url_for

import db

from .records import InvalidRecord, read_state, save_record

workspace = Blueprint("techfest", __name__, url_prefix="/techfest")
ASSETS = {"index.html", "events.html", "attendees.html", "registration.html",
          "admin.html", "styles.css", "app.js"}


@workspace.before_request
def require_team_access():
    password = current_app.config["TECHFEST_TEAM_PASSWORD"]
    if not password:
        return {"error": "Set TECHFEST_TEAM_PASSWORD on the server to enable the workspace."}, 503

    credentials = request.authorization
    if credentials and credentials.type == "basic":
        username_ok = hmac.compare_digest((credentials.username or "").encode(), b"techfest")
        password_ok = hmac.compare_digest((credentials.password or "").encode(), password.encode())
        if username_ok and password_ok:
            return None
    return {"error": "Team sign-in required."}, 401, {
        "WWW-Authenticate": 'Basic realm="CLE TechFest team", charset="UTF-8"',
    }


@workspace.after_request
def prevent_shared_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@workspace.get("/")
def index():
    return redirect(url_for("techfest.asset", filename="index.html"))


@workspace.get("/<filename>")
def asset(filename):
    if filename not in ASSETS:
        return {"error": "Page not found."}, 404
    return send_from_directory(current_app.config["TECHFEST_FRONTEND"], filename)


@workspace.get("/api/state")
def state():
    if not db.is_initialized():
        return {"error": "The database has not been initialized."}, 503
    connection = db.get_db()
    with connection:
        connection.execute("BEGIN")
        return read_state(connection)


@workspace.post("/api/<table>")
@workspace.patch("/api/<table>/<int:record_id>")
def write(table, record_id=None):
    if table not in ("venues", "events", "participants", "registrations"):
        return {"error": "Unknown resource."}, 404
    if record_id is not None and table == "registrations":
        return {"error": "Registrations can only be created here."}, 405
    if not request.is_json:
        return {"error": "Send a JSON request."}, 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {"error": "Send a JSON object."}, 400
    if not db.is_initialized():
        return {"error": "The database has not been initialized."}, 503

    connection = db.get_db()
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            save_record(connection, table, record_id, payload)
            snapshot = read_state(connection)
    except InvalidRecord as error:
        return {"error": str(error)}, error.status
    except sqlite3.IntegrityError:
        return {"error": "The record could not be saved. Check the selected values."}, 409
    except sqlite3.OperationalError:
        current_app.logger.exception("SQLite write failed")
        return {"error": "The database is unavailable. Try again shortly."}, 503
    return snapshot, 201 if record_id is None else 200
