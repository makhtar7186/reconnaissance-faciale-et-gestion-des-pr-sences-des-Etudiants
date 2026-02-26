# student.py


class Student:
    """Représente un étudiant avec ses informations d'identité."""

    def __init__(self, name: str):
        parts = name.split("_")
        self.prenom = parts[0] if len(parts) > 0 else name
        self.nom = parts[1] if len(parts) > 1 else ""
        self.full_name = name
        self.entry_time: str | None = None

    def mark_present(self, entry_time: str):
        self.entry_time = entry_time

    def is_present(self) -> bool:
        return self.entry_time is not None

    def __repr__(self):
        return f"Student({self.prenom} {self.nom}, présent={self.is_present()})"
