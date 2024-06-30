import os
import cv2
import face_recognition
import numpy as np
import datetime
import pandas as pd

# Fonction pour charger les images et leurs encodages depuis un répertoire
def load_images_from_directory(directory):
    face_encodings = []
    face_names = []

    for filename in os.listdir(directory):
        if filename.endswith(".jpeg"):
            image_path = os.path.join(directory, filename)
            img = face_recognition.load_image_file(image_path)
            encoding = face_recognition.face_encodings(img)[0]
            face_encodings.append(encoding)
            face_names.append(filename.split(".")[0]) 
            # Utiliser le nom de fichier (sans extension) comme nom du visage
    return np.array(face_encodings), face_names
########### fin fonction chargement des images et leurs ecodages

# Charger les images et les encodages depuis le répertoire "img"
known_face_encodings, known_face_names = load_images_from_directory('img')

listeEtudiant=known_face_names.copy()
# Initialiser la capture vidéo
cap = cv2.VideoCapture(0)

# Seuil pour la similarité de reconnaissance faciale
seuil_de_similarity = 0.4

# Dictionnaire pour stocker les étudiants présents et leurs heures d'entrée
present_students = {}

# Fonction pour traiter la présence
def process_attendance(name, entry_time):
    if name not in present_students:
        present_students[name] = entry_time
        prenom = name.split("_")[0]
        nom = name.split("_")[1]
        print(f"{prenom} {nom} s'est authentifié a la date {entry_time}")
        existing_data = profileEtudiant(present_students)
        print("liste de presence")
        print(existing_data)
        listeEtudiant.remove(name)
def process_missing(name, entry_time):
    if name not in present_students:
        present_students[name] = entry_time
        prenom = name.split("_")[0]
        nom = name.split("_")[1]
        print(f"{prenom} {nom} est absent")
        existing_data = profileEtudiant(present_students)
     
################ fin traitement de la presence

################ Traitement des données de présence 
def profileEtudiant(present_students):
    student_library = []

    for student, entry_time in present_students.items():
        prenom = student.split('_')[0]
        nom = student.split('_')[1]
        date, heure = entry_time.split(' ')
        
        statut = statut1 = None

        # Vérification si l'étudiant est déjà dans student_library
        student_already_present = False
        for info in student_library:
            if prenom == info[0] and nom == info[1] and date == info[2]:
                student_already_present = True
                if info[4]== None :
                    info[4],info[5]=statutEtudiant(heure)
                if info[3]== None :
                    info[3],info[5]=statutEtudiant(heure)
                break

        if not student_already_present:
            ha= datetime.datetime.now().strftime("%H:%M:%S")
            if ha <= "12:00:00" :
                statut,tempRetard = statutEtudiant(heure) 
            else:
                statut,statut1,tempRetard = statutEtudiant1(heure) 
                 
            student_info = [prenom,nom,date,statut,statut1,tempRetard]
            student_library.append(student_info)
 ###################### fin traitement des donnees de l'etudiant 
    
    ############################# creation/transcription de student_library en fichier excel
    excel_filename = 'student_data.xlsx'
    # Créer un DataFrame à partir de la liste student_library
    columns = ['prenom', 'nom', 'date', 'cour_1', 'cour_2', 'tempRetard']
    df = pd.DataFrame(student_library, columns=columns)
    if os.path.isfile(excel_filename):
        existing_data = pd.read_excel(excel_filename)
        # Boucle sur les lignes pour vérifier les correspondances
        for index, row in df.iterrows():
            match_found = False
            for i, existing_row in existing_data.iterrows():
                if (row['prenom'] == existing_row['prenom'] and 
                    row['nom'] == existing_row['nom'] and 
                    row['date'] == existing_row['date']):
                    row['cour_1'] = existing_row['cour_1']
                    existing_data.loc[i] = row  # Remplacer la ligne existante en y ajoutant les nouvelles donnees 
                    match_found = True
                    break

            # Si aucune correspondance trouvée, ajouter une nouvelle ligne contenant le nouveau etudiant
            if not match_found:
                existing_data = existing_data._append(row, ignore_index=True)

        # Sauvegarder les données dans le fichier Excel
        existing_data.to_excel(excel_filename, index=False)
        return existing_data
    else:
        # Si le fichier n'existe pas, sauvegarder simplement les données dans un nouveau fichier
        df.to_excel(excel_filename, index=False)
        return df
