#!/bin/bash

# Pfade absolut setzen
BASE_DIR="/home/bastian/Desktop/bgl-gstreamer-plugins"
# Hier muss der Ordner rein, wo dein qrcodescanner.py (oder .so) liegt!
PLUGIN_DIR="$BASE_DIR" 

# 1. GST_PLUGIN_PATH komplett isolieren! 
# Wir nehmen NUR die System-Plugins und DEIN Verzeichnis.
# KEIN Punkt (.) und KEIN BASE_DIR, wenn das venv darin liegt!
export GST_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/gstreamer-1.0:$PLUGIN_DIR"

# 2. Den Scanner anweisen, NICHTS anderes zu laden
export GST_REGISTRY_FORK=no

# 3. Python Pfade (für das gi Modul und dein Plugin)
export PYTHONPATH="$PLUGIN_DIR:$PYTHONPATH"

# 4. Radikaler Cache-Cleanup
rm -rf ~/.cache/gstreamer-1.0/
# Wir löschen auch alle potentiellen lokalen Registries
rm -f "$BASE_DIR/*.bin"

echo "--- Checke GStreamer Python Loader ---"
gst-inspect-1.0 python

echo "--- Suche gezielt nach qrcodescanner ---"
# Wir erzwingen das Laden genau dieser Datei
gst-inspect-1.0 "$PLUGIN_DIR/qrcodescanner.py" 2>/dev/null || gst-inspect-1.0 qrcodescanner

echo "--- Starte Pipeline ---"
gst-launch-1.0 v4l2src device=/dev/video0 ! \
    videoconvert ! \
    qrcodescanner ! \
    videoconvert ! \
    autovideosink