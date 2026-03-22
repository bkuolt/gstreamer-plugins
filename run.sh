#!/bin/bash

# Pfade sauber definieren
BASE_DIR="/home/bastian/Desktop/bgl-gstreamer-plugins"

# WICHTIG: GST_PLUGIN_PATH zeigt auf den Ordner ÜBER dem 'python' Verzeichnis
export GST_PLUGIN_PATH="$BASE_DIR"

# PYTHONPATH muss den Ordner 'python' enthalten, damit die Imports klappen
export PYTHONPATH="$BASE_DIR/python:$PYTHONPATH"

# Debugging: Nur Fehler und Python-Logs (sonst wird es zu voll)
export GST_DEBUG=python:4,GST_PLUGIN_LOADING:2

# Cache nur löschen, wenn wir das Plugin geändert haben
rm -f ~/.cache/gstreamer-1.0/registry.x86_64.bin

echo "--- Suche nach qrcodescanner ---"
gst-inspect-1.0 qrcodescanner

echo "--- Starte Pipeline ---"
# Ich habe 'videoscale' und 'capsfilter' ergänzt, 
# damit zbar nicht bei riesigen 4K-Webcam-Auflösungen in die Knie geht.
gst-launch-1.0 v4l2src device=/dev/video0 ! \
    videoconvert ! \
    video/x-raw,format=RGB,width=640,height=480 ! \
    qrcodescanner ! \
    videoconvert ! \
    autovideosink