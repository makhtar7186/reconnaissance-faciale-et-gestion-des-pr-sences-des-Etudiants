# facerecognizer.py

import os
import cv2
import face_recognition
import numpy as np


class FaceRecognizer:
    """Charge les encodages faciaux et identifie les visages dans une frame."""

    def __init__(self, image_directory: str, similarity_threshold: float = 0.4):
        self.threshold = similarity_threshold
        self.known_encodings: np.ndarray = np.array([])
        self.known_names: list[str] = []
        self.known_encodings, self.known_names = self._load_images(image_directory)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    # ------------------------------------------------------------------
    # Chargement des images
    # ------------------------------------------------------------------
    def _load_images(self, directory: str) -> tuple[np.ndarray, list[str]]:
        encodings, names = [], []
        if not os.path.isdir(directory):
            print(f"⚠️  Dossier introuvable : {directory}")
            return np.array([]), []

        for filename in os.listdir(directory):
            if filename.lower().endswith(".jpeg") or filename.lower().endswith(".jpg") or filename.lower().endswith(".png") or filename.lower().endswith(".heic"):
                path = os.path.join(directory, filename)
                img = face_recognition.load_image_file(path)
                enc = face_recognition.face_encodings(img)
                if enc:
                    encodings.append(enc[0])
                    names.append(os.path.splitext(filename)[0])
                else:
                    print(f"⚠️  Aucun visage détecté dans {filename}")

        print(f"✅ {len(names)} étudiant(s) chargé(s) : {names}")
        return np.array(encodings), names

    # ------------------------------------------------------------------
    # Reconnaissance
    # ------------------------------------------------------------------
    def _best_match(self, encoding: np.ndarray) -> tuple[str | None, float]:
        """Retourne le meilleur nom et sa distance par rapport à l'encodage."""
        if len(self.known_encodings) == 0:
            return None, float("inf")
        distances = np.linalg.norm(self.known_encodings - encoding, axis=1)
        idx = np.argmin(distances)
        return self.known_names[idx], float(distances[idx])

    def identify_faces(self, frame: np.ndarray) -> list[tuple[str, tuple]]:
        """
        Identifie les visages dans une frame.
        Retourne une liste de (nom_ou_Inconnu, (top, right, bottom, left)).
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)
        results = []

        for (top, right, bottom, left), enc in zip(locations, encodings):
            name, distance = self._best_match(enc)

            # Méthode 1 : encodage direct
            if distance < self.threshold:
                results.append((name, (top, right, bottom, left)))
                continue

            # Méthode 2 : cascade Haar + ré-encodage de la ROI
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces_cascade = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            best_name, best_dist = "Inconnu", float("inf")
            for (x, y, w, h) in faces_cascade:
                roi = cv2.cvtColor(frame[y: y + h, x: x + w], cv2.COLOR_BGR2RGB)
                roi_enc = face_recognition.face_encodings(roi)
                if roi_enc:
                    candidate, dist = self._best_match(roi_enc[0])
                    if dist < best_dist:
                        best_dist = dist
                        best_name = candidate

            final_name = best_name if best_dist < self.threshold else "Inconnu"
            results.append((final_name, (top, right, bottom, left)))

        return results
