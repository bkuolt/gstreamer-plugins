import os
import sys

# 1. Pfade und Environment-Variablen setzen (MUSS vor Gst.init passieren!)
base_dir = "/home/bastian/Desktop/bgl-gstreamer-plugins"
os.environ["GST_PLUGIN_PATH"] = base_dir

# Den alten PYTHONPATH anhängen, falls vorhanden
current_pythonpath = os.environ.get("PYTHONPATH", "")
os.environ["PYTHONPATH"] = f"{base_dir}/python:{current_pythonpath}"

# Debugging anwerfen
os.environ["GST_DEBUG"] = "python:4,GST_PLUGIN_LOADING:2"

# 2. Cache löschen
cache_file = os.path.expanduser("~/.cache/gstreamer-1.0/registry.x86_64.bin")
if os.path.exists(cache_file):
    os.remove(cache_file)
    print("GStreamer-Cache gelöscht.")

# 3. GStreamer Imports NACH dem Setzen der Env-Variablen
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gst, GLib

# Initialisieren
Gst.init(sys.argv)

# 4. Pipeline definieren
pipeline_str = (
    "v4l2src device=/dev/video0 ! "
    "videoconvert ! "
    "video/x-raw,format=RGB,width=1280,height=720 ! "
    "qrcodescanner ! "
    "videoconvert ! "
    "autovideosink"
)

print("--- Starte Pipeline ---")
pipeline = Gst.parse_launch(pipeline_str)

# 5. Bus-Setup für sauberes Error-Handling
bus = pipeline.get_bus()
bus.add_signal_watch()

def on_message(bus, message, loop):
    msg_type = message.type
    if msg_type == Gst.MessageType.EOS:
        print("End-Of-Stream erreicht.")
        loop.quit()
    elif msg_type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"Error: {err.message}")
        print(f"Debug info: {debug}")
        loop.quit()
    return True

loop = GLib.MainLoop()
bus.connect("message", on_message, loop)

# 6. Pipeline abspielen
pipeline.set_state(Gst.State.PLAYING)

try:
    loop.run()
except KeyboardInterrupt:
    print("\nPipeline durch User abgebrochen (Strg+C).")
finally:
    # Sauberes Aufräumen am Ende
    pipeline.set_state(Gst.State.NULL)
    print("Pipeline erfolgreich beendet.")