import subprocess
import sys
import os
import keyboard

# Plattformabhängige Geräte-IDs für Kamera und Mikrofon
if sys.platform == "win32":
    video_device = "video=Integrated Camera"  # Anpassen falls nötig
    audio_device = "audio=Mikrofonarray (Intel® Smart Sound Technologie für digitale Mikrofone)"  # Anpassen
elif sys.platform == "darwin":
    video_device = "0"  # macOS nutzt ID (0 für Standardkamera)
    audio_device = "1"  # 1 für Standardmikrofon


def start_recording(output_file):
    # ffmpeg-Befehl für Video- und Audioaufnahme
    command = [
        "ffmpeg",
        "-f",
        "avfoundation" if sys.platform == "darwin" else "dshow",  # macOS vs. Windows
        "-i",
        f"{video_device}:{audio_device}",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-y",
        output_file,
    ]
    # Startet die Aufnahme. Beendet Aufnahme durch input "q"
    print(f"Starte Aufnahme... ({output_file})")
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    keyboard.wait("q")
    process.communicate(input=b"q")
    print("Aufnahme abgeschlossen.")
