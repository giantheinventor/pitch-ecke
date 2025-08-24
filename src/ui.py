# ui.py
from multiprocessing import Process, Queue
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import time

def _ui_loop(q: Queue):
    root = tk.Tk()
    root.title("Recorder Status")

    # Styles
    root.attributes("-fullscreen", True)
    # Keyboard shortcuts for fullscreen control
    state = {"fullscreen": True}
    def _toggle_fullscreen(event=None):
        state["fullscreen"] = not state["fullscreen"]
        root.attributes("-fullscreen", state["fullscreen"])
    def _exit_fullscreen(event=None):
        state["fullscreen"] = False
        root.attributes("-fullscreen", False)
    root.bind("<Escape>", _exit_fullscreen)  # ESC = exit fullscreen
    root.bind("<F>", _toggle_fullscreen)     # F/f = toggle
    root.bind("<f>", _toggle_fullscreen)
    root.configure(bg="#111111")

    # --- Dynamic sizing for fullscreen UI ---
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    scale = max(1.0, min(sw / 1920.0, sh / 1080.0))  # base on 1080p; never below 1.0
    SZ = {
        "PAD": int(16 * scale),
        "TITLE": max(24, int(40 * scale)),
        "STATUS": max(18, int(28 * scale)),
        "DOT": max(18, int(28 * scale)),
        "PB_LEN": int(sw * 0.5),
        "QR": int(min(sw, sh) * 0.45),
        "LINK": max(14, int(18 * scale)),
        "SUB": max(12, int(16 * scale)),
    }

    # --- Nicer ttk progressbar style ---
    style = ttk.Style()
    try:
        style.theme_use("clam")  # supports color customization well
    except Exception:
        pass
    SZ["PB_THICK"] = max(12, int(20 * scale))
    style.configure(
        "MU.Horizontal.TProgressbar",
        troughcolor="#1a1a1a",
        bordercolor="#1a1a1a",
        background="#5FB3F3",
        lightcolor="#5FB3F3",
        darkcolor="#5FB3F3",
        thickness=SZ["PB_THICK"],
        troughrelief="flat",
        relief="flat",
    )

    title = tk.Label(root, text="PITCH", fg="#FFFFFF", bg="#111111", font=("Helvetica", SZ["TITLE"] * 2, "bold"))
    title.pack(pady=(SZ["PAD"] * 2, SZ["PAD"]))

    # Status row (dot + text)
    status_frame = tk.Frame(root, bg="#111111")
    status_frame.pack(pady=SZ["PAD"])

    dot = tk.Canvas(status_frame, width=SZ["DOT"] + 6, height=SZ["DOT"] + 6, bg="#111111", highlightthickness=0)
    dot.pack(side="left")
    dot_id = dot.create_oval(3, 3, SZ["DOT"] + 3, SZ["DOT"] + 3, fill="#666666", outline="")

    status_text = tk.Label(status_frame, text="Bereit", fg="#CCCCCC", bg="#111111", font=("Helvetica", SZ["STATUS"]))
    status_text.pack(side="left", padx=SZ["PAD"])

    # Upload status
    upload_var = tk.StringVar(value="")
    upload_lbl = tk.Label(root, fg="#AAAAAA", bg="#111111", font=("Helvetica", SZ["SUB"]))
    upload_lbl.pack(pady=SZ["PAD"] // 2)

    # Progress (indeterminate)
    pb = ttk.Progressbar(root, mode="indeterminate", length=SZ["PB_LEN"], style="MU.Horizontal.TProgressbar")
    pb.pack(pady=SZ["PAD"] // 2)
    pb.stop()
    pb.pack_forget()  # verstecken bis gebraucht

    # QR image + link
    qr_label = tk.Label(root, bg="#111111")
    qr_label.pack(pady=SZ["PAD"])
    link_var = tk.StringVar(value="")
    link_lbl = tk.Label(root, textvariable=link_var, fg="#5FB3F3", bg="#111111", font=("Helvetica", SZ["LINK"]), cursor="hand2")
    link_lbl.pack()
    link_lbl.bind("<Button-1>", lambda e: root.clipboard_clear() or root.clipboard_append(link_var.get()))

    qr_img_ref = {"img": None}  # damit Tk das Image nicht weg-GCed

    def set_status(state: str):
        if state == "recording":
            dot.itemconfig(dot_id, fill="#EA4335")
            status_text.config(text="● Recording…", fg="#EA4335")
        elif state == "uploading":
            dot.itemconfig(dot_id, fill="#FFD700")
            status_text.config(text="● Uploading…", fg="#FFD700")
        else:
            dot.itemconfig(dot_id, fill="#34A853")
            status_text.config(text="Idle", fg="#34A853")

    def set_uploading(on: bool):
        if on:
            pb.pack(pady=SZ["PAD"] // 2)
            pb.start(12)
        else:
            pb.stop()
            pb.pack_forget()
            upload_var.set("")

    def show_qr(qr_path: str | None, link: str | None):
        # Bild (falls vorhanden)
        if qr_path and os.path.exists(qr_path):
            try:
                im = Image.open(qr_path).resize((SZ["QR"], SZ["QR"]))
                qr_img_ref["img"] = ImageTk.PhotoImage(im)
                qr_label.config(image=qr_img_ref["img"])
            except Exception:
                qr_label.config(image="", text="QR konnte nicht geladen werden", fg="#CCCCCC")
        else:
            qr_label.config(image="", text="", fg="#CCCCCC")
        # Link anzeigen
        link_var.set(link or "")

    def poll_queue():
        try:
            while True:
                evt = q.get_nowait()
                etype = evt.get("type")
                if etype == "recording":
                    set_status("recording" if evt.get("on") else "idle")
                    # beim Start/Stop QR ausblenden
                    if evt.get("on"):
                        show_qr(None, None)
                elif etype == "uploading":
                    set_uploading(bool(evt.get("on")))
                    set_status("uploading" if evt.get("on") else "idle")                    
                elif etype == "uploaded":
                    # { "link": ..., "qr_path": ... }
                    set_uploading(False)
                    show_qr(evt.get("qr_path"), evt.get("link"))
                elif etype == "message":
                    upload_var.set(str(evt.get("text", "")))
        except Exception:
            pass
        root.after(120, poll_queue)

    poll_queue()
    root.mainloop()

def start_ui() -> Queue:
    """
    Startet die UI in einem separaten Prozess und gibt die Queue zurück.
    Sende Events mit: q.put({...})
    """
    q = Queue()
    p = Process(target=_ui_loop, args=(q,), daemon=True)
    p.start()
    return q