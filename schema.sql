PRAGMA foreign_keys = ON;
BEGIN;
CREATE TABLE IF NOT EXISTS festivals (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL CHECK (end_date >= start_date)
);
CREATE TABLE IF NOT EXISTS venues (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    capacity INTEGER NOT NULL CHECK (typeof(capacity) = 'integer' AND capacity > 0)
);
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    contact_info TEXT NOT NULL CHECK (length(trim(contact_info)) > 0),
    type TEXT NOT NULL CHECK (type IN ('Student', 'Professional', 'Speaker', 'Volunteer'))
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    festival_id INTEGER NOT NULL REFERENCES festivals(id),
    venue_id INTEGER NOT NULL REFERENCES venues(id),
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    description TEXT NOT NULL CHECK (length(trim(description)) > 0),
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL CHECK (ends_at > starts_at),
    capacity INTEGER NOT NULL CHECK (typeof(capacity) = 'integer' AND capacity > 0),
    status TEXT NOT NULL DEFAULT 'Scheduled' CHECK (status IN ('Scheduled', 'Cancelled')),
    UNIQUE (id, festival_id)
);
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY,
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    festival_id INTEGER NOT NULL REFERENCES festivals(id),
    event_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Cancelled')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id, festival_id) REFERENCES events(id, festival_id)
);
CREATE INDEX IF NOT EXISTS idx_events_venue_start ON events(venue_id, starts_at);
CREATE INDEX IF NOT EXISTS idx_registrations_event ON registrations(event_id);
COMMIT;
