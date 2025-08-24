import subprocess
import sys


# Plattformabhängige Geräte-IDs für Kamera und Mikrofon
if sys.platform == "win32":
    video_device = "video=Integrated Camera"  # Anpassen falls nötig
    audio_device = "audio=Mikrofonarray (Intel® Smart Sound Technologie für digitale Mikrofone)"  # Anpassen
elif sys.platform == "darwin":
    video_device = "0"  # macOS nutzt ID (0 für Standardkamera)
    audio_device = "0"  # 1 für Standardmikrofon


def start_recording(output_file, status_cb=None):
    # ffmpeg-Befehl für Video- und Audioaufnahme
    command = [
        "ffmpeg",
        "-f", "avfoundation" if sys.platform == "darwin" else "dshow",
        "-framerate", "30",
    ]
    if sys.platform == "darwin":
        command += ["-pixel_format", "nv12"]
    command += [
        "-i", f"{video_device}:{audio_device}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-y", output_file,
    ]

    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    if status_cb:
        status_cb("started")
    return process

def stop_recording(process, status_cb=None, timeout: float = 5.0):
    if process and process.poll() is None:
        try:
            process.communicate(input=b"q", timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    if status_cb:
        status_cb("stopped")