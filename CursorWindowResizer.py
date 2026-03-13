import os
from tkinter import Tk, Button, Label, Entry, StringVar, filedialog, Frame

from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD


MAX_FILES = 5


class ZenvaResizerGUI:
    def __init__(self, root: Tk) -> None:
        root.title("ZenvaResizer (Desktop) - drag images here")
        self.root = root
        self.filepaths: list[str] = []
        self.previews: list[ImageTk.PhotoImage] = []
        self.output_dir: str | None = None

        self.width_var = StringVar(value="400")
        self.height_var = StringVar(value="300")
        self.quality_var = StringVar(value="85")

        Button(root, text="Choose Images (max 5)", command=self.choose_files).pack(pady=5)

        self.info_label = Label(root, text="No files selected.")
        self.info_label.pack()
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.on_drop_files)

        Button(root, text="Choose Output Folder", command=self.choose_output_dir).pack(
            pady=(0, 5)
        )

        self.output_label = Label(root, text="No output folder selected.")
        self.output_label.pack()

        form = Frame(root)
        form.pack(pady=5)

        Label(form, text="Width:").grid(row=0, column=0, sticky="e")
        Entry(form, textvariable=self.width_var, width=6).grid(row=0, column=1)

        Label(form, text="Height:").grid(row=0, column=2, sticky="e")
        Entry(form, textvariable=self.height_var, width=6).grid(row=0, column=3)

        Label(form, text="Quality (1-100):").grid(row=0, column=4, sticky="e")
        Entry(form, textvariable=self.quality_var, width=6).grid(row=0, column=5)

        Button(root, text="Resize Images", command=self.resize_images).pack(pady=5)

        self.preview_frame = Frame(root)
        self.preview_frame.pack(pady=5)

        self.status_label = Label(root, text="", fg="red")
        self.status_label.pack()

    def choose_files(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg")],
        )
        # Keep only first MAX_FILES
        self.filepaths = list(files)[:MAX_FILES]
        self.info_label.config(
            text=f"{len(self.filepaths)} file(s) selected (max {MAX_FILES})."
        )

    def on_drop_files(self, event) -> None:
        raw = event.data
        paths: list[str] = []
        current = ""
        in_brace = False
        for ch in raw:
            if ch == "{":
                in_brace = True
                current = ""
            elif ch == "}":
                in_brace = False
                if current:
                    paths.append(current)
                    current = ""
            elif ch == " " and not in_brace:
                if current:
                    paths.append(current)
                    current = ""
            else:
                current += ch
        if current:
            paths.append(current)

        # Filter image files and respect MAX_FILES
        exts = {".png", ".jpg", ".jpeg"}
        image_paths = [
            p for p in paths if os.path.splitext(p)[1].lower() in exts and os.path.isfile(p)
        ][:MAX_FILES]

        if not image_paths:
            self.status_label.config(text="No valid image files in drop.")
            return

        self.filepaths = image_paths
        self.info_label.config(
            text=f"{len(self.filepaths)} file(s) selected via drag & drop (max {MAX_FILES})."
        )

    def clear_previews(self) -> None:
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        self.previews.clear()

    def choose_output_dir(self) -> None:
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir = folder
            self.output_label.config(text=f"Output folder: {folder}")
        else:
            self.output_dir = None
            self.output_label.config(text="No output folder selected.")

    def resize_images(self) -> None:
        self.status_label.config(text="")
        self.clear_previews()

        if not self.filepaths:
            self.status_label.config(text="Please select at least one image.")
            return

        if not self.output_dir:
            self.status_label.config(text="Please choose an output folder.")
            return

        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            quality = int(self.quality_var.get())
        except ValueError:
            self.status_label.config(text="Width, height and quality must be integers.")
            return

        if width <= 0 or height <= 0 or not (1 <= quality <= 100):
            self.status_label.config(text="Invalid width/height/quality values.")
            return

        for i, path in enumerate(self.filepaths):
            try:
                img = Image.open(path)
                img = img.convert("RGB")
                resized = img.resize((width, height), Image.LANCZOS)

                # Show preview thumbnail
                thumb = resized.copy()
                thumb.thumbnail((200, 200))
                tk_img = ImageTk.PhotoImage(thumb)
                self.previews.append(tk_img)

                lbl = Label(
                    self.preview_frame,
                    image=tk_img,
                    text=os.path.basename(path),
                    compound="top",
                )
                lbl.grid(row=0, column=i, padx=5, pady=5)

                # Save into selected output folder with _resized suffix
                base_name, ext = os.path.splitext(os.path.basename(path))
                out_path = os.path.join(self.output_dir, f"{base_name}_resized{ext}")
                save_kwargs = {"quality": quality} if ext.lower() in {".jpg", ".jpeg"} else {}
                resized.save(out_path, **save_kwargs)
            except Exception as exc:  # pragma: no cover - simple status text
                self.status_label.config(
                    text=f"Error processing {os.path.basename(path)}: {exc}"
                )
                continue

        if not self.status_label.cget("text"):
            self.status_label.config(
                text="Resizing complete. Files saved next to originals."
            )


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ZenvaResizerGUI(root)
    root.mainloop()

