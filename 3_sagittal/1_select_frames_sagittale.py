import cv2
import os
import json
import numpy as np
import time




# ================================================
# CONFIG
# ================================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
VIDEO_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "CMJ_sagittale.mp4")
PARAMS_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "parametres_selection_sagittale.json")


FPS_FORCED = 240




# ================================================
# ROTATION
# ================================================
def rotate_frame(frame, angle):
   if angle == 90:
       return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
   elif angle == 180:
       return cv2.rotate(frame, cv2.ROTATE_180)
   elif angle == 270:
       return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
   return frame




# ================================================
# REDIMENSION SANS DÉFORMATION
# ================================================
def resize_contain(frame, max_w, max_h):
   h, w = frame.shape[:2]
   ratio = min(max_w / w, max_h / h)
   new_w = int(w * ratio)
   new_h = int(h * ratio)
   return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA), new_w, new_h




# ================================================
# MAIN
# ================================================
def main():


   if not os.path.exists(VIDEO_PATH):
       raise FileNotFoundError(f"❌ Vidéo sagittale introuvable : {VIDEO_PATH}")


   cap = cv2.VideoCapture(VIDEO_PATH)
   total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

   current_frame = 0
   rotation_angle = 0
   frame_contact = None
   frame_takeoff = None
   saved = False


   cv2.namedWindow("Sagittale", cv2.WINDOW_AUTOSIZE)


   # ---- Slider ----
   def on_trackbar(val):
       nonlocal current_frame
       current_frame = val


   cv2.createTrackbar("Frame", "Sagittale", 0, total_frames - 1, on_trackbar)


   # ================================================
   # LOOP
   # ================================================
   while True:


       if saved:
           time.sleep(1)
           break


       current_frame = max(0, min(total_frames - 1, current_frame))
       cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
       ret, frame = cap.read()
       if not ret:
           break


       frame = rotate_frame(frame, rotation_angle)

       MAX_DISPLAY_HEIGHT = 800
       h, w = frame.shape[:2]
       if h > MAX_DISPLAY_HEIGHT:
           scale = MAX_DISPLAY_HEIGHT / h
           frame = cv2.resize(frame, (int(w * scale), int(h * scale)),
                              interpolation=cv2.INTER_AREA)

       # ---- Dimensions vidéo originales ----
       h, w = frame.shape[:2]


       # ---- Canvas ----
       sidebar_w = 300
       margin = 20
       canvas_h = 700
       canvas_w = sidebar_w + 900


       canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)


       # ---- Resize vidéo sans déformation ----
       max_video_w = canvas_w - sidebar_w - 2 * margin
       max_video_h = canvas_h - 2 * margin


       frame_resized, new_w, new_h = resize_contain(frame, max_video_w, max_video_h)


       # ---- Centrage vertical + horizontal ----
       video_x = sidebar_w + (max_video_w - new_w) // 2 + margin
       video_y = (canvas_h - new_h) // 2


       canvas[video_y:video_y + new_h, video_x:video_x + new_w] = frame_resized


       # ================================================
       # SIDEBAR
       # ================================================
       cv2.rectangle(canvas, (0, 0), (sidebar_w, canvas_h), (0, 0, 0), -1)


       cv2.putText(canvas, "CONTROLES CLAVIER", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)


       lines = [
           "A / <- : -1 frame",
           "D / -> : +1 frame",
           "Q : -10 frames",
           "W : +10 frames",
           "R : rotation 90°",
           "C : Contact",
           "T : Decollage",
           "S : Sauvegarder",
           "ESC : Quitter"
       ]


       for i, txt in enumerate(lines):
           cv2.putText(canvas, txt, (20, 80 + i * 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)


       cv2.putText(canvas, f"Frame: {current_frame}/{total_frames-1}",
                   (20, canvas_h - 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)


       cv2.putText(canvas, f"Rotation: {rotation_angle} deg",
                   (20, canvas_h - 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)


       if frame_contact is not None:
           cv2.putText(canvas, f"Contact: {frame_contact}",
                       (20, canvas_h // 2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)


       if frame_takeoff is not None:
           cv2.putText(canvas, f"Decollage: {frame_takeoff}",
                       (20, canvas_h // 2 + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 150, 255), 2)


       if saved:
           cv2.rectangle(canvas, (20, 540), (260, 590), (0, 180, 0), -1)
           cv2.putText(canvas, "Sauvegarde OK ✓", (30, 575),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

       cv2.setTrackbarPos("Frame", "Sagittale", current_frame)

       cv2.imshow("Sagittale", canvas)


       # ================================================
       # KEYBOARD
       # ================================================
       key = cv2.waitKey(20) & 0xFF


       if key in [ord('d'), 83]: current_frame += 1
       elif key in [ord('a'), 81]: current_frame -= 1
       elif key == ord('w'): current_frame += 10
       elif key == ord('q'): current_frame -= 10
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


           saved = True


       elif key == 27:
           break


   cap.release()
   cv2.destroyAllWindows()




if __name__ == "__main__":
   main()
