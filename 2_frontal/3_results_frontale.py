import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cv2




# ============================
# CONFIG
# ============================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
VIDEO_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "CMJ_frontale.mp4")
CSV_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "angles_valgus.csv")
FRAMES_DIR = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "frames_peaks_frontale")
SUMMARY_CSV_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "summary_valgus.csv")
PARAMS_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "parametres_selection_frontale.json")


os.makedirs(FRAMES_DIR, exist_ok=True)




def rotate_frame(frame, angle):
   if angle == 90: return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
   elif angle == 180: return cv2.rotate(frame, cv2.ROTATE_180)
   elif angle == 270: return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
   return frame




# ============================
# MAIN
# ============================
def main():


   # ---- paramètres ----
   with open(PARAMS_PATH, "r") as f:
       params = json.load(f)


   rotation = params["rotation"]
   frame_start = params["frame_contact"]
   fps = params["fps"]
   frame_100 = frame_start + int(0.100 * fps)  # fenêtre 100ms
   frame_end = params["frame_takeoff"]


   # ---- CSV ----
   df = pd.read_csv(CSV_PATH)
   df["valgus_droite"] = df["angle_droite_signed_filt10"]
   df["valgus_gauche"] = df["angle_gauche_signed_filt10"]


   # =======================
   # 🔥 Identification des valeurs
   # =======================
   # Frame valide la plus proche de frame_start
   closest = df.iloc[(df["frame"] - frame_start).abs().argsort()[:1]].index[0]
   IC_R = df.loc[closest, "valgus_droite"]
   IC_L = df.loc[closest, "valgus_gauche"]

   peak_R_100 = df.loc[df["frame"].between(frame_start, frame_100)]["valgus_droite"].min()
   peak_L_100 = df.loc[df["frame"].between(frame_start, frame_100)]["valgus_gauche"].min()

   peak_R_global = df.loc[df["frame"] >= frame_start, "valgus_droite"].min()
   peak_L_global = df.loc[df["frame"] >= frame_start, "valgus_gauche"].min()


   # ==========================
   # 🔥 GRAPH 1 — Courbe complète
   # ==========================
   fig, ax = plt.subplots(figsize=(15,7))


   ax.fill_between(df["frame"],-60,0,color="red",alpha=0.1,label="Valgus")
   ax.fill_between(df["frame"],0,60,color="blue",alpha=0.1,label="Varus")


   ax.plot(df["frame"],df["valgus_droite"],color="orange",label="Droite filtré")
   ax.plot(df["frame"],df["valgus_gauche"],color="purple",label="Gauche filtré")


   # --- visualisation des événements ---
   ax.axvline(frame_start,color="green",linestyle="--",linewidth=2,label="IC")
   ax.axvline(frame_100,color="red",linestyle="--",linewidth=2,label="100 ms")
   ax.axvline(frame_end,color="orange",linestyle="--",linewidth=2,label="Take-off")


   # --- pics ---
   ax.scatter(frame_start,IC_R,color="orange",s=120,edgecolor="black")
   ax.text(frame_start, IC_R+5, f"{IC_R:.2f}°", fontsize=9)


   ax.scatter(frame_start,IC_L,color="purple",s=120,edgecolor="black")
   ax.text(frame_start, IC_L-6, f"{IC_L:.2f}°", fontsize=9)

   df_contact = df.loc[df["frame"] >= frame_start]
   ax.scatter(df_contact.loc[df_contact["valgus_droite"].idxmin(), "frame"], peak_R_global, color="orange", s=140,
              edgecolor="black")
   ax.text(df_contact.loc[df_contact["valgus_droite"].idxmin(), "frame"], peak_R_global + 5, f"{peak_R_global:.2f}°",
           fontsize=9)

   ax.scatter(df_contact.loc[df_contact["valgus_gauche"].idxmin(), "frame"], peak_L_global, color="purple", s=140,
              edgecolor="black")
   ax.text(df_contact.loc[df_contact["valgus_gauche"].idxmin(), "frame"], peak_L_global - 6, f"{peak_L_global:.2f}°",
           fontsize=9)

   # --- titres & style ---
   ax.set_title("Déviation frontale — IC, Peaks Globaux & 0-100ms")
   ax.set_ylabel("Valgus (−) / Varus (+) (°)")
   ax.set_xlabel("Frame")
   ax.legend(loc="center left",bbox_to_anchor=(1.02,0.5))
   ax.grid(alpha=0.3)
   plt.tight_layout()
   plt.savefig(os.path.join(BASE_DIR,"1_Fichiers_Vidéos","FRONTAL_GLOBAL.png"),dpi=300)
   plt.show()




   # ==========================
   # 🔥 GRAPH 2 — Fenêtre 0–100ms uniquement
   # ==========================
   win=df[df["frame"].between(frame_start,frame_100)]


   fig,ax=plt.subplots(figsize=(10,6))
   ax.plot(win["frame"],win["valgus_droite"],color="orange",label="Droite")
   ax.plot(win["frame"],win["valgus_gauche"],color="purple",label="Gauche")


   ax.scatter(frame_start,IC_R,color="orange",s=120,edgecolor="black")
   ax.text(frame_start, IC_R-1, f"{IC_R:.2f}°", fontsize=9)


   ax.scatter(frame_start,IC_L,color="purple",s=120,edgecolor="black")
   ax.text(frame_start, IC_L+1, f"{IC_L:.2f}°", fontsize=9)

   ax.scatter(win.loc[win["valgus_droite"].idxmin(), "frame"], peak_R_100, color="orange", s=140, edgecolor="black")
   ax.text(win.loc[win["valgus_droite"].idxmin(), "frame"], peak_R_100 - 1, f"{peak_R_100:.2f}°", fontsize=9)

   ax.scatter(win.loc[win["valgus_gauche"].idxmin(), "frame"], peak_L_100, color="purple", s=140, edgecolor="black")
   ax.text(win.loc[win["valgus_gauche"].idxmin(), "frame"], peak_L_100 + 1, f"{peak_L_100:.2f}°", fontsize=9)


   ax.axvline(frame_start,color="green",linestyle="--")
   ax.axvline(frame_100,color="red",linestyle="--")


   ax.set_title("Fenêtre IC → 100ms — Peaks ciblés")
   ax.set_xlabel("Frame")
   ax.set_ylabel("Valgus (°)")
   ax.grid(alpha=0.4)
   ax.legend()
   plt.tight_layout()
   plt.savefig(os.path.join(BASE_DIR,"1_Fichiers_Vidéos","FRONTAL_WINDOW_100ms.png"),dpi=300)
   plt.show()


   print("\n✅ FRONTAL — 2 GRAPHIQUES GÉNÉRÉS AVEC SUCCÈS")




if __name__ == "__main__":
   main()


