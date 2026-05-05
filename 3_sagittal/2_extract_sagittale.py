import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import json
import math
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt


# ============================================================
# CONFIG
# ============================================================
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

VIDEO_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "CMJ_sagittale.mp4")
PARAMS_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "parametres_selection_sagittale.json")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "sagittal_pose_angles_annotated.mp4")
CSV_OUTPUT = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "angles_sagittal.csv")

PNG_KNEE = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "sagittal_knee_10Hz.png")
PNG_TRUNK = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "sagittal_trunk_10Hz.png")
PNG_KNEE_100 = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "sagittal_knee_0_100ms.png")
PNG_TRUNK_100 = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "sagittal_trunk_0_100ms.png")





# ============================================================
# Charger paramètres
# ============================================================
with open(PARAMS_PATH, "r") as f:
   params = json.load(f)


frame_contact = params["frame_contact"]
frame_end = params["frame_takeoff"]
frame_start = max(0, frame_contact - 15)
rotation = params["rotation"]
fps_forced = params["fps"]




# ============================================================
# Fonctions utilitaires
# ============================================================
def rotate_frame(frame, angle):
   if angle == 90:
       return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
   if angle == 180:
       return cv2.rotate(frame, cv2.ROTATE_180)
   if angle == 270:
       return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
   return frame




def angle_between(v1, v2):
   cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
   return np.degrees(np.arccos(np.clip(cosang, -1, 1)))




# ============================================================
# Filtre BUTTERWORTH 10 Hz
# ============================================================
def butterworth_filter(data, fps, cutoff=10.0, order=4):
    data = np.asarray(data, dtype=float)
    if len(data) < 16:
        print(f"⚠️ Signal trop court ({len(data)} frames) — filtre ignoré")
        return data
    nyquist = 0.5 * fps
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype="low")
    return filtfilt(b, a, data, padlen=min(len(data)-1, 15))




# ============================================================
# Initialisation MediaPipe
# ============================================================
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles  # style du squelette


pose = mp_pose.Pose(
   static_image_mode=False,
   model_complexity=2,
   smooth_landmarks=True,
   min_detection_confidence=0.6,
   min_tracking_confidence=0.6,
)




# ============================================================
# Lecture vidéo
# ============================================================
cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame0 = cap.read()
if not ret:
   raise RuntimeError("Impossible de lire la vidéo sagittale")


frame0 = rotate_frame(frame0, rotation)
h, w = frame0.shape[:2]


out = cv2.VideoWriter(
   OUTPUT_VIDEO,
   cv2.VideoWriter_fourcc(*"mp4v"),
   fps_forced,
   (w, h),
)


frames = []
knee_angles = []
trunk_angles = []


frame_idx = 0


# ============================================================
# Analyse vidéo
# ============================================================
print("▶️ Début analyse sagittale...")


while True:
   ret, frame = cap.read()
   if not ret:
       break


   frame = rotate_frame(frame, rotation)


   if frame_idx < frame_start:
       frame_idx += 1
       continue
   if frame_idx > frame_end:
       break


   rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
   res = pose.process(rgb)


   if res.pose_landmarks:
       lm = res.pose_landmarks.landmark


       # masque jambe gauche
       for i in [23, 25, 27]:
           lm[i].visibility = 0


       hip = np.array([lm[24].x * w, lm[24].y * h])
       knee = np.array([lm[26].x * w, lm[26].y * h])
       ankle = np.array([lm[28].x * w, lm[28].y * h])
       shoulder = np.array([lm[12].x * w, lm[12].y * h])


       # Angle genou
       knee_angle = angle_between(hip - knee, ankle - knee)


       # Flexion tronc
       vertical = np.array([0, -1])
       trunk_angle = angle_between(hip - shoulder, vertical)


       knee_angles.append(knee_angle)
       trunk_angles.append(trunk_angle)
       frames.append(frame_idx)


       # === DESSIN DU SQUELETTE MEDIAPIPE ===
       mp_drawing.draw_landmarks(
           frame,
           res.pose_landmarks,
           mp_pose.POSE_CONNECTIONS,
           landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style(),
       )


       # === TEXTE VIDÉO (compteur + angles instantanés) ===
       cv2.putText(
           frame,
           f"FRAME: {frame_idx}",
           (10, 30),
           cv2.FONT_HERSHEY_SIMPLEX,
           0.8,
           (255, 255, 255),
           2,
       )
       cv2.putText(
           frame,
           f"Genou: {knee_angle:.1f}°",
           (10, 70),
           cv2.FONT_HERSHEY_SIMPLEX,
           0.8,
           (255, 220, 0),
           2,
       )
       cv2.putText(
           frame,
           f"Tronc: {trunk_angle:.1f}°",
           (10, 110),
           cv2.FONT_HERSHEY_SIMPLEX,
           0.8,
           (0, 255, 255),
           2,
       )


   out.write(frame)
   frame_idx += 1


cap.release()
out.release()
pose.close()


# ============================================================
# FILTRAGE 10 Hz
# ============================================================
knee_filt = butterworth_filter(knee_angles, fps_forced, cutoff=10)
trunk_filt = butterworth_filter(trunk_angles, fps_forced, cutoff=10)


