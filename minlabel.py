import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showwarning
from glob import glob
import os
from pathlib import Path
from pygame import mixer
import wave
import contextlib
import json

JSON_FILENAME = "status.json"


def show_size(bytes: int) -> str:
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes // 1024 < 1024:
        return f"{round(bytes / 1024, 2)} KB"
    else:
        return f"{round(bytes / (1024 * 1024), 2)} MB"


def process_label(content: str) -> str:
    return " ".join(content.strip().split())


def check_no_diff(label_content: str, show_content: str) -> bool:
    label_content = process_label(label_content)
    return label_content == show_content.rstrip()


class MinLabel(tk.Tk):
    def __init__(self):
        super().__init__()
        # pygame mixer
        mixer.init()
        # global var
        self.status = {}  # filename -> bool
        self.track = tk.StringVar()
        self.track.set("Select audio file.")
        self.is_ready = tk.BooleanVar()
        self.lab_path = ""
        self.status_for_button = tk.StringVar()  # play/pause
        self.status_for_button.set("play")
        self.last_dir = "/"
        self.open_dir = ""
        # configure the root window
        self.title("MinLabel")
        self.geometry("1000x600")
        # frame & widget
        self.create_menu()
        self.create_treeview()
        self.create_right_frame()
        # bind event
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Control-o>", self.open_folder)
        self.bind("<Control-O>", self.open_folder)
        self.bind("<Control-s>", self.status_ready)
        self.bind("<Control-S>", self.status_ready)
        self.bind("<Control-s>", self.replace_content, add="+")
        self.bind("<Control-S>", self.replace_content, add="+")
        self.bind("<Control-p>", self.play_music)
        self.bind("<Control-P>", self.play_music)
        self.bind("<Control-Up>", self.switch_prev)
        self.bind("<Control-Down>", self.switch_next)
        self.bind("<Button-1>", self.focus_change)
        self.bind("<Key>", self.key_pressed)

    def create_menu(self):
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar, tearoff=False)
        # add a menu item to the menu
        self.file_menu.add_command(
            label="Open Folder",
            command=self.open_folder,
            accelerator="Ctrl+O",
        )
        # add the File menu to the menubar
        self.menubar.add_cascade(label="File", menu=self.file_menu)

    def create_treeview(self):
        self.table_frame = tk.Frame(
            self, highlightbackground="grey", highlightthickness=1, width=300
        )
        self.table_frame.pack(
            ipadx=10, ipady=10, fill=tk.BOTH, expand=True, side=tk.LEFT
        )
        self.table = ttk.Treeview(
            master=self.table_frame,
            height=20,
            columns=["Name", "Size", "Status"],
            show="headings",
            selectmode="browse",
        )
        self.table.column("Name", minwidth=50, width=100, anchor=tk.W)
        self.table.column("Size", width=80, anchor=tk.W)
        self.table.column("Status", width=50, anchor=tk.W)
        self.table.heading("Name", text="Name", anchor=tk.W)
        self.table.heading("Size", text="Size", anchor=tk.W)
        self.table.heading("Status", text="Status", anchor=tk.W)
        self.table.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.vscrol = tk.Scrollbar(
            self.table_frame, orient=tk.VERTICAL, command=self.table.yview
        )
        self.vscrol.pack(fill=tk.BOTH, expand=True)
        self.table.configure(yscrollcommand=self.vscrol.set)

    def create_right_frame(self):
        self.right_frame = tk.Frame(
            self, highlightbackground="grey", highlightthickness=1
        )
        self.right_frame.pack(
            ipadx=10, ipady=10, fill=tk.BOTH, expand=True, side=tk.LEFT
        )
        # right top
        self.right_top_frame = tk.Frame(
            self.right_frame, highlightbackground="grey", highlightthickness=1
        )
        self.right_top_frame.pack(fill=tk.BOTH)
        self.filename_label = tk.Label(self.right_top_frame, textvariable=self.track)
        self.filename_label.pack(fill=tk.X, expand=True)
        self.progress = ttk.Progressbar(
            self.right_top_frame, orient=tk.HORIZONTAL, mode="determinate"
        )
        self.progress.pack(fill=tk.X, expand=True)
        # right middle
        self.button_frame = tk.Frame(
            self.right_frame, highlightbackground="grey", highlightthickness=1
        )
        self.button_frame.pack(fill=tk.BOTH)

        self.replace_button = ttk.Button(
            self.button_frame, text="replace", command=self.replace_content
        )

        # play and stop button
        self.play_button = ttk.Button(
            self.button_frame,
            textvariable=self.status_for_button,
            command=self.play_music,
        )
        # play and stop button
        self.stop_button = ttk.Button(
            self.button_frame, text="stop", command=self.stop_music
        )
        # button delete file
        self.delete_button = ttk.Button(
            self.button_frame, text="delete", command=self.delete_file
        )
        self.ready_check = ttk.Checkbutton(
            self.button_frame,
            text="Ready",
            command=self.status_change,
            variable=self.is_ready,
            onvalue=True,
            offvalue=False,
        )
        self.replace_button.grid(row=0, column=0)
        self.play_button.grid(row=0, column=1)
        self.stop_button.grid(row=0, column=2)
        self.delete_button.grid(row=0, column=3)
        self.ready_check.grid(row=0, column=4)
        # right bottom
        self.right_bottom_frame = tk.Frame(
            self.right_frame, highlightbackground="grey", highlightthickness=1
        )
        self.right_bottom_frame.pack(fill=tk.BOTH, expand=True)

        self.label_text = tk.Text(self.right_bottom_frame, height=5)
        self.label_text.configure(font=("Courier New", 12))
        self.label_text.pack(ipadx=10, fill=tk.X)
        # read only
        self.show_text = tk.Text(self.right_bottom_frame)
        self.show_text.configure(font=("Courier New", 12), state="disabled")
        self.show_text.pack(fill=tk.BOTH, expand=True)

    def clear(self):
        self.stop_music()
        for item in self.table.get_children():
            self.table.delete(item)
        self.track.set("Select audio file.")
        self.lab_path = ""
        self.status_for_button.set("play")
        self.clear_text()
        self.is_ready.set(False)
        self.open_dir = ""

    def open_folder(self, *args):
        dirname = askdirectory(
            title="Open files",
            initialdir=self.last_dir,
        )
        if not os.path.isdir(dirname):
            return
        self.save_status()
        self.clear()
        self.open_dir = dirname
        self.last_dir = Path(dirname).parent
        # read status.json
        if os.path.exists(os.path.join(self.open_dir, JSON_FILENAME)):
            with open(
                os.path.join(self.open_dir, JSON_FILENAME), encoding="utf-8"
            ) as f:
                self.status = json.loads(f.read())
        # order by modified time
        glob_lst = sorted(glob(f"{dirname}/*.wav"), key=os.path.getmtime)
        new_status = {}
        for idx, file_path in enumerate(glob_lst):
            path = Path(file_path)
            status = self.status.get(path.name, False)
            new_status[path.name] = status
            size = show_size(os.path.getsize(file_path))
            self.table.insert(
                parent="",
                index=idx,
                values=(path.name, size, str(status)),
            )
        self.status = new_status

    def play_music(self, event=None):
        if mixer.music.get_busy():  # Playing
            self.status_for_button.set("play")
            mixer.music.pause()
        elif mixer.music.get_pos() >= 0:  # Pause
            self.status_for_button.set("pause")
            mixer.music.unpause()
            self.after(25, self.update_progress)
        elif os.path.isfile(self.track.get()):  # Stopped
            self.status_for_button.set("pause")
            mixer.music.load(self.track.get())
            with contextlib.closing(wave.open(self.track.get(), "r")) as f:
                rate = f.getframerate()
                frames = f.getnframes()
                duration = frames / rate
            self.progress["maximum"] = duration * 1000  # ms
            self.progress["value"] = 0
            mixer.music.play()
            self.after(25, self.update_progress)

    def stop_music(self):
        self.progress["value"] = 0
        mixer.music.stop()
        mixer.music.unload()

    def focus_change(self, event=None):
        cur = self.table.focus()
        values = self.table.item(cur)["values"]
        # no focus
        if not values:
            self.clear_text()
            return
        wav_name = values[0]
        status = values[-1]
        track = os.path.join(Path(self.open_dir), wav_name)
        if self.track.get() != track:
            # print("focus change", track)
            self.stop_music()
            self.track.set(track)
            self.is_ready.set(status == "True")
            lab_name = wav_name[:-3] + "lab"
            lab_path = os.path.join(self.open_dir, lab_name)
            self.lab_path = lab_path
            if not os.path.exists(lab_path):
                with open(lab_path, "w", encoding="utf-8") as f:
                    f.write("")
            content = ""
            with open(lab_path, "r", encoding="utf-8") as f:
                content = f.readline()
            self.write_show_text(content)
            self.label_text.delete("1.0", tk.END)
            self.label_text.insert("1.0", content)
            self.star_title()
        else:
            pass

    def update_progress(self):
        self.progress["value"] = max(mixer.music.get_pos(), 0)
        if mixer.music.get_busy():
            self.after(25, self.update_progress)
        else:
            self.status_for_button.set("play")
            if mixer.music.get_pos() <= 0:  # stopped
                mixer.music.unload()

    def replace_content(self, event=None):
        if not self.table.focus() or not os.path.isfile(self.lab_path):
            return
        new_content = self.label_text.get("0.0", tk.END)
        new_content = process_label(new_content)
        self.write_show_text(new_content)
        with open(self.lab_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    def delete_file(self):
        if not self.table.focus():
            return
        os.remove(self.lab_path)
        os.remove(self.track.get())
        # focus next item after delete
        cur = self.table.focus()
        next = self.table.next(cur)
        self.table.delete(cur)
        if next:  # not last
            self.table.focus(next)
            self.table.selection_clear()
            self.table.selection_add(next)
        self.focus_change()

    def save_status(self):
        if not os.path.exists(self.open_dir):
            return
        path = os.path.join(self.open_dir, JSON_FILENAME)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.status, f)
        print(f"saved file {path}")

    def close(self):
        self.save_status()
        self.destroy()

    def status_change(self):
        if not os.path.exists(self.track.get()):
            return
        wav_name = Path(self.track.get()).name
        self.status[wav_name] = self.is_ready.get()
        cur = self.table.focus()
        values = list(self.table.item(cur)["values"])
        values[-1] = str(self.is_ready.get())
        self.table.item(self.table.focus(), values=tuple(values))

    def status_ready(self, event=None):
        self.is_ready.set(True)
        self.status_change()

    def focus_on_label(self, event=None):
        self.label_text.focus_set()

    def focus_on_table(self, event=None):
        self.table.focus_set()

    def switch_prev(self, event=None):
        self.focus_on_table()
        self.table.tk_focusPrev()
        self.focus_change()

    def switch_next(self, event=None):
        self.focus_on_table()
        self.table.tk_focusNext()
        self.focus_change()

    def key_pressed(self, event=None):
        if event.char in ["i", "I"]:
            self.focus_on_label()
        elif event.keysym == "Escape":
            self.focus_on_table()
        self.focus_change()

    def star_title(self, event=None):
        label_content = self.label_text.get("0.0", tk.END)
        show_content = self.show_text.get("0.0", tk.END)
        if check_no_diff(label_content, show_content):
            self.title("MinLabel")
        else:
            self.title("*MinLabel")

    def clear_text(self):
        self.write_show_text("")
        self.label_text.delete("1.0", tk.END)

    def write_show_text(self, content):
        self.show_text.configure(state="normal")
        self.show_text.delete("1.0", tk.END)
        self.show_text.insert("1.0", content)
        self.show_text.configure(state="disabled")

    def report_callback_exception(self, exc, val, tb):
        showwarning("warning", message=str(val))

    # def debug(self):
    #     print(self.table.focus())
    #     print(
    #         "get pos",
    #         mixer.music.get_pos(),
    #         "get busy",
    #         mixer.music.get_busy(),
    #     )
    #     print(self.progress["value"], "/", self.progress["maximum"])


if __name__ == "__main__":
    app = MinLabel()
    app.mainloop()
