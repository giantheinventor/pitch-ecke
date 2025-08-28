import os
import time
from generate_qr import create_qr_code
from upload import upload
from record import start_recording, stop_recording
from ui import start_ui
from pynput import keyboard


base_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.abspath(os.path.join(base_dir, "../", "assets"))
os.makedirs(assets_dir, exist_ok=True)
output_file = os.path.join(assets_dir, "output.mp4")
qr_file = os.path.join(assets_dir, "last_qr.png")

mode = {"state": "idle", "qr_ignore_until": 0}  # "idle" | "recording" | "uploading" | "qr"

if __name__ == "__main__":
    
    os.makedirs("assets", exist_ok=True)
    uiq = start_ui()  
    recording = {"on": False, "proc": None}

    def do_start():
        if mode["state"] != "idle":
            return
        uiq.put({"type": "recording", "on": True})
        recording["proc"] = start_recording(output_file)
        recording["on"] = True
        mode["state"] = "recording"

    def do_stop_and_upload():
        if mode["state"] != "recording":
            return
        
        recording["on"] = False
        mode["state"] = "uploading"
        uiq.put({"type": "uploading", "on": True})
        stop_recording(recording["proc"])
        

        video_link = upload(output_file)
        print(f"Video-Link: {video_link}")

        # QR Code 
        create_qr_code(video_link)
        qr_path = os.path.join(assets_dir, "qr_code.png")

    
        uiq.put({"type": "uploading", "on": False})
        uiq.put({"type": "countdown", "seconds": 10, "qr_path": qr_path, "link": video_link})
        mode["state"] = "qr"
        mode["qr_ignore_until"] = time.time() + 30

    def on_press(key):
        try:
            ch = key.char
        except AttributeError:
            return

        if ch == "r":
            if mode["state"] == "idle":
                do_start()
            elif mode["state"] == "recording":
                do_stop_and_upload()
            elif mode["state"] == "qr":
                if time.time() < mode.get("qr_ignore_until", 0):
                    return
                uiq.put({"type": "reset"})
                mode["state"] = "idle"
            elif mode["state"] == "uploading":
                return
            else:
                pass

        elif ch == "q":
            # sauber beenden
            if mode["state"] == "recording":
                do_stop_and_upload()
            # optional: QR-Ansicht vorher schließen
            if mode["state"] == "qr":
                uiq.put({"type": "reset"})
            raise SystemExit
        
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    listener.join()