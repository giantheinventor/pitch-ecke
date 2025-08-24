import qrcode
import os


def create_qr_code(link):
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "..", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    output_file = os.path.join(assets_dir, "qr_code.png")
    link = "".join(link.split())

    qr = qrcode.QRCode(
        version=None,  
        error_correction=qrcode.constants.ERROR_CORRECT_L,  
        box_size=10,  
        border=4, 
    )
    qr.add_data(link)  
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")
    img.save(output_file)
