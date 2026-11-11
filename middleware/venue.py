from dataclasses import dataclass


@dataclass
class Venue:
    venue_id: int
    name: str
    capacity: int

    @classmethod
    def from_row(cls, row):
        return cls(
            venue_id=row["id"],
            name=row["name"],
            capacity=row["capacity"]
        )

    def can_hold(self, event_capacity: int) -> bool:
        return (
            type(event_capacity) is int
            and 0 < event_capacity <= self.capacity
        )


