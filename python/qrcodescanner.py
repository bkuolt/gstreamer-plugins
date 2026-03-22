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

import requests
import urllib3

# Warnungen unterdrücken (wegen verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_product_name(ean_code):
    # Probiere ggf. auch die Haupt-API (off.org), falls world. zu zickig ist
    url = f"https://world.openfoodfacts.org/api/v0/product/{ean_code}.json"
    
    try:
        # verify=False umgeht den Zertifikats-Fehler
        response = requests.get(url, timeout=3, verify=False)
        if response.status_code == 200:
            data = response.json()
            print(data)
            if data.get("status") == 1:
                product = data.get("product", {})
                # Wir nehmen den Namen oder die Marke als Fallback
                return product.get("product_name") or product.get("brands") or "Unbekannt"
    except Exception as e:
        print(f"Lookup-Fehler: {e}")

    return None

class QRCodeScanner(GstBase.BaseTransform):
    __gstmetadata__ = ('QR and Barcode Scanner', 'Filter/Analyzer/Video',
                       'Scans video frames for QR and EAN codes', 'Bastian')

    __gsttemplates__ = (
        Gst.PadTemplate.new("src", Gst.PadDirection.SRC, Gst.PadPresence.ALWAYS, 
                            Gst.Caps.from_string("video/x-raw,format=RGB")),
        Gst.PadTemplate.new("sink", Gst.PadDirection.SINK, Gst.PadPresence.ALWAYS, 
                            Gst.Caps.from_string("video/x-raw,format=RGB"))
    )

    def __init__(self):
        super(QRCodeScanner, self).__init__()
        self.qr_detector = cv2.QRCodeDetector()
        try:
            # Versuche den Barcode-Detektor zu laden
            self.barcode_detector = cv2.barcode.BarcodeDetector()
            print("Barcode-Detektor geladen.")
        except Exception:
            self.barcode_detector = None
    
    # TODO: move to separate file
    def is_valid_ean13(self, code):
        """Überprüft, ob ein String eine valide EAN-13 mit korrekter Prüfziffer ist."""
        if not (isinstance(code, str) and len(code) == 13 and code.isdigit()):
            return False
        
        # EAN-13 Checksummen-Algorithmus (Modulo 10)
        # 1. Die ersten 12 Ziffern gewichtet summieren (1, 3, 1, 3...)
        digits = [int(d) for d in code]
        sum_val = sum(d * (3 if i % 2 else 1) for i, d in enumerate(digits[:-1]))
        
        # 2. Die Differenz zum nächsten Vielfachen von 10 berechnen
        check_digit = (10 - (sum_val % 10)) % 10
        
        # 3. Mit der 13. Stelle vergleichen
        return check_digit == digits[-1]

    def do_transform_ip(self, buf):
        

#print(get_product_name("5026555431866"))

        caps = self.sinkpad.get_current_caps()
        if not caps: return Gst.FlowReturn.OK
            
        struct = caps.get_structure(0)
        width, height = struct.get_value('width'), struct.get_value('height')

        result, map_info = buf.map(Gst.MapFlags.READ | Gst.MapFlags.WRITE)
        if not result: return Gst.FlowReturn.OK
        
        previously_detected_url = getattr(self, 'previously_detected_qr', None)

        try:
            image_array = np.ndarray(shape=(height, width, 3), dtype=np.uint8, buffer=map_info.data)
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    
            data, bbox = None, None
            
            # 1. QR-Check
            qr_data, qr_bbox, _ = self.qr_detector.detectAndDecode(gray)
            if qr_bbox is not None and len(qr_bbox) > 0 and qr_data:
                data, bbox = qr_data, qr_bbox
            
            # 2. EAN-Check mit "Brute Force" Pre-Processing
            elif self.barcode_detector is not None:
                # TRICK: Wir erhöhen den Kontrast massiv (CLAHE)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)
                
                # Versuch 1: Normales Bild
                res, d_info, d_type, points = self.barcode_detector.detectAndDecode(enhanced)
                
                # Versuch 2: Wenn nichts gefunden, probier ein leichtes Blur (gegen Rauschen)
                if not res or not d_info or not d_info[0]:
                    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
                    res, d_info, d_type, points = self.barcode_detector.detectAndDecode(blurred)

                if res and d_info and d_info[0]:
                    data = d_info[0]
     
                    candidate = d_info[0]
                    # JETZT: Rausfiltern von Müll
                    if self.is_valid_ean13(candidate):
                        data = candidate
                        if points is not None: bbox = np.array([points[0]])
                        print(f"Valid EAN-13 Detected: {data}")
                    else:
                        # Optional: Ignoriere Fehl-Erkennungen wie '45892431'
                        pass
                    
                    #print(f"Detected: {data}")
                    overlay.draw_text_centered(map_info, width, height, f"EAN: {data}", color=(0, 255, 0))

            # Resultat-Verarbeitung
            if bbox is not None and data:
                pts = np.int32(bbox).reshape(-1, 1, 2)
                cv2.polylines(image_array, [pts], True, (0, 255, 0), 3)

                # Speichern & Overlay
                os.makedirs("data", exist_ok=True)
                cv2.imwrite(f"data/code_{int(time.time())}.png", cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR))
                overlay.draw_text_centered(map_info, width, height, f"Found: {data}", color=(0, 255, 0))
                
                if data != previously_detected_url:
                    setattr(self, 'previously_detected_qr', data)
                    if data.startswith("http"): webbrowser.open(data)
                    print(f"Detected: {data}")
            else:
                overlay.draw_text_centered(map_info, width, height, "Searching...", color=(255, 0, 0))
            
        finally:
            buf.unmap(map_info)
        return Gst.FlowReturn.OK

GObject.type_register(QRCodeScanner)
__gstelementfactory__ = ("qrcodescanner", Gst.Rank.NONE, QRCodeScanner)

