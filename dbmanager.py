# dbmanager.py

import sqlite3
import datetime
from typing import Optional


class DBManager:
    """Gère la persistance des données de présence via SQLite."""

    def __init__(self, db_path: str = "attendance.db"):
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def _init_db(self):
        """Crée la table si elle n'existe pas encore."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS presences (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    prenom    TEXT    NOT NULL,
                    nom       TEXT    NOT NULL,
                    date      TEXT    NOT NULL,
                    etat    TEXT,
                    
                    tempRetard INTEGER DEFAULT z0,
                    UNIQUE(prenom, nom, date)
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    # ------------------------------------------------------------------
    # Écriture
    # ------------------------------------------------------------------
    def upsert(
        self,
        prenom: str,
        nom: str,
        date: str,
        etat: Optional[str],
        temp_retard: int,
    ):
        """Insère ou met à jour un enregistrement de présence."""
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO presences (prenom, nom, date, etat, tempRetard)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(prenom, nom, date) DO UPDATE SET
                    etat     = excluded.etat,
                    tempRetard = excluded.tempRetard
            """, (prenom, nom, date, etat, temp_retard))

    def save_all(self, student_library: list[list]):
        """Sauvegarde une liste complète d'enregistrements."""
        for row in student_library:
            prenom, nom, date, etat, temp_retard = row
            self.upsert(prenom, nom, date, etat, temp_retard or 0)

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------
    def get_all(self) -> list[dict]:
        """Retourne tous les enregistrements sous forme de liste de dicts."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT prenom, nom, date, etat, tempRetard "
                "FROM presences ORDER BY date DESC, nom ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_by_date(self, date: str) -> list[dict]:
        """Retourne les présences d'une date donnée (format YYYY-MM-DD)."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT prenom, nom, date, etat, tempRetard "
                "FROM presences WHERE date = ? ORDER BY nom ASC",
                (date,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_dates(self) -> list[str]:
        """Retourne la liste des dates distinctes enregistrées."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT date FROM presences ORDER BY date DESC"
            ).fetchall()
        return [r[0] for r in rows]

    def get_stats(self) -> dict:
        """Retourne des statistiques globales."""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(DISTINCT prenom || nom) FROM presences").fetchone()[0]
            presents = conn.execute(
                "SELECT COUNT(*) FROM presences WHERE etat = 'present'"
            ).fetchone()[0]
            absents = conn.execute(
                "SELECT COUNT(*) FROM presences WHERE etat = 'absent'"
            ).fetchone()[0]
            retards = conn.execute(
                "SELECT COUNT(*) FROM presences WHERE etat = 'retard'"
            ).fetchone()[0]
        return {
            "total_etudiants": total,
            "presents": presents,
            "absents": absents,
            "retards": retards,
        }
