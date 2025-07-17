import qrcode
import os
from PIL import Image


def create_qr_code(link, show):
    # erstelle den Pfad zum QR-Code-Bild
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "..", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    output_file = os.path.join(assets_dir, "qr_code.png")

    link = "".join(link.split())

    qr = qrcode.QRCode(
        version=None,  # Größe des QR-Codes (1 = klein, 40 = groß)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Fehlerkorrektur-Level
        box_size=10,  # Größe der einzelnen QR-Blöcke
        border=4,  # Rand um den QR-Code
    )
    qr.add_data(link)  # Link hinzufügen
    qr.make(fit=True)

    # QR-Code als Bild generieren
    img = qr.make_image(fill="black", back_color="white")
    img.save(output_file)
    print(f"QR-Code gespeichert: {output_file}")

    if show:
        img.show()
