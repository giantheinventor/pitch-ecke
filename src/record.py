import subprocess
import sys
import os
import select
import tty
import termios

# Plattformabhängige Geräte-IDs für Kamera und Mikrofon
if sys.platform == "win32":
    video_device = "video=Integrated Camera"  # Anpassen falls nötig
    audio_device = "audio=Mikrofonarray (Intel® Smart Sound Technologie für digitale Mikrofone)"  # Anpassen
elif sys.platform == "darwin":
    print("darwin")
    video_device = "0"  # macOS nutzt ID (0 für Standardkamera)
    audio_device = "0"  # 1 für Standardmikrofon

def wait_for_keypress():
    """Gibt den gedrückten Key als String zurück, ohne Enter zu benötigen."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)  # Sofortige Auswertung der Tastenanschläge
        while True:
            r, _, _ = select.select([sys.stdin], [], [], 0.1)
            if r:
                ch = sys.stdin.read(1)
                return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)



def start_recording(output_file):
    # ffmpeg-Befehl für Video- und Audioaufnahme
    command = [
        "ffmpeg",
        "-f", "avfoundation" if sys.platform == "darwin" else "dshow",
        "-framerate", "30",
    ]

    # Auf macOS das Input-Pixelformat für avfoundation setzen
    if sys.platform == "darwin":
        command += ["-pixel_format", "nv12"]

    command += [
        "-i", f"{video_device}:{audio_device}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        # Für maximale Player-Kompatibilität im MP4-Container
        "-pix_fmt", "yuv420p",
        "-y", output_file,
    ]
    # Startet die Aufnahme. Beendet Aufnahme durch input "q"
    print(f"Starte Aufnahme... ({output_file})")
    print(command)
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    while True:
        key = wait_for_keypress()
        print(f"Taste: {key!r}")
        if key.lower() == 'q':
            print("Beendet.")
            break
    process.communicate(input=b"q")
    print("Aufnahme abgeschlossen.")
