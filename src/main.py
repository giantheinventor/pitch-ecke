import os
from generate_qr import create_qr_code
from upload import upload
from record import start_recording

base_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.abspath(os.path.join(base_dir, "..", "assets"))
os.makedirs(assets_dir, exist_ok=True)
output_file = os.path.join(assets_dir, "output.mp4")

if __name__ == "__main__":
    print("started")
    os.makedirs("assets", exist_ok=True)
    print("assets")
    start_recording(output_file)
    video_link = upload(output_file)
    print(f"Video-Link: {video_link}")
    create_qr_code(video_link, show=True)
