import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import requests
from io import BytesIO
from yt_dlp import YoutubeDL

# --- Globals ---
save_path = os.path.join(os.getcwd(), "Downloads")  # default folder
video_info = {}

def update_status(msg):
    status_var.set(msg)
    print(msg)

def download_hook(d):
    if d['status'] == 'finished':
        update_status("✅ Download selesai!")

def get_ydl_opts(url, mode):
    global save_path
    os.makedirs(save_path, exist_ok=True)

    if mode == 'MP3':
        return {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
            'quiet': True,
            'progress_hooks': [download_hook],
        }
    else:
        return {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'progress_hooks': [download_hook],
        }

def download_video():
    url = url_entry.get().strip()
    mode = mode_var.get()

    if not url.startswith("http"):
        update_status("❌ URL tidak valid!")
        return

    try:
        update_status("⬇️ Mengunduh...")
        ydl_opts = get_ydl_opts(url, mode)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        update_status(f"❌ Gagal download: {str(e)}")

def start_download():
    url = url_entry.get()
    if not url:
        messagebox.showwarning("Peringatan", "Masukkan URL terlebih dahulu!")
        return
    threading.Thread(target=download_video, daemon=True).start()

def fetch_video_info():
    url = url_entry.get().strip()
    if not url.startswith("http"):
        messagebox.showerror("Error", "URL tidak valid!")
        return

    def _fetch():
        global video_info
        try:
            update_status("🔎 Mengambil info video...")
            ydl_opts = {'quiet': True, 'skip_download': True}
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_info = info

                title = info.get('title', 'Unknown Title')
                update_status(f"Judul: {title}")

                # Tampilkan thumbnail
                thumb_url = info.get('thumbnail')
                if thumb_url:
                    try:
                        resp = requests.get(thumb_url)
                        img_data = resp.content
                        img = Image.open(BytesIO(img_data)).resize((320, 180))
                        photo = ImageTk.PhotoImage(img)
                        thumbnail_label.config(image=photo)
                        thumbnail_label.image = photo
                    except Exception as e:
                        update_status(f"⚠️ Gagal memuat thumbnail: {e}")
                else:
                    thumbnail_label.config(image='')
        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengambil info: {str(e)}")
            update_status("❌ Gagal mengambil info")

    threading.Thread(target=_fetch, daemon=True).start()

def choose_folder():
    global save_path
    folder = filedialog.askdirectory(initialdir=save_path)
    if folder:
        save_path = folder
        folder_label.config(text=f"Folder Simpan: {save_path}")

# --- GUI Setup ---
root = tk.Tk()
root.title("FDownloader MP4 & MP3")
root.geometry("460x400")
root.resizable(False, False)

tk.Label(root, text="Masukkan URL Video:").pack(pady=(10, 0))
url_entry = tk.Entry(root, width=60)
url_entry.pack(pady=5)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

load_info_btn = tk.Button(btn_frame, text="Load Info", command=fetch_video_info)
load_info_btn.grid(row=0, column=0, padx=5)

download_btn = tk.Button(btn_frame, text="Download", command=start_download, fg="black")
download_btn.grid(row=0, column=1, padx=5)

choose_folder_btn = tk.Button(btn_frame, text="Pilih Folder", command=choose_folder)
choose_folder_btn.grid(row=0, column=2, padx=5)

mode_var = ttk.Combobox(root, values=["MP4", "MP3"], state="readonly", width=10)
mode_var.set("MP4")
mode_var.pack(pady=5)

thumbnail_label = tk.Label(root)
thumbnail_label.pack(pady=10)

folder_label = tk.Label(root, text=f"Folder Simpan: {save_path}")
folder_label.pack()

status_var = tk.StringVar()
tk.Label(root, textvariable=status_var, fg="blue").pack(pady=5)

root.mainloop()