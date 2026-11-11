from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    event_id: int | None
    festival_id: int
    venue_id: int
    title: str
    description: str
    starts_at: datetime
    ends_at: datetime
    capacity: int
    status: str = "Scheduled"


    def update_details(self, *, title, description, starts_at, ends_at, capacity):
        if not title.strip() or not description.strip():
            raise ValueError("Icorrect event details")

        if ends_at <= starts_at:
            raise ValueError("Event needs to end before starting")

        if type(capacity) is not int or capacity <= 0:
            raise ValueError("Unaccepted event capacity")

        self.title = title.strip()
        self.description = description.strip()
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.capacity = capacity

    def cancel(self):
        self.status = "Cancelled"

    def to_record(self):
        return {
            "festival_id": self.festival_id,
            "venue_id": self.venue_id,
            "title": self.title,
            "description": self.description,
            "starts_at": self.starts_at.isoformat(timespec="seconds"),
            "ends_at": self.ends_at.isoformat(timespec="seconds"),
            "capacity": self.capacity
        }


    @classmethod
    def from_row(cls, row):
        return cls(
            event_id=row["id"],
            festival_id=row["festival_id"],
            venue_id=row["venue_id"],
            title=row["title"],
            description=row["description"],
            starts_at=datetime.fromisoformat(row["starts_at"]),
            ends_at=datetime.fromisoformat(row["ends_at"]),
            capacity=row["capacity"],
            status=row["status"]
        )