contact_idx = frames.index(min(frames, key=lambda f: abs(f - frame_contact)))

IC_knee = knee_filt[contact_idx]
IC_trunk = trunk_filt[contact_idx]

frames_100 = int(0.1 * fps_forced)
end_100 = min(contact_idx + frames_100, len(knee_filt) - 1)

peak_knee_100 = np.min(knee_filt[contact_idx:end_100])
peak_trunk_100 = np.min(trunk_filt[contact_idx:end_100])

delta_knee = peak_knee_100 - IC_knee
delta_trunk = peak_trunk_100 - IC_trunk

peak_knee_global = np.min(knee_filt[contact_idx:])
peak_trunk_global = np.min(trunk_filt[contact_idx:])


# ============================================================
# EXPORT CSV (angles + indicateurs)
# ============================================================
df = pd.DataFrame(
   {
       "frame": frames,
       "time_s": np.array(frames) / fps_forced,
       "knee_deg": knee_angles,
       "knee_deg_filt10": knee_filt,
       "trunk_deg": trunk_angles,
       "trunk_deg_filt10": trunk_filt,
       "IC_knee": IC_knee,
       "IC_trunk": IC_trunk,
       "peak_knee_100": peak_knee_100,
       "peak_trunk_100": peak_trunk_100,
       "delta_knee_100": delta_knee,
       "delta_trunk_100": delta_trunk,
       "peak_knee_global": peak_knee_global,
       "peak_trunk_global": peak_trunk_global,
   }
)


df.to_csv(CSV_OUTPUT, index=False)
print(f"💾 CSV sauvegardé : {CSV_OUTPUT}")


# ============================================================
# GRAPHIQUES PNG
# ============================================================
# On recharge pour être sûr et on ajoute des colonnes pratiques
df_plot = pd.read_csv(CSV_OUTPUT)
df_plot["knee"] = df_plot["knee_deg"]
df_plot["knee_f"] = df_plot["knee_deg_filt10"]
df_plot["trunk"] = df_plot["trunk_deg"]
df_plot["trunk_f"] = df_plot["trunk_deg_filt10"]


# frame correspondant à 100 ms après IC (en absolu)
f100 = frame_contact + frames_100
f100 = min(f100, int(df_plot["frame"].max()))


# ----- GRAPHE 1 : Angle du genou complet -----
plt.figure(figsize=(13, 6))
plt.plot(df_plot["frame"], df_plot["knee_f"], label="Genou filtré", color="orange")
plt.axvline(frame_contact, color="green", linestyle="--", label="IC")
plt.axvline(f100, color="red", linestyle="--", label="100ms")
plt.axvline(frame_end, color="purple", linestyle="--", label="Takeoff")
plt.title("Flexion genou — complète")
plt.xlabel("Frame")
plt.ylabel("Angle (°)")
plt.legend()
plt.grid(alpha=0.4)
plt.tight_layout()
plt.savefig(PNG_KNEE, dpi=300)


# ----- GRAPHE 2 : Angle du tronc complet -----
plt.figure(figsize=(13, 6))
plt.plot(df_plot["frame"], df_plot["trunk_f"], label="Tronc filtré", color="blue")
plt.axvline(frame_contact, color="green", linestyle="--", label="IC")
plt.axvline(f100, color="red", linestyle="--", label="100ms")
plt.axvline(frame_end, color="purple", linestyle="--", label="Takeoff")
plt.title("Flexion tronc — complète")
plt.xlabel("Frame")
plt.ylabel("Angle (°)")
plt.legend()
plt.grid(alpha=0.4)
plt.tight_layout()
plt.savefig(PNG_TRUNK, dpi=300)


# ============================ GRAPHE 3 — GENOU 0–100ms ============================
df100 = df_plot[df_plot["frame"].between(frame_contact, f100)]


plt.figure(figsize=(10, 5))
plt.plot(df100["frame"], df100["knee_f"], color="orange", label="Genou filtré")
plt.axvline(frame_contact, color="green", linestyle="--", label="IC")
plt.axvline(f100, color="red", linestyle="--", label="100ms")
plt.title("Genou — IC → 100ms")
plt.xlabel("Frame")
plt.ylabel("Angle (°)")
plt.grid(alpha=0.4)
plt.legend()
plt.tight_layout()
plt.savefig(PNG_KNEE_100, dpi=300)


# ============================ GRAPHE 4 — TRONC 0–100ms ============================
plt.figure(figsize=(10, 5))
plt.plot(df100["frame"], df100["trunk_f"], color="blue", label ="Tronc filtré")
plt.axvline(frame_contact, color="green", linestyle="--", label="IC")
plt.axvline(f100, color="red", linestyle="--", label="100ms")
plt.title("Tronc — IC → 100ms")
plt.xlabel("Frame")
plt.ylabel("Angle (°)")
plt.grid(alpha=0.4)
plt.legend()
plt.tight_layout()
plt.savefig(PNG_TRUNK_100, dpi=300)


print("\n🔥 SAGITTAL TERMINÉ ET 4 GRAPHS GÉNÉRÉS 🔥")



