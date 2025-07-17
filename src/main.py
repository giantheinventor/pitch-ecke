import os
from generate_qr import create_qr_code
from upload import upload
from record import start_recording

output_file = "~/../assets/output.mp4"

if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    start_recording(output_file)
    video_link = upload(output_file)
    print(f"Video-Link: {video_link}")
    create_qr_code(video_link, show=True)
