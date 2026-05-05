import cv2
import os
import json
import numpy as np
import time
import tkinter as tk


# ================================================
# CONFIG
# ================================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
VIDEO_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "CMJ_sagittale.mp4")
PARAMS_PATH = os.path.join(BASE_DIR, "1_Fichiers_Vidéos", "parametres_selection_sagittale.json")

FPS_FORCED = 240
SIDEBAR_W = 280


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
# MAIN
# ================================================
def main():

    # ---- Détecter la résolution de l'écran ----
    root = tk.Tk()
    SCREEN_W = root.winfo_screenwidth()
    SCREEN_H = root.winfo_screenheight()
    root.destroy()

    TASKBAR_H  = 60   # Barre des tâches Windows
    TRACKBAR_H = 70   # Slider OpenCV en haut de la fenêtre

    # Zone dispo pour la vidéo
    MAX_DISPLAY_HEIGHT = SCREEN_H - TASKBAR_H - TRACKBAR_H - 20
    MAX_DISPLAY_WIDTH  = SCREEN_W - SIDEBAR_W - 20

    # ---- Charger vidéo ----
    if not os.path.exists(VIDEO_PATH):
        raise FileNotFoundError(f"❌ Vidéo sagittale introuvable : {VIDEO_PATH}")

    cap = cv2.VideoCapture(VIDEO_PATH)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    current_frame = 0
    rotation_angle = 0
    frame_contact = None
    frame_takeoff = None
    saved = False

    # ---- Fenêtre plein écran ----
    cv2.namedWindow("Sagittale", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Sagittale", SCREEN_W, SCREEN_H - TASKBAR_H)
    cv2.moveWindow("Sagittale", 0, 0)

    cv2.createTrackbar("Frame", "Sagittale", 0, total_frames - 1,
                       lambda val: None)

    # ================================================
    # LOOP
    # ================================================
    while True:

        if saved:
            time.sleep(1)
            break

        # Sync trackbar -> current_frame
        current_frame = cv2.getTrackbarPos("Frame", "Sagittale")

        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()
        if not ret:
            break

        frame = rotate_frame(frame, rotation_angle)

        # ---- Redimensionnement adaptatif ----
        h, w = frame.shape[:2]
        scale = min(MAX_DISPLAY_HEIGHT / h, MAX_DISPLAY_WIDTH / w, 1.0)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)),
                           interpolation=cv2.INTER_AREA)

        fh, fw = frame.shape[:2]

        # ---- Canvas plein écran ----
        canvas_h = SCREEN_H - TASKBAR_H - TRACKBAR_H
        canvas_w = SCREEN_W
        canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

        # Vidéo à droite de la sidebar, centrée verticalement
        offset_x = SIDEBAR_W
        offset_y = (canvas_h - fh) // 2
        canvas[offset_y:offset_y+fh, offset_x:offset_x+fw] = frame

        # ---- Sidebar noire ----
        cv2.rectangle(canvas, (0, 0), (SIDEBAR_W - 10, canvas_h), (0, 0, 0), -1)

        # ---- Titre ----
        cv2.putText(canvas, "CONTROLES CLAVIER", (15, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)

        # ---- Commandes ----
        lines = [
            " A / <- : -1 frame",
            " D / -> : +1 frame",
            " Q : -10 frames",
            " W : +10 frames",
            " R : rotation 90",
            " C : marquer Contact",
            " T : marquer Decollage",
            " S : sauvegarder",
            " ESC : quitter"
        ]
        for i, txt in enumerate(lines):
            cv2.putText(canvas, txt, (15, 75 + i * 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # ---- Infos dynamiques ----
        y_info = 380
        cv2.putText(canvas, f"Frame: {current_frame}/{total_frames-1}",
                    (15, y_info), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
        cv2.putText(canvas, f"Rotation: {rotation_angle} deg",
                    (15, y_info + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

        if frame_contact is not None:
            cv2.putText(canvas, f"Contact: {frame_contact}",
                        (15, y_info + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

        if frame_takeoff is not None:
            cv2.putText(canvas, f"Decollage: {frame_takeoff}",
                        (15, y_info + 105), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 150, 255), 2)

        # ---- Message sauvegarde ----
        if saved:
            cv2.rectangle(canvas, (10, y_info + 140), (260, y_info + 185), (0, 180, 0), -1)
            cv2.putText(canvas, "Sauvegarde OK", (20, y_info + 170),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Sagittale", canvas)

        # ================================================
        # KEYBOARD
        # ================================================
        key = cv2.waitKey(20) & 0xFF

        if key in [ord('d'), 83]:
            current_frame = min(total_frames - 1, current_frame + 1)
            cv2.setTrackbarPos("Frame", "Sagittale", current_frame)
        elif key in [ord('a'), 81]:
            current_frame = max(0, current_frame - 1)
            cv2.setTrackbarPos("Frame", "Sagittale", current_frame)
        elif key == ord('w'):
            current_frame = min(total_frames - 1, current_frame + 10)
            cv2.setTrackbarPos("Frame", "Sagittale", current_frame)
        elif key == ord('q'):
            current_frame = max(0, current_frame - 10)
            cv2.setTrackbarPos("Frame", "Sagittale", current_frame)
        elif key == ord('r'):
            rotation_angle = (rotation_angle + 90) % 360
        elif key == ord('c'):
            frame_contact = current_frame
        elif key == ord('t'):
            frame_takeoff = current_frame

        elif key == ord('s'):
            params = {
                "rotation": rotation_angle,
                "frame_contact": frame_contact,
                "frame_takeoff": frame_takeoff,
                "fps": FPS_FORCED
            }
            with open(PARAMS_PATH, "w") as f:
                json.dump(params, f, indent=2)
            print("Parametres sauvegardes :", PARAMS_PATH)
            saved = True

        elif key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()