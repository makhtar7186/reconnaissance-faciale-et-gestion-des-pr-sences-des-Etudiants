# attendancestatus.py


class AttendanceStatus:
    """Calcule le statut d'un étudiant selon les plages horaires."""

    # Horaires matin
    MATIN_DEBUT     = "06:30:00"
    MATIN_FIN_RETARD = "11:00:00"
    MATIN_FIN       = "12:00:00"
    # Horaires après-midi
    APREM_DEBUT     = "14:30:00"
    APREM_FIN_RETARD = "15:00:00"

    @staticmethod
    def _minutes_from_time(heure: str) -> int:
        parts = heure.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    @classmethod
    def get_status_matin(cls, heure: str) -> tuple[str, int]:
        """Retourne (statut, tempRetard) pour le cours du matin."""
        temp_retard = 0
        if heure < cls.MATIN_DEBUT:
            statut = "present"
        elif cls.MATIN_DEBUT <= heure < cls.MATIN_FIN_RETARD:
            statut = "retard"
            temp_retard = cls._minutes_from_time(heure) - cls._minutes_from_time(cls.MATIN_DEBUT)
        else:
            statut = "absent"
        return statut, temp_retard

    @classmethod
    def get_status_aprem(cls, heure: str) -> tuple[str, int]:
        """Retourne (statut, tempRetard) pour le cours de l'après-midi."""
        temp_retard = 0
        if heure < cls.APREM_DEBUT:
            statut = "present"
        elif cls.APREM_DEBUT <= heure < cls.APREM_FIN_RETARD:
            statut = "retard"
            temp_retard = cls._minutes_from_time(heure) - 870
        else:
            statut = "absent"
        return statut, temp_retard

  