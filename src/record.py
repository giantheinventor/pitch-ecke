import subprocess
import signal
import re
import os
from types import SimpleNamespace
from typing import Optional

# -----------------------------
# Bevorzugte Gerätebezeichnungen (stabiler als wechselnde Indizes)
# Passe diese Listen bei Bedarf an die Namen aus Audio-MIDI-Setup / ffmpeg -list_devices an.
# -----------------------------
PREFERRED_VIDEO = [
    "OBSBOT Tail Air Camera"
]
PREFERRED_AUDIO = [
    "Studio Display Microphone"
    #"OBSBOT Tail Air Microphone"
]

# Audio-Defaults – an dein Mic anpassen (1 Kanal ist bei dir üblich)
SAMPLING_RATE = "48000"  # "44100" oder "48000"
CHANNELS = "1"           # dein Mic liefert 1 Kanal

_DEVICE_LIST_RE = re.compile(r"\[(\d+)\]\s+(.*)")


def _resolve_avfoundation_devices() -> tuple[str, str]:
    """Ermittle zur Laufzeit die aktuelle Video-Index (für ffmpeg) und Audio-Gerätenamen (für SoX).
    Rückgabe: (video_index_syntax, audio_device_name).
      - video_index_syntax: z.B. "0:" (wird von ffmpeg/avfoundation erwartet)
      - audio_device_name: exakter Gerätename für SoX/CoreAudio (z.B. "Studio Display Microphone")
    Fallback: ("0:", "default")
    """
    try:
        proc = subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True, text=True, check=False
        )
        out = proc.stdout + proc.stderr
    except Exception:
        return "0:", "default"

    video_idx = None
    audio_name = None
    mode = None
    for line in out.splitlines():
        if "AVFoundation video devices:" in line:
            mode = "video"; continue
        if "AVFoundation audio devices:" in line:
            mode = "audio"; continue
        m = _DEVICE_LIST_RE.search(line)
        if not m:
            continue
        idx, name = m.group(1), m.group(2).strip()
        if mode == "video" and video_idx is None:
            for want in PREFERRED_VIDEO:
                if want.lower() in name.lower():
                    video_idx = idx
                    break
        if mode == "audio" and audio_name is None:
            for want in PREFERRED_AUDIO:
                if want.lower() in name.lower():
                    audio_name = name
                    break

    if video_idx is None:
        video_idx = "0"
    if audio_name is None:
        audio_name = "default"

    return f"{video_idx}:", audio_name



class _RecHandle(SimpleNamespace):
    """Kleiner Wrapper, damit .poll() wie bei subprocess.Popen verfügbar ist."""
    def poll(self):
        # Wenn Video-Prozess existiert, den Status verwenden
        p = getattr(self, "p_video", None)
        if p is not None:
            return p.poll()
        return None


def start_recording(output_file, status_cb=None):
    """Startet getrennte Aufnahme: Video (FFmpeg) -> *_video.mp4, Audio (SoX) -> *_audio.wav.
    Beim späteren stop_recording() wird beides zu output_file gemerged.
    Gibt einen Handle zurück, der an stop_recording() übergeben wird.
    """
    base = os.path.splitext(output_file)[0]
    video_raw = f"{base}__video.mp4"
    audio_raw = f"{base}__audio.wav"

    # Sicherstellen, dass Ziel-Ordner existiert
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    video_dev, audio_name = _resolve_avfoundation_devices()
    print(f"[record] VIDEO={video_dev}  AUDIO(SoX)='{audio_name}'  -> {video_raw} + {audio_raw}")

    # --- VIDEO ONLY (FFmpeg) ---
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "avfoundation",
        "-framerate", "30",
        "-pixel_format", "nv12",
        "-video_size", "1920x1080",
        "-i", video_dev,
        # Video-Encode (Hardware, kein Audio)
        "-c:v", "h264_videotoolbox",
        "-b:v", "8000k",
        "-maxrate", "10000k",
        "-bufsize", "12000k",
        "-profile:v", "high",
        "-level", "4.1",
        "-g", "60",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",  # explizit KEIN Audio in dieser Datei
        "-y", video_raw,
    ]
    p_video = subprocess.Popen(ffmpeg_cmd, start_new_session=True)

    # --- AUDIO ONLY (SoX -> WAV Datei) ---
    sox_cmd = [
        "sox",
        "-t", "coreaudio", audio_name,
        "-r", SAMPLING_RATE,
        "-c", CHANNELS,
        "-b", "16",
        "-e", "signed-integer",
        audio_raw,
    ]
    p_audio = subprocess.Popen(sox_cmd, start_new_session=True)

    h = _RecHandle(p_video=p_video, p_audio=p_audio, video_raw=video_raw, audio_raw=audio_raw,
                   output_file=output_file, status_cb=status_cb)

    if status_cb:
        status_cb("started")
    return h


def stop_recording(process, status_cb=None, timeout: float = 8.0):
    """Beendet beide Rohaufnahmen und merged anschließend zu output_file."""
    if isinstance(process, _RecHandle):
        h = process
    else:
        # Fallback, falls fremder Typ – versuchen, bekannte Felder zu lesen
        h = SimpleNamespace(
            p_video=getattr(process, "p_video", None),
            p_audio=getattr(process, "p_audio", None),
            video_raw=getattr(process, "video_raw", None),
            audio_raw=getattr(process, "audio_raw", None),
            output_file=getattr(process, "output_file", None),
            status_cb=status_cb,
        )

    # 1) Rohprozesse beenden
    if h.p_audio and h.p_audio.poll() is None:
        try:
            h.p_audio.terminate()
            h.p_audio.wait(timeout=2.5)
        except Exception:
            try:
                h.p_audio.kill()
            except Exception:
                pass

    if h.p_video and h.p_video.poll() is None:
        try:
            h.p_video.send_signal(signal.SIGINT)
            h.p_video.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            h.p_video.kill()
            h.p_video.wait()

    # 2) Merge (Video+Audio -> finale MP4)
    if h.video_raw and h.audio_raw and h.output_file:
        merge_cmd = [
            "ffmpeg",
            "-i", h.video_raw,
            "-i", h.audio_raw,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",         
            "-c:a", "aac",
            "-b:a", "320k",
            "-ar", SAMPLING_RATE,
            "-ac", CHANNELS,
            "-shortest",
            "-movflags", "+faststart",
            "-y", h.output_file,
        ]
        print("[record] Merge:", " ".join(merge_cmd))
        subprocess.run(merge_cmd, check=True)

    # 3) Temp-Dateien aufräumen
    try:
        if h.video_raw and os.path.exists(h.video_raw):
            os.remove(h.video_raw)
    except Exception:
        pass
    try:
        if h.audio_raw and os.path.exists(h.audio_raw):
            os.remove(h.audio_raw)
    except Exception:
        pass

    if status_cb:
        status_cb("stopped")