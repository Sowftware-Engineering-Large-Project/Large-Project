from dataclasses import dataclass

@dataclass
class FestivalAdmin:
    id: int
    name: str
    email:str

    @classmethod
    def from_row(cls, row):
        return cls(
            id = row["id"],
            name = row["name"],
            email = row["email"]
        )

    def update_details(self, name, email):
        self.name = name
        self.email = email