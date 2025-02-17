import subprocess
import sys
import os

# Speicherpfad für das Video
output_file = "../assets/output.mp4"

# Plattformabhängige Geräte-IDs für Kamera und Mikrofon
if sys.platform == "win32":
    video_device = "video=Integrated Camera"  # Anpassen falls nötig
elif sys.platform == "darwin":
    video_device = "0"  # macOS nutzt ID (0 für Standardkamera)
   

# ffmpeg-Befehl für Video- und Audioaufnahme
command = [
    "ffmpeg",
    "-f", "avfoundation" if sys.platform == "darwin" else "dshow",  # macOS vs. Windows
    "-i", video_device,
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-crf", "23",
    "-pix_fmt", "yuv420p",
    output_file
]

def start_recording():
    """Startet die Videoaufnahme mit ffmpeg."""
    print(f"Starte Aufnahme... ({output_file})")
    subprocess.run(command)
    print("Aufnahme abgeschlossen.")

if __name__ == "__main__":
    # Erstelle den assets-Ordner, falls er nicht existiert
    os.makedirs("assets", exist_ok=True)
    start_recording()
