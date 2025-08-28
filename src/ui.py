# ui.py
from multiprocessing import Process, Queue
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
from pathlib import Path

QR_CODE_TIMER = 60
TITLE = "Engine"

def _ui_loop(q: Queue):
    root = tk.Tk()
    root.title("Recorder Status")
    remaining = 0

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
    scale = max(1.0, min(sw / 1920.0, sh / 1080.0)) 
    SZ = {
        "PAD": int(24 * scale),                 # mehr Luft
        "TITLE": max(32, int(64 * scale)),      # Logo-Fallback/Countdown groß
        "STATUS": max(24, int(42 * scale)),     # Status-Text deutlich größer
        "DOT": max(24, int(36 * scale)),        # Status-Punkt größer
        "PB_LEN": int(sw * 0.65),               # längere Progressbar
        "QR": int(min(sw, sh) * 0.45),          # größerer QR (≈ 55% der kleineren Kante)
        "LINK": max(18, int(24 * scale)),       # größerer Link-Text
        "SUB": max(16, int(20 * scale)),        # Sub-/Hinweistext größer
    }
    # Progressbar
    style = ttk.Style()
    try:
        style.theme_use("clam") 
    except Exception:
        pass
    SZ["PB_THICK"] = max(18, int(28 * scale))
    style.configure(
        "MU.Horizontal.TProgressbar",
        troughcolor="#080808",
        bordercolor="#080808",
        background="#5FB3F3",
        lightcolor="#5FB3F3",
        darkcolor="#5FB3F3",
        thickness=SZ["PB_THICK"],
        troughrelief="flat",
        relief="flat",
    )

    # Logo instead of text title
    logo_label = tk.Label(root, bg="#111111")
    logo_label.pack(pady=(SZ["PAD"] * 2, SZ["PAD"]))

    
    base_dir = Path(__file__).resolve().parent
    assets_dir = (base_dir / ".." / "assets").resolve()
    logo_path = assets_dir / "Engine-logo.png"

    logo_img_ref = {"img": None}
    if logo_path.exists():
        try:
            im = Image.open(str(logo_path))
            # Scale logo to ~30% of screen width
            target_w = int(sw * 0.45)
            w, h = im.size
            if w > 0:
                scale_factor = target_w / float(w)
                new_w = int(w * scale_factor)
                new_h = int(h * scale_factor)
                im = im.resize((new_w, new_h))
            logo_img_ref["img"] = ImageTk.PhotoImage(im)
            logo_label.config(image=logo_img_ref["img"])
        except Exception:
            logo_label.config(text=TITLE, fg="#FFFFFF", bg="#111111", font=("Helvetica", SZ["TITLE"] * 2, "bold"))
    else:
        logo_label.config(text=TITLE, fg="#FFFFFF", bg="#111111", font=("Helvetica", SZ["TITLE"] * 2, "bold"))

    # Status row (dot + text)
    status_frame = tk.Frame(root, bg="#111111")
    status_frame.pack(pady=SZ["PAD"])

    dot = tk.Canvas(status_frame, width=SZ["DOT"] + 6, height=SZ["DOT"] + 6, bg="#111111", highlightthickness=0)
    dot.pack(side="left")
    dot_id = dot.create_oval(3, 3, SZ["DOT"] + 3, SZ["DOT"] + 3, fill="#34A853", outline="")
    dot.pack_forget()

    status_text = tk.Label(status_frame, text="Press button to record...", fg="#595959", bg="#111111", font=("Helvetica", SZ["TITLE"]))
    status_text.pack(side="right", pady=(SZ["PAD"] * 5, SZ["PAD"]))

    # Upload status
    upload_var = tk.StringVar(value="")
    upload_lbl = tk.Label(root, textvariable=upload_var, fg="#AAAAAA", bg="#111111", font=("Helvetica", SZ["SUB"]))
    upload_lbl.pack(pady=(SZ["PAD"] , SZ["PAD"] // 3))

    # Progress (indeterminate)
    pb = ttk.Progressbar(root, mode="indeterminate", length=SZ["PB_LEN"], style="MU.Horizontal.TProgressbar")
    pb.pack(pady=SZ["PAD"] // 2)
    pb.stop()
    pb.pack_forget()  

    # QR image + link
    qr_label = tk.Label(root, bg="#111111")
    qr_label.pack(pady=(int(SZ["PAD"] * 0.1), int(SZ["PAD"] * 0.4)))


    qr_img_ref = {"img": None} 

    # Countdown label (hidden by default)
    countdown_var = tk.StringVar(value="")
    countdown_lbl = tk.Label(
        root,
        textvariable=countdown_var,
        fg="#FFFFFF",
        bg="#111111",
        font=("Helvetica", max(SZ["TITLE"], int(SZ["TITLE"] * 1.2)), "bold"),
    )
    countdown_lbl.pack(pady=SZ["PAD"])
    countdown_lbl.pack_forget()    

    def start_countdown(seconds: int, qr_path: str | None, link: str | None):

        set_uploading(False)
        set_status("idle")
        show_qr(qr_path, link)

        nonlocal remaining
        remaining = max(0, int(seconds))

        def tick():
            nonlocal remaining
            if remaining > 0:
                countdown_lbl.pack(pady=SZ["PAD"])
                countdown_var.set(f"Active in {remaining}...")
                remaining -= 1
                root.after(1000, tick)
            else:
                countdown_lbl.pack_forget()

        tick()
    
    def set_status(state: str):
        if state == "recording":
            dot.itemconfig(dot_id, fill="#FD5F31")
            dot.pack(side="left")
            status_text.config(text="Recording…", fg="#FD5F31")
        elif state == "uploading":
            dot.itemconfig(dot_id, fill="#F9A0B4")
            status_text.config(text="Uploading…", fg="#F9A0B4")
        elif state == "hide":
            status_frame.pack_forget()
            return
        else:
            status_text.config(text="Press button ● to record...", fg="#9c9c9c")
            dot.pack_forget()
        
        status_frame.pack(pady=SZ["PAD"])

    def set_uploading(on: bool):
        if on:
            pb.pack(pady=SZ["PAD"] // 2)
            pb.start(12)
        else:
            pb.stop()
            pb.pack_forget()
            upload_var.set("")

    def show_qr(qr_path: str | None, link: str | None):
        if qr_path and os.path.exists(qr_path):
            try:
                im = Image.open(qr_path).resize((SZ["QR"], SZ["QR"]))
                qr_img_ref["img"] = ImageTk.PhotoImage(im)
                qr_label.config(image=qr_img_ref["img"])
            except Exception:
                qr_label.config(image="", text="QR konnte nicht geladen werden", fg="#CCCCCC")
        else:
            qr_label.config(image="", text="", fg="#CCCCCC")

    def clear_to_idle():
        # QR & Link verstecken
        qr_label.config(image="", text="", fg="#CCCCCC")
        nonlocal remaining 
        remaining = 0
        try:
            countdown_lbl.pack_forget()
        except Exception:
            pass
        set_uploading(False)
        set_status("idle")

    def poll_queue():
        try:
            while True:
                evt = q.get_nowait()
                etype = evt.get("type")
                if etype == "recording":
                    set_status("recording" if evt.get("on") else "idle")
                    if evt.get("on"):
                        show_qr(None, None)
                elif etype == "uploading":
                    set_uploading(bool(evt.get("on")))
                    set_status("uploading" if evt.get("on") else "idle")   
                elif etype == "countdown":
                    start_countdown(QR_CODE_TIMER, evt.get("qr_path"), evt.get("link"))
                    set_status("hide")
                elif etype == "reset":
                    clear_to_idle()
                elif etype == "message":
                    upload_var.set(str(evt.get("text", "")))
        except Exception:
            pass
        root.after(120, poll_queue)

    poll_queue()
    root.mainloop()

def start_ui() -> Queue:
    q = Queue()
    p = Process(target=_ui_loop, args=(q,), daemon=True)
    p.start()
    return q