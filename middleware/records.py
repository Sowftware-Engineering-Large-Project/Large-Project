"""Validate and persist the Sprint 5 team workflows."""

from datetime import datetime

from db import TABLES
from .venue import Venue
from .event import Event




PARTICIPANT_TYPES = {"Student", "Professional", "Speaker", "Volunteer"}
MAX_SQLITE_ID = 2**63 - 1


class InvalidRecord(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def read_state(connection):
    return {
        table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY id")]
        for table in TABLES
    }


def text(payload, key, label, limit=200):
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise InvalidRecord(f"Enter {label} of up to {limit} characters.")
    return value.strip()


def integer(payload, key, label, maximum=MAX_SQLITE_ID):
    value = payload.get(key)
    if type(value) is not int or not 1 <= value <= maximum:
        raise InvalidRecord(f"Choose a valid {label}." if key.endswith("_id")
                            else f"Enter a whole-number {label} from 1 to {maximum}.")
    return value


def timestamp(payload, key, label):
    value = payload.get(key)
    for pattern in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            parsed = datetime.strptime(value, pattern)
        except (TypeError, ValueError):
            continue
        if parsed.strftime(pattern) == value:
            return parsed
    raise InvalidRecord(f"Enter a valid {label} in Cleveland local time.")


def get_record(connection, table, record_id, label):
    if record_id > MAX_SQLITE_ID:
        raise InvalidRecord(f"{label} was not found.", 404)
    row = connection.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        raise InvalidRecord(f"{label} was not found.", 404)
    return row


def venue_values(connection, payload, existing):
    name = text(payload, "name", "a venue name")
    capacity = integer(payload, "capacity", "capacity", 2**53 - 1)
    if existing and connection.execute(
        "SELECT 1 FROM events WHERE venue_id = ? AND status = 'Scheduled' AND capacity > ?",
        (existing["id"], capacity),
    ).fetchone():
        raise InvalidRecord("Capacity is below that of a scheduled event at this venue.")
    return {"name": name, "capacity": capacity}


def participant_values(_connection, payload, _existing):
    participant_type = text(payload, "type", "a participant type")
    if participant_type not in PARTICIPANT_TYPES:
        raise InvalidRecord("Choose a valid participant type.")
    return {
        "name": text(payload, "name", "a participant name"),
        "contact_info": text(payload, "contact_info", "contact information"),
        "type": participant_type,
    }


def event_values(connection, payload, existing):
    venue_id = integer(payload, "venue_id", "venue")
    venue = get_record(connection, "venues", venue_id, "Venue")
    venue_object = Venue.from_row(venue)
    festival = (get_record(connection, "festivals", existing["festival_id"], "Festival")
                if existing else connection.execute("SELECT * FROM festivals ORDER BY id LIMIT 1").fetchone())
    if festival is None:
        raise InvalidRecord("Initialize a festival before adding events.", 409)

    starts = timestamp(payload, "starts_at", "start date and time")
    ends = timestamp(payload, "ends_at", "end date and time")
    if ends <= starts:
        raise InvalidRecord("The event must end after it starts.")
    if starts.date().isoformat() < festival["start_date"] or ends.date().isoformat() > festival["end_date"]:
        raise InvalidRecord(f"Keep the event within {festival['start_date']} to {festival['end_date']}.")

    capacity = integer(payload, "capacity", "capacity", 2**53 - 1)
    if not venue_object.can_hold(capacity):
        raise InvalidRecord("Event capacity cannot exceed the venue capacity.")
    event = Event(
        event_id=existing["id"] if existing else None,
        festival_id=festival["id"],
        venue_id=venue_id,
        title=text(payload, "title", "an event title"),
        description=text(payload, "description", "an event description", 2000),
        starts_at=starts,
        ends_at=ends,
        capacity=capacity,
        status=existing["status"] if existing else "Scheduled"
    )
    return event.to_record()


def registration_values(connection, payload, _existing):
    participant_id = integer(payload, "participant_id", "participant")
    event_id = integer(payload, "event_id", "event")
    get_record(connection, "participants", participant_id, "Participant")
    event = get_record(connection, "events", event_id, "Event")
    if event["status"] != "Scheduled":
        raise InvalidRecord("Choose a scheduled event.")
    if connection.execute(
        "SELECT 1 FROM registrations WHERE participant_id = ? AND event_id = ? AND status = 'Active'",
        (participant_id, event_id),
    ).fetchone():
        raise InvalidRecord("This participant is already registered for the event.", 409)
    return {"participant_id": participant_id, "event_id": event_id, "festival_id": event["festival_id"]}


VALIDATORS = {
    "venues": venue_values,
    "events": event_values,
    "participants": participant_values,
    "registrations": registration_values,
}


def save_record(connection, table, record_id, payload):
    """Use fixed table and column names; bind values as SQL parameters."""
    existing = get_record(connection, table, record_id, "Record") if record_id is not None else None
    values = VALIDATORS[table](connection, payload, existing)
    if existing is None:
        placeholders = ", ".join("?" for _ in values)
        connection.execute(f"INSERT INTO {table} ({', '.join(values)}) VALUES ({placeholders})",
                           tuple(values.values()))
    else:
        assignments = ", ".join(f"{column} = ?" for column in values)
        connection.execute(f"UPDATE {table} SET {assignments} WHERE id = ?",
                           (*values.values(), record_id))
