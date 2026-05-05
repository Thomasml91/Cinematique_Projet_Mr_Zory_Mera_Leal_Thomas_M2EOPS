import cv2
import os
import json
import mediapipe as mp
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt


# ==== AJOUT : utilitaires de dessin MediaPipe ====
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles
# ================================================


# ============================
# CONFIG
# ============================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
VIDEO_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "CMJ_frontale.mp4")
PARAMS_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "parametres_selection_frontale.json")
OUTPUT_VIDEO_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "valgus_pose_angles_annotated.mp4")
ANGLES_CSV_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "angles_valgus.csv")


PNG_ABS_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "valgus_angles_absolus_10Hz.png")
PNG_SIGNED_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "valgus_varus_10Hz.png")




# ============================
# FONCTIONS
# ============================
def rotate_frame(frame, angle):
   if angle == 90:
       return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
   elif angle == 180:
       return cv2.rotate(frame, cv2.ROTATE_180)
   elif angle == 270:
       return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
   return frame


def absolute_knee_angle(hip, knee, ankle, width, height):
    def to_px(p):
        return np.array([p[0] * width, p[1] * height])

    h = to_px(hip)
    k = to_px(knee)
    a = to_px(ankle)

    u = h - k
    v = a - k

    cosang = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))
    cosang = np.clip(cosang, -1.0, 1.0)
    return np.degrees(np.arccos(cosang))


def signed_frontal_angle(hip, knee, ankle, side, width, height):
    def to_px(p):
        return np.array([p[0] * width, p[1] * height])

    u = to_px(hip) - to_px(knee)
    v = to_px(ankle) - to_px(knee)

    cosang = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))
    cosang = np.clip(cosang, -1.0, 1.0)
    angle = np.degrees(np.arccos(cosang))

    deviation = 180 - angle
    sign = np.sign(u[0] * v[1] - u[1] * v[0])
    return deviation * (sign if side == "right" else -sign)




# ======== BUTTERWORTH 10 Hz ========
def butterworth_filter(data, fps, cutoff=10.0, order=4):
    data = np.asarray(data, dtype=float)
    if len(data) < 16:
        print(f"⚠️ Signal trop court ({len(data)} frames) — filtre ignoré")
        return data
    nyquist = 0.5 * fps
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype="low")
    return filtfilt(b, a, data, padlen=min(len(data)-1, 15))


