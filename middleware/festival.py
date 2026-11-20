from dataclasses import dataclass

@dataclass
class Festival:
    id: int
    name: str
    start_date: str
    end_date: str

    @classmethod #Creating a festival class by itself
    def from_row(cls, row):
        return cls(
            id=row["id"],
            name=row["name"],
            start_date=row["start_date"],
            end_date=row["end_date"]
        )
    def update_details(self, name, start_date, end_date):
        if end_date < start_date:
            return False

        self.name = name
        self.start_date = start_date
        self.end_date = end_date

        return True





