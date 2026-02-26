# app.py  —  Interface Tkinter pour la gestion des présences

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import datetime
from PIL import Image, ImageTk

from student import Student
from facerecognizer import FaceRecognizer
from attendancemanager import AttendanceManager
from videoprocessor import VideoProcessor


# ─────────────────────────────────────────────────────────────────────────────
# Constantes de style
# ─────────────────────────────────────────────────────────────────────────────
BG_DARK    = "#1a1a2e"
BG_PANEL   = "#16213e"
BG_CARD    = "#0f3460"
ACCENT     = "#e94560"
ACCENT2    = "#00b4d8"
TEXT_LIGHT = "#eaeaea"
TEXT_MUTED = "#8892a4"
GREEN      = "#2ecc71"
ORANGE     = "#f39c12"
RED        = "#e74c3c"

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_HEAD  = ("Segoe UI", 13, "bold")
FONT_BODY  = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
FONT_BADGE = ("Segoe UI", 10, "bold")


# ─────────────────────────────────────────────────────────────────────────────
# Fenêtre principale
# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    IMAGE_DIR = "img"
    THRESHOLD = 0.4
    DB_PATH   = "attendance.db"
    CAM_W, CAM_H = 440, 300   # taille d'affichage du flux dans l'interface

    def __init__(self):
        super().__init__()
        self.title("Système de Présence — Reconnaissance Faciale")
        self.geometry("1280x760")
        self.minsize(1100, 680)
        self.configure(bg=BG_DARK)

        # ── Instanciation des classes métier ───────────────────────────
        self.recognizer = FaceRecognizer(self.IMAGE_DIR, self.THRESHOLD)

        # AttendanceManager reçoit la liste des étudiants connus
        # (déduits des noms uniques chargés par FaceRecognizer)
        unique_names = list(dict.fromkeys(self.recognizer.known_names))
        students = [Student(n) for n in unique_names]
        self.attendance = AttendanceManager(students, self.DB_PATH)

        # VideoProcessor orchestre caméra + reconnaissance + présences
        self.processor = VideoProcessor(self.recognizer, self.attendance)

        # Callback : AttendanceManager notifie l'UI après chaque détection
        self.attendance.on_update = self._schedule_refresh

        # ── Thread de capture (démarré uniquement quand l'user clique) ─
        self._cam_thread: threading.Thread | None = None

        # ── Construction de l'interface ────────────────────────────────
        self._build_ui()
        self._refresh_table()
        self._refresh_stats()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═══════════════════════════════════════════════════════════════════
    # Construction de l'UI
    # ═══════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # Barre de titre
        header = tk.Frame(self, bg=BG_PANEL, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🎓  Gestion des Présences",
                 font=FONT_TITLE, bg=BG_PANEL, fg=TEXT_LIGHT).pack(side="left", padx=24, pady=12)
        self.lbl_clock = tk.Label(header, text="", font=FONT_BODY, bg=BG_PANEL, fg=TEXT_MUTED)
        self.lbl_clock.pack(side="right", padx=24)
        self._tick_clock()

        # Corps principal
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        left = tk.Frame(body, bg=BG_DARK, width=460)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True)

        self._build_camera_panel(left)
        self._build_controls(left)
        self._build_stats_bar(right)
        self._build_table(right)

    # ── Panneau caméra ────────────────────────────────────────────────
    def _build_camera_panel(self, parent):
        card = tk.Frame(parent, bg=BG_CARD)
        card.pack(fill="x", pady=(0, 10))
        tk.Label(card, text="📷  Flux Caméra", font=FONT_HEAD,
                 bg=BG_CARD, fg=TEXT_LIGHT).pack(pady=(10, 6))
        self.lbl_cam = tk.Label(card, bg="#000000",
                                 width=self.CAM_W, height=self.CAM_H)
        self.lbl_cam.pack(padx=10, pady=(0, 10))
        self._show_placeholder()

    def _show_placeholder(self):
        img = Image.new("RGB", (self.CAM_W, self.CAM_H), "#111111")
        self._ph = ImageTk.PhotoImage(img)
        self.lbl_cam.configure(image=self._ph)

    # ── Contrôles ─────────────────────────────────────────────────────
    def _build_controls(self, parent):
        card = tk.Frame(parent, bg=BG_CARD)
        card.pack(fill="x")
        tk.Label(card, text="⚙️  Contrôles", font=FONT_HEAD,
                 bg=BG_CARD, fg=TEXT_LIGHT).pack(pady=(10, 8))

        btn_f = tk.Frame(card, bg=BG_CARD)
        btn_f.pack(padx=14, pady=(0, 14))

        self.btn_start = self._btn(btn_f, "▶  Démarrer caméra",
                                    ACCENT2, self._start_camera)
        self.btn_start.grid(row=0, column=0, padx=6, pady=4, sticky="ew")

        self.btn_stop = self._btn(btn_f, "⏹  Arrêter",
                                   ACCENT, self._stop_camera, state="disabled")
        self.btn_stop.grid(row=0, column=1, padx=6, pady=4, sticky="ew")

        self._btn(btn_f, "✅  Finaliser session",
                  "#8e44ad", self._finalize).grid(row=1, column=0, padx=6, pady=4, sticky="ew")
        self._btn(btn_f, "🔄  Rafraîchir",
                  "#27ae60", self._refresh_all).grid(row=1, column=1, padx=6, pady=4, sticky="ew")

        btn_f.columnconfigure(0, weight=1)
        btn_f.columnconfigure(1, weight=1)

        # Filtre par date
        flt = tk.Frame(card, bg=BG_CARD)
        flt.pack(padx=14, pady=(0, 14), fill="x")
        tk.Label(flt, text="Filtrer par date :", font=FONT_SMALL,
                 bg=BG_CARD, fg=TEXT_MUTED).pack(side="left")
        self.date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        tk.Entry(flt, textvariable=self.date_var, font=FONT_SMALL, width=13,
                 bg=BG_PANEL, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT,
                 relief="flat").pack(side="left", padx=8)
        self._btn(flt, "Filtrer", BG_PANEL, self._filter_by_date, width=8).pack(side="left")
        self._btn(flt, "Tout",    BG_PANEL, self._refresh_table,  width=5).pack(side="left", padx=4)

    # ── Barre de stats ────────────────────────────────────────────────
    def _build_stats_bar(self, parent):
        bar = tk.Frame(parent, bg=BG_DARK)
        bar.pack(fill="x", pady=(0, 12))
        self.stat_cards = {}
        for key, label, color in [
            ("total",    "👤 Total",    BG_CARD),
            ("presents", "✅ Présents", "#1a472a"),
            ("retards",  "⏰ Retards",  "#7d4e00"),
            ("absents",  "❌ Absents",  "#4a1010"),
        ]:
            c = tk.Frame(bar, bg=color)
            c.pack(side="left", expand=True, fill="both", padx=5, ipady=8)
            tk.Label(c, text=label, font=FONT_SMALL, bg=color, fg=TEXT_MUTED).pack()
            lbl = tk.Label(c, text="—", font=FONT_TITLE, bg=color, fg=TEXT_LIGHT)
            lbl.pack()
            self.stat_cards[key] = lbl

    # ── Tableau des présences ─────────────────────────────────────────
    def _build_table(self, parent):
        card = tk.Frame(parent, bg=BG_PANEL)
        card.pack(fill="both", expand=True)
        tk.Label(card, text="📋  Liste des Présences", font=FONT_HEAD,
                 bg=BG_PANEL, fg=TEXT_LIGHT).pack(anchor="w", padx=14, pady=(10, 6))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                         background=BG_DARK, fieldbackground=BG_DARK,
                         foreground=TEXT_LIGHT, rowheight=28, font=FONT_BODY)
        style.configure("Dark.Treeview.Heading",
                         background=BG_CARD, foreground=TEXT_LIGHT,
                         font=FONT_BADGE, relief="flat")
        style.map("Dark.Treeview", background=[("selected", ACCENT)])

        frame_tree = tk.Frame(card, bg=BG_PANEL)
        frame_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols    = ("prenom", "nom", "date", "etat", "retard")
        headers = ("Prénom", "Nom", "Date", "État", "Retard (min)")
        self.tree = ttk.Treeview(frame_tree, columns=cols,
                                  show="headings", style="Dark.Treeview")
        for col, head, w in zip(cols, headers, [100, 100, 100, 110, 110, 110]):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor="center")

        self.tree.tag_configure("present", foreground=GREEN)
        self.tree.tag_configure("retard",  foreground=ORANGE)
        self.tree.tag_configure("absent",  foreground=RED)

        sb = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    # ═══════════════════════════════════════════════════════════════════
    # Gestion caméra — délégation complète à VideoProcessor
    # ═══════════════════════════════════════════════════════════════════
    def _start_camera(self):
        """Démarre VideoProcessor en mode Tkinter et lance la boucle d'affichage."""
        self.processor.start()                         # ← VideoProcessor.start()
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self._cam_thread = threading.Thread(
            target=self._camera_loop, daemon=True
        )
        self._cam_thread.start()

    def _stop_camera(self):
        """Arrête VideoProcessor et remet le placeholder."""
        self.processor.stop()                          # ← VideoProcessor.stop()
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self._show_placeholder()

    def _camera_loop(self):
        """
        Tourne dans un thread secondaire.
        Demande une frame annotée à VideoProcessor et l'affiche dans le Label Tkinter.
        Toute la logique de détection/présence est dans VideoProcessor._process_frame().
        """
        while self.processor.running:
            frame = self.processor.get_annotated_frame()   # ← VideoProcessor.get_annotated_frame()
            if frame is None:
                break

            from PIL import Image as PILImage
            import cv2
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            photo = ImageTk.PhotoImage(
                PILImage.fromarray(frame_rgb).resize((self.CAM_W, self.CAM_H))
            )
            # Mise à jour du label dans le thread Tkinter
            self.lbl_cam.configure(image=photo)
            self.lbl_cam.image = photo   # référence pour éviter le GC

    # ═══════════════════════════════════════════════════════════════════
    # Tableau & Stats — délégation à AttendanceManager
    # ═══════════════════════════════════════════════════════════════════
    def _refresh_table(self, records=None):
        """Rafraîchit le tableau via AttendanceManager.get_all_records()."""
        if records is None:
            records = self.attendance.get_all_records()   # ← AttendanceManager

        for row in self.tree.get_children():
            self.tree.delete(row)

        for r in records:
            c1  = r.get("etat") or "—"
            
            tag = c1 if c1 in ("present", "retard", "absent") else "absent"
            self.tree.insert("", "end", values=(
                r["prenom"], r["nom"], r["date"],
                c1, r.get("tempRetard", 0)
            ), tags=(tag,))

    def _refresh_stats(self):
        """Rafraîchit les cartes de stats via AttendanceManager.get_stats()."""
        stats = self.attendance.get_stats()              # ← AttendanceManager
        self.stat_cards["total"].configure(text=str(stats["total_etudiants"]))
        self.stat_cards["presents"].configure(text=str(stats["presents"]))
        self.stat_cards["retards"].configure(text=str(stats["retards"]))
        self.stat_cards["absents"].configure(text=str(stats["absents"]))

    def _refresh_all(self):
        self._refresh_table()
        self._refresh_stats()

    def _filter_by_date(self):
        date = self.date_var.get().strip()
        if not date:
            messagebox.showwarning("Date vide", "Veuillez saisir une date (YYYY-MM-DD).")
            return
        records = self.attendance.get_records_by_date(date)  # ← AttendanceManager
        self._refresh_table(records)

    def _schedule_refresh(self):
        """Appelé depuis un thread secondaire → planifie le refresh dans le thread Tkinter."""
        self.after(0, self._refresh_all)

    # ═══════════════════════════════════════════════════════════════════
    # Finalisation — délégation à VideoProcessor.finalize()
    # ═══════════════════════════════════════════════════════════════════
    def _finalize(self):
        confirm = messagebox.askyesno(
            "Finaliser la session",
            "Arrêter la caméra et marquer les étudiants non détectés comme absents ?"
        )
        if not confirm:
            return
        self._stop_camera()
        self.processor.finalize()     # ← VideoProcessor.finalize() → AttendanceManager.process_absences()
        self._refresh_all()
        messagebox.showinfo("Session terminée", "Les absences ont été enregistrées.")

    # ═══════════════════════════════════════════════════════════════════
    # Utilitaires
    # ═══════════════════════════════════════════════════════════════════
    def _btn(self, parent, text, color, command, state="normal", width=16):
        return tk.Button(parent, text=text, font=FONT_BADGE,
                         bg=color, fg=TEXT_LIGHT, activebackground=color,
                         activeforeground=TEXT_LIGHT, relief="flat",
                         cursor="hand2", command=command,
                         state=state, width=width, pady=6)

    def _tick_clock(self):
        now = datetime.datetime.now().strftime("%A %d %B %Y  —  %H:%M:%S")
        self.lbl_clock.configure(text=now)
        self.after(1000, self._tick_clock)

    def _on_close(self):
        self.processor.stop()    # ← libère proprement la webcam
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