# ============================
# MAIN
# ============================
def main():
   if not os.path.exists(VIDEO_PATH):
       raise FileNotFoundError(f"❌ Vidéo introuvable : {VIDEO_PATH}")


   if not os.path.exists(PARAMS_PATH):
       raise FileNotFoundError(f"❌ Paramètres non trouvés : {PARAMS_PATH}")


   with open(PARAMS_PATH, "r") as f:
       params = json.load(f)

   frame_contact = params["frame_contact"]
   frame_end = params["frame_takeoff"]
   frame_start = max(0, frame_contact - 15)  # démarre 15 frames avant l'IC
   fps_forced = params["fps"]
   rotation = params["rotation"]


   print(f"📄 Paramètres chargés — rotation={rotation}° fps={fps_forced}")


   mp_pose = mp.solutions.pose
   pose = mp_pose.Pose(model_complexity=2,
                       min_detection_confidence=0.3,
                       min_tracking_confidence=0.3)


   cap = cv2.VideoCapture(VIDEO_PATH)


   ret, test_frame = cap.read()
   if not ret:
       raise RuntimeError("Impossible de lire la vidéo")


   test_frame = rotate_frame(test_frame, rotation)
   height, width = test_frame.shape[:2]
   cap.set(cv2.CAP_PROP_POS_FRAMES, 0)


   out = cv2.VideoWriter(
       OUTPUT_VIDEO_PATH,
       cv2.VideoWriter_fourcc(*"mp4v"),
       fps_forced,
       (width, height)
   )


   # === stockage des angles ===
   angles_r = []
   angles_l = []
   angles_r_abs = []
   angles_l_abs = []
   valid_frames = []


   frame_idx = 0


   while True:
       ret, frame = cap.read()
       if not ret:
           break


       if frame_idx < frame_start:
           frame_idx += 1
           continue
       if frame_idx > frame_end:
           break


       frame = rotate_frame(frame, rotation)
       results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


       if results.pose_landmarks:
           lm = results.pose_landmarks.landmark


           r_hip = [lm[24].x, lm[24].y]
           r_knee = [lm[26].x, lm[26].y]
           r_ank = [lm[28].x, lm[28].y]


           l_hip = [lm[23].x, lm[23].y]
           l_knee = [lm[25].x, lm[25].y]
           l_ank = [lm[27].x, lm[27].y]

           angle_r = signed_frontal_angle(r_hip, r_knee, r_ank, "right", width, height)
           angle_l = signed_frontal_angle(l_hip, l_knee, l_ank, "left", width, height)


           angle_r_abs = absolute_knee_angle(r_hip, r_knee, r_ank, width, height)
           angle_l_abs = absolute_knee_angle(l_hip, l_knee, l_ank, width, height)


           angles_r.append(angle_r)
           angles_l.append(angle_l)
           angles_r_abs.append(angle_r_abs)
           angles_l_abs.append(angle_l_abs)
           valid_frames.append(frame_idx)


           # ==== AJOUT : squelette + compteur + angles sur la vidéo ====
           mp_drawing.draw_landmarks(
               frame,
               results.pose_landmarks,
               mp_pose.POSE_CONNECTIONS,
               landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style()
           )


           cv2.putText(
               frame,
               f"FRAME: {frame_idx}",
               (30, 50),
               cv2.FONT_HERSHEY_SIMPLEX,
               1.0,
               (255, 255, 255),
               2
           )
           cv2.putText(
               frame,
               f"Valgus R: {angle_r:.1f} deg",
               (30, 90),
               cv2.FONT_HERSHEY_SIMPLEX,
               0.8,
               (0, 215, 255),
               2
           )
           cv2.putText(
               frame,
               f"Valgus L: {angle_l:.1f} deg",
               (30, 125),
               cv2.FONT_HERSHEY_SIMPLEX,
               0.8,
               (0, 255, 120),
               2
           )
           # ===========================================================


       # on écrit *toujours* le frame (annoté ou non)
       out.write(frame)
       frame_idx += 1


   cap.release()
   out.release()
   pose.close()


   # =============== FILTRAGE 10 Hz ==================
   filt_r = butterworth_filter(angles_r, fps_forced, cutoff=10)
   filt_l = butterworth_filter(angles_l, fps_forced, cutoff=10)
   filt_r_abs = butterworth_filter(angles_r_abs, fps_forced, cutoff=10)
   filt_l_abs = butterworth_filter(angles_l_abs, fps_forced, cutoff=10)


   # === Fonction d'extraction des valeurs 0–100ms ===
   def slice_0_100(signal, frames_list, frame_start, frame_window):
       # Prendre la frame valide la plus proche de frame_start
       closest_start = min(frames_list, key=lambda f: abs(f - frame_start))
       start_index = frames_list.index(closest_start)
       end_index = min(start_index + frame_window, len(signal))
       return signal[start_index:end_index]


   # === NOUVEAUX CALCULS — IC, Peak 0-100 ms, Delta ===

   # Trouver la frame valide la plus proche de frame_start
   closest = min(valid_frames, key=lambda f: abs(f - frame_contact))
   IC_valgus_R = angles_r[valid_frames.index(closest)]
   IC_valgus_L = angles_l[valid_frames.index(closest)]

   # Index de frame_contact dans valid_frames
   contact_idx = valid_frames.index(min(valid_frames, key=lambda f: abs(f - frame_contact)))

   # conversion frames → 100 ms fenêtre
   frames_100 = int(0.1 * fps_forced)
   end_100 = min(contact_idx + frames_100, len(filt_r) - 1)

   # Peak 0-100ms — uniquement après le contact
   peak_100_R = np.min(filt_r[contact_idx:end_100])
   peak_100_L = np.min(filt_l[contact_idx:end_100])

   # Delta 0-100ms
   delta_R = peak_100_R - IC_valgus_R
   delta_L = peak_100_L - IC_valgus_L


   # === 100ms window slices ===
   R_0_100 = slice_0_100(angles_r, valid_frames, frame_contact, frames_100)
   L_0_100 = slice_0_100(angles_l, valid_frames, frame_contact, frames_100)


   # === Peak values 0–100ms ===
   peak_R_0_100 = np.min(R_0_100)  # valgus négatif = min
   peak_L_0_100 = np.min(L_0_100)


   # === Delta values ===
   delta_R_0_100 = peak_R_0_100 - IC_valgus_R
   delta_L_0_100 = peak_L_0_100 - IC_valgus_L

   # ==== PEAKS GLOBAUX — uniquement après le contact ====
   peak_global_R = np.min(filt_r[contact_idx:])
   peak_global_L = np.min(filt_l[contact_idx:])


   # =============== CSV COMPLET (brut + filtré) ==================
   df = pd.DataFrame({
       "frame": valid_frames,
       "time_s": [f / fps_forced for f in valid_frames],
       "angle_droite_signed": angles_r,
       "angle_gauche_signed": angles_l,
       "angle_droite_signed_filt10": filt_r,
       "angle_gauche_signed_filt10": filt_l,
       "angle_droite_abs": angles_r_abs,
       "angle_gauche_abs": angles_l_abs,
       "angle_droite_abs_filt10": filt_r_abs,
       "angle_gauche_abs_filt10": filt_l_abs,
       "valgus_IC_R": IC_valgus_R,
       "valgus_IC_L": IC_valgus_L,
       "peak_100ms_R": peak_100_R,
       "peak_100ms_L": peak_100_L,
       "delta_100ms_R": delta_R,
       "delta_100ms_L": delta_L,
       "peak_global_R": peak_global_R,
       "peak_global_L": peak_global_L,


   })


   df.to_csv(ANGLES_CSV_PATH, index=False)
   print(f"💾 CSV sauvegardé → {ANGLES_CSV_PATH}")


   # ============================
   # GRAPHIQUE 1 — ANGLES ABSOLUS
   # ============================
   plt.figure(figsize=(12, 6))
   plt.plot(valid_frames, angles_r_abs, "--", alpha=0.3, label="Droite brut")
   plt.plot(valid_frames, angles_l_abs, "--", alpha=0.3, label="Gauche brut")
   plt.plot(valid_frames, filt_r_abs, linewidth=2, label="Droite filtré 10 Hz")
   plt.plot(valid_frames, filt_l_abs, linewidth=2, label="Gauche filtré 10 Hz")


   plt.axvline(frame_contact, color="green", linestyle="--", label="Contact")
   plt.axvline(frame_end, color="orange", linestyle="--", label="Décollage")


   plt.xlabel("Frame")
   plt.ylabel("Angle interne (°)")
   plt.grid(alpha=0.4)
   plt.legend()
   plt.tight_layout()
   plt.axvline(frame_contact + frames_100, color="red", linestyle="--", label="100 ms post-contact")
   plt.savefig(PNG_ABS_PATH, dpi=300)



   # ============================
   # GRAPHIQUE 2 — VALGUS/VARUS
   # ============================
   plt.figure(figsize=(12, 6))
   plt.plot(valid_frames, angles_r, "--", alpha=0.3, label="Droite brut")
   plt.plot(valid_frames, angles_l, "--", alpha=0.3, label="Gauche brut")
   plt.plot(valid_frames, filt_r, linewidth=2, label="Droite filtré 10 Hz")
   plt.plot(valid_frames, filt_l, linewidth=2, label="Gauche filtré 10 Hz")




   plt.fill_between(valid_frames, -60, 0, color='red', alpha=0.1, label="Valgus (−)")
   plt.fill_between(valid_frames, 0, 60, color='blue', alpha=0.1, label="Varus (+)")


   plt.axvline(frame_contact, color="green", linestyle="--", label="Contact")
   plt.axvline(frame_end, color="orange", linestyle="--", label="Décollage")


   plt.axhline(0, color="black", linewidth=1)
   plt.axvline(frame_contact, color="green", linestyle="--")
   plt.axvline(frame_end, color="orange", linestyle="--")


   plt.ylim(-60, 60)
   plt.yticks(range(-60, 61, 10))
   plt.xlabel("Frame")
   plt.ylabel("Valgus (−) / Varus (+) (°)")
   plt.grid(alpha=0.3)
   plt.legend()
   plt.tight_layout()
   plt.axvline(frame_contact + frames_100, color="red", linestyle="--", label="100 ms post-contact")
   plt.savefig(PNG_SIGNED_PATH, dpi=300)



   # dernier frame de la fenêtre 0–100 ms effectivement utilisé
   frame_100 = valid_frames[end_100]


   # ============================
   # GRAPHIQUE 3 — ABSOLU 0-100 ms
   # ============================
   plt.figure(figsize=(12, 6))
   plt.plot(valid_frames[contact_idx:end_100 + 1], filt_r_abs[contact_idx:end_100 + 1], label="Droite filtré")
   plt.plot(valid_frames[contact_idx:end_100 + 1], filt_l_abs[contact_idx:end_100 + 1], label="Gauche filtré")
   plt.xlabel("Frame")
   plt.ylabel("Angle absolu (°)")
   plt.axvline(frame_contact, color="green", linestyle="--", label="Contact")
   plt.axvline(frame_100, color="red", linestyle=":", label="100 ms")
   plt.title("Angles absolus — fenêtre 0-100 ms")
   plt.legend()
   plt.grid(alpha=0.4)
   plt.savefig(os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "valgus_abs_0_100ms.png"), dpi=300)



   # ============================
   # GRAPHIQUE 4 — Valgus/Varus 0-100 ms
   # ============================
   plt.figure(figsize=(12, 6))
   plt.plot(valid_frames[contact_idx:end_100 + 1], filt_r[contact_idx:end_100 + 1], label="Droite filtré")
   plt.plot(valid_frames[contact_idx:end_100 + 1], filt_l[contact_idx:end_100 + 1], label="Gauche filtré")
   plt.xlabel("Frame")
   plt.ylabel("Valgus (−) / Varus (+) (°)")
   plt.axhline(0, color="black")
   plt.axvline(frame_contact, color="green", linestyle="--", label="Contact")
   plt.axvline(frame_100, color="red", linestyle=":", label="100 ms")
   plt.title("Valgus / Varus — fenêtre 0-100 ms")
   plt.legend()
   plt.grid(alpha=0.4)
   plt.savefig(os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "valgus_0_100ms.png"), dpi=300)



   print("🎉 Analyse frontale terminée !")




if __name__ == "__main__":
   main()
