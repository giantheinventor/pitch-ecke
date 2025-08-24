import os
from generate_qr import create_qr_code
from upload import upload
from record import start_recording, stop_recording
from ui import start_ui
from pynput import keyboard


base_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.abspath(os.path.join(base_dir, "..", "assets"))
os.makedirs(assets_dir, exist_ok=True)
output_file = os.path.join(assets_dir, "output.mp4")
qr_file = os.path.join(assets_dir, "last_qr.png")

if __name__ == "__main__":
    
    os.makedirs("assets", exist_ok=True)
    uiq = start_ui()  
    recording = {"on": False, "proc": None}

    def _status(evt):
        if evt == "started":
            uiq.put({"type": "recording", "on": True})
        elif evt == "stopped":
            uiq.put({"type": "recording", "on": False})

    def do_start():
        if recording["on"]:
            return
        recording["proc"] = start_recording(output_file, status_cb=_status)
        recording["on"] = True

    def do_stop_and_upload():
        if not recording["on"]:
            return
        stop_recording(recording["proc"], status_cb=_status)
        recording["on"] = False
        uiq.put({"type": "uploading", "on": True})
        video_link = upload(output_file)
        print(f"Video-Link: {video_link}")
        create_qr_code(video_link)
        qr_path = os.path.join(assets_dir, "qr_code.png")
        uiq.put({"type": "uploaded", "link": video_link, "qr_path": qr_path})
        uiq.put({"type": "uploading", "on": False})
        print("Bereit für die nächste Aufnahme. (Hotkey: r)")

    def on_press(key):
        try:
            ch = key.char
        except AttributeError:
            return
        if ch == "r":
            if recording["on"]:
                do_stop_and_upload()
            else:
                do_start()
        elif ch == "q":
            if recording["on"]:
                do_stop_and_upload()
            print("Beendet.")
            return False

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    listener.join()