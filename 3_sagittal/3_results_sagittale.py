import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt




# =============================
# 🔗 CHEMINS
# =============================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

CSV = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "angles_sagittal.csv")
PARAMS = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "parametres_selection_sagittale.json")

PNG_GLOBAL = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "SAGITTAL_GLOBAL.png")
PNG_100 = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "SAGITTAL_0_100ms.png")





# =============================
# 📥 Chargement
# =============================
df = pd.read_csv(CSV)


with open(PARAMS,"r") as f:
   p = json.load(f)


frame_contact = p["frame_contact"]
frame_end   = p["frame_takeoff"]
fps         = p["fps"]
frame_100   = frame_contact + int(0.1 * fps)  # fenêtre 100ms




# =============================
# 🔥 IDENTIFICATION DES POINTS CLÉS
# =============================
closest = df.iloc[(df["frame"] - frame_contact).abs().argsort()[:1]].index[0]
IC_knee  = df.loc[closest, "knee_deg_filt10"]
IC_trunk = df.loc[closest, "trunk_deg_filt10"]


df_contact = df.loc[df["frame"] >= frame_contact]
peak_knee_global  = df_contact["knee_deg_filt10"].min()
peak_trunk_global = df_contact["trunk_deg_filt10"].min()


peak_knee_100  = df.loc[df["frame"].between(frame_contact, frame_100), "knee_deg_filt10"].min()
peak_trunk_100 = df.loc[df["frame"].between(frame_contact, frame_100), "trunk_deg_filt10"].min()


# frames associés
f_pknee_global  = df_contact.loc[df_contact["knee_deg_filt10"]  == peak_knee_global,  "frame"].iloc[0]
f_ptrunk_global = df_contact.loc[df_contact["trunk_deg_filt10"] == peak_trunk_global, "frame"].iloc[0]


df_100 = df.loc[df["frame"].between(frame_contact, frame_100)]
f_pknee100  = df_100.loc[df_100["knee_deg_filt10"]  == peak_knee_100,  "frame"].iloc[0]
f_ptrunk100 = df_100.loc[df_100["trunk_deg_filt10"] == peak_trunk_100, "frame"].iloc[0]






# ==========================================================
# 🔷 GRAPH 1 — COMPLET (du contact au décollage)
# ==========================================================
win_full = df[df.frame.between(frame_contact, frame_end)]


plt.figure(figsize=(15,7))
plt.plot(win_full.frame, win_full.knee_deg_filt10, color="orange", label="Genou filtré")
plt.plot(win_full.frame, win_full.trunk_deg_filt10, color="blue", label="Tronc filtré")


# IC
plt.scatter(frame_contact,IC_knee,color="orange",s=140,edgecolor="black")
plt.text(frame_contact,IC_knee+2,f"{IC_knee:.2f}°",fontsize=9)


plt.scatter(frame_contact,IC_trunk,color="blue",s=140,edgecolor="black")
plt.text(frame_contact,IC_trunk+2,f"{IC_trunk:.2f}°",fontsize=9)


# Peaks globaux
plt.scatter(f_pknee_global,peak_knee_global,color="orange",s=160,edgecolor="black",marker="v")
plt.text(f_pknee_global,peak_knee_global+3,f"{peak_knee_global:.2f}°",fontsize=9)


plt.scatter(f_ptrunk_global,peak_trunk_global,color="blue",s=160,edgecolor="black",marker="v")
plt.text(f_ptrunk_global,peak_trunk_global+3,f"{peak_trunk_global:.2f}°",fontsize=9)


# Lignes repères
plt.axvline(frame_contact,color="green",linestyle="--",label="IC")
plt.axvline(frame_100,color="red",linestyle="--",label="100ms")
plt.axvline(frame_end,color="purple",linestyle="--",label="Take-Off")


plt.title("Flexion GENOU + TRONC — Analyse Complète")
plt.xlabel("Frame"); plt.ylabel("Angle (°)")
plt.grid(alpha=.4); plt.legend()
plt.tight_layout(); plt.savefig(PNG_GLOBAL,dpi=300)
plt.show()






# ==========================================================
# 🔷 GRAPH 2 — FENÊTRE 0–100ms
# ==========================================================
win100 = df[df.frame.between(frame_contact, frame_100)]


plt.figure(figsize=(10,6))
plt.plot(win100.frame, win100.knee_deg_filt10, color="orange",label="Genou")
plt.plot(win100.frame, win100.trunk_deg_filt10,color="blue",label="Tronc")


# points + valeurs
plt.scatter(frame_contact,IC_knee,color="orange",s=140,edgecolor="black")
plt.text(frame_contact,IC_knee-4,f"{IC_knee:.2f}°",fontsize=9)


plt.scatter(frame_contact,IC_trunk,color="blue",s=140,edgecolor="black")
plt.text(frame_contact,IC_trunk-2,f"{IC_trunk:.2f}°",fontsize=9)


plt.scatter(f_pknee100,peak_knee_100,color="orange",s=160,marker="v",edgecolor="black")
plt.text(f_pknee100,peak_knee_100+3,f"{peak_knee_100:.2f}°",fontsize=9)


plt.scatter(f_ptrunk100,peak_trunk_100,color="blue",s=160,marker="v",edgecolor="black")
plt.text(f_ptrunk100,peak_trunk_100+3,f"{peak_trunk_100:.2f}°",fontsize=9)


plt.axvline(frame_contact,color="green",linestyle="--", label="IC")
plt.axvline(frame_100,color="red",linestyle="--", label="100ms")




plt.title("Fenêtre 0–100ms — Peaks ciblés")
plt.xlabel("Frame"); plt.ylabel("Angle (°)")
plt.grid(alpha=.4); plt.legend()
plt.tight_layout(); plt.savefig(PNG_100,dpi=300)
plt.show()




print("\n✅ SAGITTAL — 2 GRAPHIQUES GÉNÉRÉS AVEC SUCCÈS")