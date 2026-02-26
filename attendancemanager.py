# attendancemanager.py

import datetime
from student import Student
from attendancestatus import AttendanceStatus
from dbmanager import DBManager


class AttendanceManager:
    """Orchestre la gestion de la présence des étudiants."""

    def __init__(self, known_students: list[Student], db_path: str = "attendance.db"):
        self.known_students: dict[str, Student] = {s.full_name: s for s in known_students}
        self.absent_students: list[str] = list(self.known_students.keys())
        self.db = DBManager(db_path)
        # Callback optionnel pour notifier l'interface (ex : Tkinter)
        self.on_update = None

    # ------------------------------------------------------------------
    # Présence en temps réel
    # ------------------------------------------------------------------
    def process_presence(self, name: str, entry_time: str):
        """Marque un étudiant comme présent s'il ne l'est pas déjà."""
        student = self.known_students.get(name)
        if student and not student.is_present():
            student.mark_present(entry_time)
            if name in self.absent_students:
                self.absent_students.remove(name)
            print(f"✅ {student.prenom} {student.nom} authentifié à {entry_time}")
            self._build_and_save()
            if self.on_update:
                self.on_update()

    def process_absences(self):
        """Marque les étudiants non détectés comme absents en fin de session."""
        absent_time = datetime.datetime.now().strftime("%Y-%m-%d 23:00:00")
        for name in list(self.absent_students):
            student = self.known_students[name]
            student.mark_present(absent_time)
            print(f"❌ {student.prenom} {student.nom} marqué absent")
        self._build_and_save()
        if self.on_update:
            self.on_update()

    # ------------------------------------------------------------------
    # Construction + sauvegarde
    # ------------------------------------------------------------------
    def _build_and_save(self):
        """Calcule les statuts de tous les étudiants présents et les sauvegarde."""
        student_library = []
        now = datetime.datetime.now().strftime("%H:%M:%S")

        for student in self.known_students.values():
            if not student.is_present():
                continue

            date, heure = student.entry_time.split(" ")

            
            statut, temp_retard = AttendanceStatus.get_status_matin(heure)
                
                
   
            student_library.append(
                [student.prenom, student.nom, date, statut, temp_retard]
            )

        self.db.save_all(student_library)

    # ------------------------------------------------------------------
    # Accès aux données (pour l'interface)
    # ------------------------------------------------------------------
    def get_all_records(self) -> list[dict]:
        return self.db.get_all()

    def get_records_by_date(self, date: str) -> list[dict]:
        return self.db.get_by_date(date)

    def get_dates(self) -> list[str]:
        return self.db.get_dates()

    def get_stats(self) -> dict:
        return self.db.get_stats()
