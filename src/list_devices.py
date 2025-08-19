import subprocess
import sys
import re

def list_avfoundation_devices():
    # ffmpeg gibt die Device-Liste auf stderr mit Loglevel "info" aus
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", "", "-loglevel", "info"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    lines = proc.stderr.splitlines()

    video = []
    audio = []
    section = None
    # regex trifft NICHT die erste Klammer mit der Hex-Adresse, weil dort keine reinen Ziffern stehen
    pat = re.compile(r"\[(\d+)\]\s+(.+)$")

    for raw in lines:
        line = raw.strip()

        if "AVFoundation video devices" in line:
            section = "video"
            continue
        if "AVFoundation audio devices" in line:
            section = "audio"
            continue

        m = pat.search(line)
        if m and section in ("video", "audio"):
            dev_id = int(m.group(1))
            name = m.group(2).strip()
            if section == "video":
                video.append((dev_id, name))
            else:
                audio.append((dev_id, name))

    print("Video Devices:")
    for i, name in video:
        print(f"{i}: {name}")

    print("\nAudio Devices:")
    for i, name in audio:
        print(f"{i}: {name}")

if __name__ == "__main__":
    if sys.platform != "darwin":
        print("Dieses Skript unterstützt aktuell nur macOS (avfoundation).")
        sys.exit(1)
    try:
        list_avfoundation_devices()
    except FileNotFoundError:
        print("ffmpeg nicht gefunden. Installiere es z. B. mit Homebrew: brew install ffmpeg")
        sys.exit(1)