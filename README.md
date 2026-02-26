# 🎓 Système de Reconnaissance Faciale et Gestion des Présences

Système automatisé de gestion des présences étudiantes basé sur la **reconnaissance faciale en temps réel** via webcam. Le système détecte les visages, les identifie, enregistre les heures d'arrivée et génère un rapport de présence au format Excel.

---

## 📁 Structure du projet

```
reconnaissance-faciale/
│
├── img/                        # Images d'entraînement des étudiants
│   ├── prenom_nom.jpeg
│   └── ...
│
├── attendance.db               ## generer automatiquement
├── attendancemanager.py        ## Orchestre la gestion de la présence des étudiants
├── attendancestatus.py         ## calcule du statut de la personne
├── faceapp.py                  ## interface de l'application
├── facerecognizer.py           ## reconnaisance fasciale
├── dbmanager.py                ## pour creer la base de donnee sqlite
├── student.py
├── videoprocessor.py      ### demarer la webcam
├── Main.py                 # Script principal 
├── haarcascade_frontalface_default.xml  ## modele faceId
└── README.md
```

---

## ⚙️ Prérequis

- Python 3.10+
- Une webcam fonctionnelle

---

## 📦 Installation des dépendances

```bash
pip install opencv-python face-recognition numpy pandas openpyxl
```

> Si `face-recognition` échoue à l'installation, installe d'abord `cmake` et `dlib` :
> ```bash
> pip install cmake
> pip install dlib
> pip install face-recognition
> ```

---

## 🚀 Lancement

1. **Ajouter les photos des étudiants** dans le dossier `img/` au format :
   ```
   prenom_nom.jpeg
   ```
   > Exemple : `Alice_Dupont.jpeg`, `Mohamed_Benali.jpeg`

2. **Lancer le script :**
   ```bash
   python Main_POO.py
   ```

3. **Quitter** : appuyer sur `q` dans la fenêtre vidéo.

Une fois quittée, le système marque automatiquement les étudiants non détectés comme **absents** et génère/met à jour le fichier `student_data.xlsx`.

---

## 🏗️ Architecture POO

Le projet est structuré autour de **5 classes** avec des responsabilités distinctes :

| Classe | Rôle |
|---|---|
| `Student` | Représente un étudiant (nom, prénom, heure d'entrée) |
| `AttendanceStatus` | Calcule le statut selon les plages horaires |
| `DBManager` | Gère la lecture/écriture du fichier attendance.db |
| `AttendanceManager` | Orchestre la présence et les absences |
| `FaceRecognizer` | Charge les encodages et identifie les visages |
| `VideoProcessor` | Gère la boucle vidéo et l'affichage |

---

## 🕐 Logique des statuts

### Matin (avant 12h00)

| Heure d'arrivée | Statut |
|---|---|
| Avant 08h05 | ✅ Présent |
| 08h05 – 11h00 | ⏰ Retard |
| Après 11h00 | ❌ Absent |


---

## 📊 Fichier Excel généré

Le fichier `student_data.xlsx` contient les colonnes suivantes :

| prenom | nom | date | etat| tempRetard |
|---|---|---|---|---|---|
| Alice | Dupont | 2024-10-15 | présent| 0 |
| Mohamed | Benali | 2024-10-15 | retard | 12 |

- **`tempRetard`** : nombre de minutes de retard (0 si pas de retard)
- Le fichier est mis à jour à chaque nouvelle détection et en fin de session

---

## 🔍 Fonctionnement de la reconnaissance

Le système utilise **deux niveaux de détection** :

1. **Encodage facial direct** (`face_recognition`) — méthode principale, précise et rapide
2. **Cascade de Haar** (`OpenCV`) — méthode de secours si la première échoue (angles, éclairage difficile)

Le seuil de similarité est fixé à `0.4` (modifiable dans `main()`). Plus la valeur est basse, plus la reconnaissance est stricte.

---

## 📸 Conseils pour les photos d'entraînement

- Utiliser des photos **nettes**, bien éclairées, de face
- Une seule personne par photo
- Format **JPEG** recommander
- Nommage strict : `prenom_nom.jpeg` (avec underscore `_` comme séparateur)

---

## 🛠️ Personnalisation

Dans la fonction `main()` de `Main.py`, tu peux modifier :

```python
IMAGE_DIR = "img"           # Dossier contenant les photos
SIMILARITY_THRESHOLD = 0.4  # Seuil de reconnaissance (0.0 = strict, 1.0 = permissif)
```
