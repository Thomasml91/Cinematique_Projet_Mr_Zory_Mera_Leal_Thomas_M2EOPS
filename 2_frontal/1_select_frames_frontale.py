import cv2
import os
import json
import numpy as np
import time


# ======================================
# CONFIG
# ======================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
VIDEO_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "CMJ_frontale.mp4")
PARAMS_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "parametres_selection_frontale.json")


FPS_FORCED = 240

MAX_DISPLAY_WIDTH = 1000


# ======================================
# ROTATION
# ======================================
def rotate_frame(frame, angle):
   if angle == 90:
       return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
   elif angle == 180:
       return cv2.rotate(frame, cv2.ROTATE_180)
   elif angle == 270:
       return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
   return frame


# ======================================
# MAIN PROGRAM
# ======================================
def main():


   # ---- Charger vidéo ----
   if not os.path.exists(VIDEO_PATH):
       raise FileNotFoundError("❌ Vidéo introuvable.")


   cap = cv2.VideoCapture(VIDEO_PATH)
   total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

   current_frame = 0
   rotation_angle = 0
   frame_contact = None
   frame_takeoff = None


   # ---- Fenêtre + Slider ----
   cv2.namedWindow("Frontale", cv2.WINDOW_AUTOSIZE)

   def on_trackbar(val):
       nonlocal current_frame
       current_frame = val


   cv2.createTrackbar("Frame", "Frontale", 0, total_frames - 1, on_trackbar)


   saved = False   # Pour afficher le message de sauvegarde


   # ======================================
   # LOOP
   # ======================================
   while True:


       # Si sauvegardé → petit délai puis fermeture automatique
       if saved:
           time.sleep(1)
           break


       cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
       ret, frame = cap.read()
       if not ret:
           break

       frame = rotate_frame(frame, rotation_angle)

       # Adapter à la hauteur de l'écran
       MAX_DISPLAY_HEIGHT = 800
       h, w = frame.shape[:2]
       if h > MAX_DISPLAY_HEIGHT:
           scale = MAX_DISPLAY_HEIGHT / h
           frame = cv2.resize(frame, (int(w * scale), int(h * scale)),
                              interpolation=cv2.INTER_AREA)


       # --------------- CANVAS (propre) ---------------
       canvas_h = frame.shape[0] + 40
       canvas_w = frame.shape[1] + 300
       canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)


       # Centrer la vidéo
       offset_x = 280  # OK tel quel, rien de critique
       offset_y = 20
       canvas[offset_y:offset_y+frame.shape[0], offset_x:offset_x+frame.shape[1]] = frame


       # ---- Sidebar noire ----
       cv2.rectangle(canvas, (0, 0), (260, canvas_h), (0, 0, 0), -1)


       # ---- Encadré commandes clavier ----
       cv2.putText(canvas, "CONTROLES CLAVIER", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)


       lines = [
           " A / <- : -1 frame",
           " D / -> : +1 frame",
           " Q : -10",
           " W : +10",
           " R : rotation 90",
           " C : marquer Contact",
           " T : marquer Decollage",
           " S : sauvegarder",
           " ESC : quitter"
       ]


       for i, txt in enumerate(lines):
           cv2.putText(canvas, txt, (20, 80 + i*30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)


       # ---- Infos dynamiques ----
       cv2.putText(canvas, f"Frame: {current_frame}/{total_frames-1}",
                   (20, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)


       cv2.putText(canvas, f"Rotation: {rotation_angle} deg",
                   (20, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)


       if frame_contact is not None:
           cv2.putText(canvas, f"Contact: {frame_contact}",
                       (20, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)


       if frame_takeoff is not None:
           cv2.putText(canvas, f"Decollage: {frame_takeoff}",
                       (20, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,150,255), 2)


       # Si sauvegardé → encadré vert
       if saved:
           cv2.rectangle(canvas, (10, 540), (250, 590), (0,180,0), -1)
           cv2.putText(canvas, "Sauvegarde OK ✓", (20, 575),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

       cv2.setTrackbarPos("Frame", "Frontale", current_frame)

       cv2.imshow("Frontale", canvas)


       # ---- Touches clavier ----
       key = cv2.waitKey(20) & 0xFF


       if key in [ord('d'), 83]: current_frame = min(total_frames-1, current_frame + 1)
       elif key in [ord('a'), 81]: current_frame = max(0, current_frame - 1)
       elif key == ord('w'): current_frame = min(total_frames-1, current_frame + 10)
       elif key == ord('q'): current_frame = max(0, current_frame - 10)
       elif key == ord('r'): rotation_angle = (rotation_angle + 90) % 360
       elif key == ord('c'): frame_contact = current_frame
       elif key == ord('t'): frame_takeoff = current_frame


       elif key == ord('s'):
           params = {
               "rotation": rotation_angle,
               "frame_contact": frame_contact,
               "frame_takeoff": frame_takeoff,
               "fps": FPS_FORCED
           }
           with open(PARAMS_PATH, "w") as f:
               json.dump(params, f, indent=2)


           print("💾 Paramètres sauvegardés :", PARAMS_PATH)
           saved = True   # Active l'encadré vert → puis fermeture


       elif key == 27:  # ESC
           break


   cap.release()
   cv2.destroyAllWindows()




if __name__ == "__main__":
   main()
