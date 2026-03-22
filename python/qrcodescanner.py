import os
import sys

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GstBase, GstVideo, GObject
import cv2
import numpy as np

import webbrowser
import time
                
import overlay
import os


class QRCodeScanner(GstBase.BaseTransform):
    __gstmetadata__ = ('QR Code Scanner', 'Filter/Analyzer/Video',
                       'Scans video frames for QR codes', 'Bastian')

    __gsttemplates__ = (
        Gst.PadTemplate.new("src",
                            Gst.PadDirection.SRC,
                            Gst.PadPresence.ALWAYS,
                            Gst.Caps.from_string("video/x-raw,format=RGB")),
        Gst.PadTemplate.new("sink",
                            Gst.PadDirection.SINK,
                            Gst.PadPresence.ALWAYS,
                            Gst.Caps.from_string("video/x-raw,format=RGB"))
    )

    def __init__(self):
        super(QRCodeScanner, self).__init__()
        self.detector = cv2.QRCodeDetector()

    def do_transform_ip(self, buf):
        caps = self.sinkpad.get_current_caps()
        if not caps:
            return Gst.FlowReturn.OK
            
        struct = caps.get_structure(0)
        width = struct.get_value('width')
        height = struct.get_value('height')

        # WICHTIG: Hier jetzt READ und WRITE, damit wir ins Bild zeichnen dürfen!
        result, map_info = buf.map(Gst.MapFlags.READ | Gst.MapFlags.WRITE)
        if not result:
            return Gst.FlowReturn.OK
        
        
        previously_detected_url = getattr(self, 'previously_detected_qr', None)

        try:
            image_array = np.ndarray(shape=(height, width, 3), dtype=np.uint8, buffer=map_info.data)
            gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            data, bbox, _ = self.detector.detectAndDecode(gray_image)
               
            # bbox ist ein Numpy-Array, wenn was gefunden wurde, sonst None
            if bbox is not None and len(bbox) > 0 and data:
                # Koordinaten in Integer umwandeln und umformen für cv2.polylines
                pts = np.int32(bbox).reshape(-1, 1, 2)
                # Zeichne ein grünes Rechteck ins Originalbild (RGB: 0, 255, 0)
                cv2.polylines(image_array, [pts], isClosed=True, color=(0, 255, 0), thickness=3)

                # QR-Code-Bereich extrahieren und als PNG speichern
                x, y, w, h = cv2.boundingRect(np.array(bbox, dtype=np.float32))
                cropped = image_array[y:y+h, x:x+w]
                filename = f"qr_code_{int(time.time())}.png"
                cv2.imwrite(filename, cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))
                # Das hier flusht alle Filesystem-Buffer auf die Disk
                os.sync() 
                print(f"Saved and flushed: {filename}")
                            
                print(f"QR code saved as {filename}")
           
                
               
                overlay.draw_text_centered(map_info, width, height, f"QR CCode detected: {data}", color=(0, 255, 0))
                
                #und öffnen Sie die URL automatisch im 
                if (previously_detected_url != data):
                    setattr(self, 'previously_detected_qr', data)
                    webbrowser.open(data)
                    previously_detected_url = data
         
            # rot,wenn kein qr code erklanntt wird
            elif bbox is None and previously_detected_url is None:
                overlay.draw_text_centered(map_info, width, height, "No QR code detected", color=(255, 0, 0))
            
       
            if data:
                print(f"QR Code detected: {data}")
            
        finally:
            buf.unmap(map_info)

        return Gst.FlowReturn.OK

GObject.type_register(QRCodeScanner)
__gstelementfactory__ = ("qrcodescanner", Gst.Rank.NONE, QRCodeScanner)