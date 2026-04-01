# videoprocessor.py

import cv2
import datetime
import numpy as np
from facerecognizer import FaceRecognizer
from attendancemanager import AttendanceManager


class VideoProcessor:
    """
    Gère la capture vidéo, la reconnaissance et l'enregistrement des présences.

    Deux modes d'utilisation :
    ──────────────────────────
    1. Mode autonome (console)  → appeler run()  : boucle bloquante avec fenêtre cv2
    2. Mode Tkinter             → appeler start() / get_annotated_frame() / stop()
       L'interface récupère les frames annotées via get_annotated_frame() et les
       affiche elle-même — VideoProcessor ne crée aucune fenêtre dans ce cas.
    """

    def __init__(self, recognizer: FaceRecognizer, attendance: AttendanceManager):
        self.recognizer = recognizer
        self.attendance = attendance
        self.url = "http://192.168.1.8:4747/video"  # Adresse donnée par l'app
        #self.cap = cv2.VideoCapture(self.url)

        self.cap  = cv2.VideoCapture(0)
        self.running    = False

    # ──────────────────────────────────────────────────────────────────
    # Dessin des annotations sur la frame
    # ──────────────────────────────────────────────────────────────────
    def _draw_label(self, frame: np.ndarray, name: str, box: tuple) -> None:
        top, right, bottom, left = box
        color = (0, 220, 0) if name != "Inconnu" else (0, 0, 220)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 22), (right, bottom), color, cv2.FILLED)
        cv2.putText(
            frame, name, (left + 6, bottom - 5),
            cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1
        )

    # ──────────────────────────────────────────────────────────────────
    # Traitement d'une seule frame (logique commune aux deux modes)
    # ──────────────────────────────────────────────────────────────────
    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Détecte les visages, enregistre les présences et annote la frame.
        Retourne la frame annotée.
        """
        detections = self.recognizer.identify_faces(frame)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for name, box in detections:
            if name != "Inconnu":
                self.attendance.process_presence(name, now)
            self._draw_label(frame, name, box)

        # Overlay horloge
        clock = datetime.datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, clock, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return frame

    # ──────────────────────────────────────────────────────────────────
    # Mode autonome (console)
    # ──────────────────────────────────────────────────────────────────
    def run(self):
        """Démarre la boucle principale bloquante avec fenêtre OpenCV. Quitter avec 'q'."""
        self.running = True
        print("🎥 Reconnaissance faciale démarrée. Appuyez sur 'q' pour quitter.")

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Impossible de lire la webcam.")
                break

            annotated = self._process_frame(frame)
            cv2.imshow("Reconnaissance Faciale — [q] pour quitter", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.running = False

        self._shutdown()

    # ──────────────────────────────────────────────────────────────────
    # Mode Tkinter
    # ──────────────────────────────────────────────────────────────────
    def start(self):
        """Active la capture (sans boucle bloquante) pour le mode Tkinter."""
        self.running = True

    def stop(self):
        """Arrête la capture et libère la webcam."""
        self.running = False
        self._shutdown()

    def get_annotated_frame(self) -> np.ndarray | None:
        """
        Capture une frame, détecte les visages, enregistre les présences
        et retourne la frame annotée prête à afficher dans Tkinter.
        Retourne None si la webcam n'est pas disponible.
        """
        if not self.running or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return self._process_frame(frame)

    # ──────────────────────────────────────────────────────────────────
    # Fin de session
    # ──────────────────────────────────────────────────────────────────
    def finalize(self):
        """Marque les absents et affiche le rapport final en console."""
        print("\n📊 Traitement des absences en cours...")
        self.attendance.process_absences()
        records = self.attendance.get_all_records()
        print("\n📋 Rapport final :")
        for r in records:
            print(r)

    def _shutdown(self):
        self.cap.release()
        cv2.destroyAllWindows()
