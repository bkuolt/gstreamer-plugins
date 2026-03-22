import cv2
import numpy as np

def draw_text_centered(map_info, width, height, text, color=(255, 0, 0)):
    # Den GStreamer-Buffer in ein NumPy-Array "casten" (Zero-Copy!)
    # Wir sagen NumPy, dass die Daten als (H, W, 3) interpretiert werden sollen
    frame = np.ndarray((height, width, 3), buffer=map_info.data, dtype=np.uint8)

    # Schrift-Einstellungen
    font = cv2.FONT_HERSHEY_COMPLEX
    font_scale = 1.2
    thickness = 3
    
    # Text-Größe berechnen für die Platzierung links unten
    text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
    text_x = 10  # Links mit kleinem Abstand
    text_y = height - 10  # Unten mit kleinem Abstand


    # Den Text direkt in das Frame zeichnen
    cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness, lineType=cv2.LINE_AA)