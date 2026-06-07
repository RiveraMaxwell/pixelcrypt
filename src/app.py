"""
Image Pixel Encryption Tool - GUI Application
A tool for encrypting and decrypting images using XOR-based pixel manipulation.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import threading

from encryption import (
    process_image,
    evaluate_key_strength,
    compute_image_hash,
)

# Try to enable drag & drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

SUPPORTED_FORMATS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PixelCrypt - Image Encryption Tool")
        self.root.geometry("750x650")
        self.root.minsize(600, 500)

        # State
        self.input_path = tk.StringVar()
        self.key = tk.StringVar()
        self.show_key = False
        self.realtime = tk.BooleanVar()
        self.original_img = None
        self.result_img = None
        self.view_mode = tk.StringVar(value="result")  # "original", "result", "side_by_side"
        self.last_output_path = None

        # Apply dark theme colors
        self.bg = "#1e1e2e"
        self.fg = "#cdd6f4"
        self.accent = "#89b4fa"
        self.surface = "#313244"
        self.red = "#f38ba8"
        self.green = "#a6e3a1"
        self.yellow = "#f9e2af"

        self.root.configure(bg=self.bg)

        # Configure ttk style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background=self.bg)
        self.style.configure("TLabel", background=self.bg, foreground=self.fg)
        self.style.configure("TButton", background=self.surface, foreground=self.fg)
        self.style.configure("TCheckbutton", background=self.bg, foreground=self.fg)
        self.style.configure(
            "Horizontal.TProgressbar",
            background=self.accent,
            troughcolor=self.surface,
        )
        self.style.configure("TLabelframe", background=self.bg, foreground=self.fg)
        self.style.configure("TLabelframe.Label", background=self.bg, foreground=self.fg)

        self.key.trace_add("write", self._on_key_change)

        self._build_ui()

    def _build_ui(self):
        # --- File Selection ---
        file_frame = ttk.Frame(self.root)
        file_frame.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Button(file_frame, text="Browse Image", command=self.browse_input).pack(side="left")

        self.file_label = ttk.Label(file_frame, text="No file selected", foreground="#6c7086")
        self.file_label.pack(side="left", padx=10)

        self.info_label = ttk.Label(file_frame, text="", foreground="#6c7086")
        self.info_label.pack(side="right")

        # --- Key Entry ---
        key_frame = ttk.Frame(self.root)
        key_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(key_frame, text="Key:").pack(side="left")

        self.key_entry = tk.Entry(
            key_frame,
            textvariable=self.key,
            show="*",
            width=30,
            bg=self.surface,
            fg=self.fg,
            insertbackground=self.fg,
            relief="flat",
            font=("Consolas", 10),
        )
        self.key_entry.pack(side="left", padx=5)

        self.toggle_btn = ttk.Button(key_frame, text="👁", width=3, command=self.toggle_key)
        self.toggle_btn.pack(side="left")

        # Key strength indicator
        self.strength_label = ttk.Label(key_frame, text="", width=12)
        self.strength_label.pack(side="left", padx=10)

        self.strength_bar = ttk.Progressbar(
            key_frame, orient="horizontal", length=100, mode="determinate"
        )
        self.strength_bar.pack(side="left")

        # --- Options ---
        options_frame = ttk.Frame(self.root)
        options_frame.pack(fill="x", padx=10, pady=5)

        ttk.Checkbutton(
            options_frame, text="Realtime Preview", variable=self.realtime
        ).pack(side="left")

        # View mode
        ttk.Label(options_frame, text="  View:").pack(side="left", padx=(20, 5))
        views = [("Result", "result"), ("Original", "original"), ("Side by Side", "side_by_side")]
        for text, value in views:
            ttk.Radiobutton(
                options_frame, text=text, variable=self.view_mode, value=value,
                command=self._refresh_preview
            ).pack(side="left", padx=2)

        # --- Action Buttons ---
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill="x", padx=10, pady=5)

        self.encrypt_btn = ttk.Button(action_frame, text="🔒 Encrypt", command=self.encrypt)
        self.encrypt_btn.pack(side="left", padx=5)

        self.decrypt_btn = ttk.Button(action_frame, text="🔓 Decrypt", command=self.decrypt)
        self.decrypt_btn.pack(side="left", padx=5)

        self.batch_btn = ttk.Button(action_frame, text="📁 Batch Process", command=self.batch_process)
        self.batch_btn.pack(side="left", padx=5)

        self.verify_btn = ttk.Button(
            action_frame, text="✓ Verify", command=self.verify_decryption, state="disabled"
        )
        self.verify_btn.pack(side="left", padx=5)

        self.copy_btn = ttk.Button(
            action_frame, text="📋 Copy Path", command=self.copy_output_path, state="disabled"
        )
        self.copy_btn.pack(side="left", padx=5)

        # --- Progress ---
        self.progress = ttk.Progressbar(
            self.root, orient="horizontal", mode="determinate", style="Horizontal.TProgressbar"
        )
        self.progress.pack(fill="x", padx=10, pady=5)

        # --- Preview Canvas ---
        self.canvas = tk.Label(
            self.root,
            text="Drag & Drop image here\nor use Browse",
            bg=self.surface,
            fg="#6c7086",
            font=("Segoe UI", 12),
            relief="flat",
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Enable drag & drop
        if DND_AVAILABLE:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self.on_drop)

    def _on_key_change(self, *_):
        """Update key strength indicator when key changes."""
        key = self.key.get()
        score, label = evaluate_key_strength(key)
        self.strength_bar["value"] = score

        if score >= 80:
            color = self.green
        elif score >= 60:
            color = self.accent
        elif score >= 40:
            color = self.yellow
        else:
            color = self.red

        self.strength_label.config(text=label, foreground=color)

    def toggle_key(self):
        self.show_key = not self.show_key
        self.key_entry.config(show="" if self.show_key else "*")

    def browse_input(self):
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("BMP", "*.bmp"),
            ("TIFF", "*.tiff *.tif"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.load_file(path)

    def on_drop(self, event):
        path = event.data.strip("{}")
        self.load_file(path)

    def load_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_FORMATS:
            messagebox.showwarning(
                "Unsupported Format",
                f"Supported formats: {', '.join(SUPPORTED_FORMATS)}\n\n"
                "Note: For lossless encrypt/decrypt, use PNG.",
            )
            return

        if ext in (".jpg", ".jpeg"):
            messagebox.showinfo(
                "Format Notice",
                "JPEG is lossy. The encrypted output will be saved as PNG\n"
                "to ensure lossless decryption.",
            )

        self.input_path.set(path)
        self.original_img = Image.open(path).convert("RGB")
        self.result_img = None

        # Update file info
        filename = os.path.basename(path)
        self.file_label.config(text=filename, foreground=self.fg)

        w, h = self.original_img.size
        size_kb = os.path.getsize(path) / 1024
        self.info_label.config(text=f"{w}×{h} | {size_kb:.0f} KB")

        self._show_image(self.original_img)
        self.verify_btn.config(state="disabled")
        self.copy_btn.config(state="disabled")

    def _get_preview_size(self):
        """Calculate max preview size based on canvas."""
        self.root.update_idletasks()
        cw = self.canvas.winfo_width() - 20
        ch = self.canvas.winfo_height() - 20
        return max(200, cw), max(200, ch)

    def _show_image(self, img):
        """Display a single image in the canvas."""
        max_w, max_h = self._get_preview_size()
        display = img.copy()
        display.thumbnail((max_w, max_h))
        self.tk_img = ImageTk.PhotoImage(display)
        self.canvas.config(image=self.tk_img, text="")

    def _show_side_by_side(self):
        """Show original and result side by side."""
        if not self.original_img or not self.result_img:
            return

        max_w, max_h = self._get_preview_size()
        half_w = max_w // 2 - 5

        left = self.original_img.copy()
        left.thumbnail((half_w, max_h))

        right = self.result_img.copy()
        right.thumbnail((half_w, max_h))

        # Create combined image
        combined_w = left.width + right.width + 10
        combined_h = max(left.height, right.height)
        combined = Image.new("RGB", (combined_w, combined_h), color=(49, 50, 68))
        combined.paste(left, (0, 0))
        combined.paste(right, (left.width + 10, 0))

        self.tk_img = ImageTk.PhotoImage(combined)
        self.canvas.config(image=self.tk_img, text="")

    def _refresh_preview(self):
        """Refresh preview based on current view mode."""
        mode = self.view_mode.get()
        if mode == "original" and self.original_img:
            self._show_image(self.original_img)
        elif mode == "result" and self.result_img:
            self._show_image(self.result_img)
        elif mode == "side_by_side":
            self._show_side_by_side()

    def update_preview(self, img):
        """Called during realtime processing."""
        self.result_img = img
        self.root.after(0, lambda: self._show_image(img))

    def update_progress(self, value):
        self.progress["value"] = value
        self.root.update_idletasks()

    def build_output_path(self, input_path, mode):
        directory, filename = os.path.split(input_path)
        name, ext = os.path.splitext(filename)
        # Always save as PNG for lossless output
        return os.path.join(directory, f"{name}_{mode}.png")

    def _set_buttons_state(self, state):
        """Enable/disable action buttons during processing."""
        self.encrypt_btn.config(state=state)
        self.decrypt_btn.config(state=state)
        self.batch_btn.config(state=state)

    def encrypt(self):
        self._run("encrypt")

    def decrypt(self):
        self._run("decrypt")

    def _run(self, mode):
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an image file.")
            return
        if not self.key.get():
            messagebox.showerror("Error", "Please enter an encryption key.")
            return

        self._set_buttons_state("disabled")
        self.progress["value"] = 0

        input_path = self.input_path.get()
        output_path = self.build_output_path(input_path, mode)

        thread = threading.Thread(
            target=self._process_thread, args=(input_path, output_path, mode), daemon=True
        )
        thread.start()

    def _process_thread(self, input_path, output_path, mode):
        try:
            img = Image.open(input_path).convert("RGB")

            result = process_image(
                img=img,
                key=self.key.get(),
                progress_callback=lambda v: self.root.after(0, self.update_progress, v),
                preview_callback=self.update_preview if self.realtime.get() else None,
                realtime=self.realtime.get(),
            )

            result.save(output_path)
            self.result_img = result
            self.last_output_path = output_path

            self.root.after(0, self._on_process_complete, output_path, mode)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, lambda: self._set_buttons_state("normal"))

    def _on_process_complete(self, output_path, mode):
        self._set_buttons_state("normal")
        self.verify_btn.config(state="normal")
        self.copy_btn.config(state="normal")
        self._refresh_preview()
        messagebox.showinfo("Success", f"{'Encrypted' if mode == 'encrypt' else 'Decrypted'} image saved to:\n{output_path}")

    def batch_process(self):
        """Process multiple files with the same key."""
        if not self.key.get():
            messagebox.showerror("Error", "Please enter an encryption key first.")
            return

        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
            ("All files", "*.*"),
        ]
        paths = filedialog.askopenfilenames(filetypes=filetypes)
        if not paths:
            return

        # Ask encrypt or decrypt
        mode = messagebox.askquestion(
            "Batch Mode", "Click 'Yes' to Encrypt or 'No' to Decrypt"
        )
        mode = "encrypt" if mode == "yes" else "decrypt"

        self._set_buttons_state("disabled")

        thread = threading.Thread(
            target=self._batch_thread, args=(paths, mode), daemon=True
        )
        thread.start()

    def _batch_thread(self, paths, mode):
        try:
            total = len(paths)
            for i, path in enumerate(paths):
                ext = os.path.splitext(path)[1].lower()
                if ext not in SUPPORTED_FORMATS:
                    continue

                img = Image.open(path).convert("RGB")
                output_path = self.build_output_path(path, mode)

                result = process_image(img=img, key=self.key.get())
                result.save(output_path)

                progress = ((i + 1) / total) * 100
                self.root.after(0, self.update_progress, progress)

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Batch Complete", f"Processed {total} images ({mode})."
                ),
            )
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, lambda: self._set_buttons_state("normal"))

    def verify_decryption(self):
        """Verify that decrypting an encrypted image returns the original."""
        if not self.original_img or not self.result_img:
            messagebox.showinfo("Verify", "Encrypt or decrypt an image first.")
            return

        original_hash = compute_image_hash(self.original_img)

        # Re-process the result to see if we get back the original
        verification = process_image(img=self.result_img, key=self.key.get())
        verify_hash = compute_image_hash(verification)

        if original_hash == verify_hash:
            messagebox.showinfo(
                "Verification Passed ✓",
                "Round-trip verification successful.\n"
                "Decrypting the output with the same key\n"
                "produces the original image.",
            )
        else:
            messagebox.showwarning(
                "Verification Failed ✗",
                "Round-trip verification failed.\n"
                "The decrypted output does not match the original.\n"
                "This may indicate the wrong key was used.",
            )

    def copy_output_path(self):
        """Copy the last output file path to clipboard."""
        if self.last_output_path:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_output_path)
            messagebox.showinfo("Copied", "Output path copied to clipboard.")


def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
