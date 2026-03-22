import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GstBase, GstVideo, GObject
import zbar
from PIL import Image

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
        self.scanner = zbar.Scanner()

    def do_transform_ip(self, buf):
        caps = self.sinkpad.get_current_caps()
        if not caps:
            return Gst.FlowReturn.OK
            
        struct = caps.get_structure(0)
        width = struct.get_value('width')
        height = struct.get_value('height')

        result, map_info = buf.map(Gst.MapFlags.READ)
        if not result:
            return Gst.FlowReturn.OK

        try:
            # Bild verarbeiten
            image = Image.frombytes('RGB', (width, height), map_info.data)
            gray_image = image.convert('L')
            results = self.scanner.scan(gray_image.tobytes(), width, height)
            
            for res in results:
                data = res.data.decode('utf-8')
                print(f"QR Code detected: {data}")
        finally:
            # EXTREM WICHTIG: Buffer unmappen!
            buf.unmap(map_info)

        return Gst.FlowReturn.OK

# --- DAS HIER MUSS ANS ENDE DER DATEI ---
# Registriert die Klasse im GObject-System
GObject.type_register(QRCodeScanner)

# Diese magische Variable sucht der gst-python Loader!
__gstelementfactory__ = ("qrcodescanner", Gst.Rank.NONE, QRCodeScanner)


# Am Ende deiner qrcodescanner.py:
from gi.repository import GObject
GObject.type_register(QRCodeScanner) # QRCodeScanner ist dein Klassenname
__gstelementfactory__ = ("qrcodescanner", Gst.Rank.NONE, QRCodeScanner)