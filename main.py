import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import threading

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("Sélection frontale", os.path.join(ROOT_DIR, "2_frontal", "1_select_frames_frontale.py")),
    ("Analyse frontale", os.path.join(ROOT_DIR, "2_frontal", "2_extract_frontale.py")),
    ("Résultats frontaux", os.path.join(ROOT_DIR, "2_frontal", "3_results_frontale.py")),
    ("Sélection sagittale", os.path.join(ROOT_DIR, "3_sagittal", "1_select_frames_sagittale.py")),
    ("Analyse sagittale", os.path.join(ROOT_DIR, "3_sagittal", "2_extract_sagittale.py")),
    ("Résultats sagittaux", os.path.join(ROOT_DIR, "3_sagittal", "3_results_sagittale.py")),
    ("Organisation + PDF", os.path.join(ROOT_DIR, "4_Organisation", "4_organise_session.py")),
]

class App:
    def __init__(self, root):
        self.root = root
        root.title("Analyse Drop Jump")
        root.geometry("600x350")
        root.configure(bg="#f5f5f5")

        self.label = tk.Label(root, text="Prêt à lancer l’analyse",
                              font=("Arial", 14), bg="#f5f5f5")
        self.label.pack(pady=20)

        self.progress = ttk.Progressbar(root, orient="horizontal",
                                        length=400, mode="determinate")
        self.progress.pack(pady=20)

        self.percent = tk.Label(root, text="0 %",
                                font=("Arial", 12), bg="#f5f5f5")
        self.percent.pack()

        self.button = tk.Button(root, text="Lancer analyse complète",
                                command=self.start,
                                font=("Arial", 12, "bold"),
                                bg="black", fg="white", padx=20, pady=10)
        self.button.pack(pady=30)

    def run_script(self, path):
        return subprocess.run([sys.executable, path]).returncode == 0

    def pipeline(self):
        total = len(STEPS)

        for i, (name, path) in enumerate(STEPS):
            self.label.config(text=f"Étape : {name}")
            self.root.update_idletasks()

            ok = self.run_script(path)

            if not ok:
                messagebox.showerror("Erreur", f"Erreur sur : {name}")
                self.button.config(state="normal")
                return

            progress_value = int(((i + 1) / total) * 100)
            self.progress["value"] = progress_value
            self.percent.config(text=f"{progress_value} %")

        self.label.config(text="Analyse terminée 🎉")
        messagebox.showinfo("Succès", "Analyse complète terminée")
        self.button.config(state="normal")

    def start(self):
        self.button.config(state="disabled")
        threading.Thread(target=self.pipeline).start()

root = tk.Tk()
app = App(root)
root.mainloop()