########################################## fin fonction transcription en excel
        
# fonction pour le statut de l'etudiant
def statutEtudiant(heure):
    h_minute=int(heure.split(':')[0])*60+int(heure.split(':')[1])
    tempRetard=0
    ha  = datetime.datetime.now().strftime("%H:%M:%S")
    if ha<= "12:00:00":
        if heure < "08:05:00":
            statut = "present" 
        elif "08:05:00" <= heure < "11:00:00":
            statut= "retard"
            tempRetard=h_minute - 485
        elif "11:00:00" <= heure < "12:00:00":
            statut= "absent"
    else:
        if heure < "14:30:00":
            statut = "present" 
        elif "14:30:00" <= heure < "15:00:00":
            statut= "retard"
            tempRetard=h_minute - 870
        else:
            statut= "absent"
    return statut,tempRetard

def statutEtudiant1(heure):
    h_minute=int(heure.split(':')[0])*60+int(heure.split(':')[1])
    tempRetard=0
    statut1 = None
    if heure < "08:05:00":
        statut = "absent" 
    elif "08:05:00" <= heure < "11:00:00":
        statut= "absent"
        tempRetard=h_minute - 485
    elif "11:00:00" <= heure < "14:30:00":
        statut= "absent"
        statut1= "present"
    elif "14:30:00" <= heure < "15:00:00":
        statut= "absent"
        statut1= "retard"
        tempRetard=h_minute - 870
    else:
        statut= "absent"
        statut1= "absent"
    
    return statut,statut1,tempRetard
#---------- fin fonction statut des etudiants

# Boucle principale pour capturer les images de la vidéo
while True:
    ret, frame = cap.read()

    if not ret:
        print("Erreur: Impossible de capturer la vidéo.")
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    # Première étape de reconnaissance : Utiliser la reconnaissance faciale basée sur les encodages faciaux
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        distances = np.linalg.norm(known_face_encodings - face_encoding, axis=1)
        min_distance_index = np.argmin(distances)

        if distances[min_distance_index] < seuil_de_similarity:
            name = known_face_names[min_distance_index]
            process_attendance(name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, "{}".format(name), (left + 6, bottom - 6), font, 0.5, (0, 255, 0), 1)
        else:
            # Deuxième étape de reconnaissance : Utiliser la reconnaissance faciale par cascade
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            min_distance_cascade = float('inf')  # Initialiser la distance minimale avec une valeur infinie
            min_distance_name = "Inconnu"
            
            for (x, y, w, h) in faces:
                # Récupérer la région d'intérêt (ROI) du visage
                face_roi = frame[y:y+h, x:x+w]

                # Convertir la ROI en RGB (face_recognition utilise des images au format RGB)
                rgb_face_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)

                # Trouver l'encodage facial de la ROI
                face_encoding_cascade = face_recognition.face_encodings(rgb_face_roi)

                if len(face_encoding_cascade) > 0:
                    face_encoding_cascade = face_encoding_cascade[0]

                    # Comparer avec les visages connus
                    distances_cascade = np.linalg.norm(known_face_encodings - face_encoding_cascade, axis=1)
                    min_distance_index_cascade = np.argmin(distances_cascade)

                    if distances_cascade[min_distance_index_cascade] < min_distance_cascade:
                        min_distance_cascade = distances_cascade[min_distance_index_cascade]
                        min_distance_name = known_face_names[min_distance_index_cascade]

            if min_distance_cascade < seuil_de_similarity:
                # Si la distance minimale est inférieure au seuil de similarité, la personne est reconnue
                name = min_distance_name
                process_attendance(name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, "{}".format(name), (left + 6, bottom - 6), font, 0.5, (0, 255, 0), 1)
            else:
                # Si la distance minimale est supérieure au seuil de similarité, la personne est inconnue
                cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, "Inconnu", (left + 6, bottom - 6), font, 0.5, (255, 0, 0), 1)

    cv2.imshow('RECONNAISSANCE FACIALE', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
print(listeEtudiant)
for E in listeEtudiant:
    process_missing(E, datetime.datetime.now().strftime("%Y-%m-%d 23:00:00"))
    
listefinale = pd.read_excel("student_data.xlsx")
print(listefinale)

cap.release()
cv2.destroyAllWindows()
