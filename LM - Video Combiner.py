import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import subprocess
import threading
import os
import requests
import zipfile
import tempfile

class VideoCombinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LM - Video Combiner")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.root.configure(bg='#282c34')
        self.video_files = []

        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 12), padding=10, background='#61afef', foreground='#000')
        style.configure("TLabel", font=("Helvetica", 14, "bold"), background='#282c34', foreground='#61afef')
        style.configure("TFrame", background='#282c34')

        self.frame = ttk.Frame(root, padding="20 20 20 20", style='TFrame')
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.label = ttk.Label(self.frame, text="LM - Video Combiner", style='TLabel')
        self.label.pack(pady=20)

        self.select_button = ttk.Button(self.frame, text="Selecione os vídeos", command=self.select_videos, style='TButton')
        self.select_button.pack(fill=tk.X, pady=10)

        self.listbox = tk.Listbox(self.frame, font=("Helvetica", 12), selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        button_frame = ttk.Frame(self.frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=10)

        self.up_button = ttk.Button(button_frame, text="↑ Mover para Cima", command=self.move_up, style='TButton')
        self.up_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.down_button = ttk.Button(button_frame, text="↓ Mover para Baixo", command=self.move_down, style='TButton')
        self.down_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.combine_button = ttk.Button(button_frame, text="Agrupar vídeos", command=self.combine_videos, style='TButton')
        self.combine_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.progress = ttk.Progressbar(self.frame, orient=tk.HORIZONTAL, length=400, mode='indeterminate')
        self.progress.pack(side=tk.BOTTOM, pady=20)
        self.progress.pack_forget()

        self.ffmpeg_path = os.path.join(tempfile.gettempdir(), "ffmpeg", "ffmpeg.exe")
        self.check_ffmpeg()

    def select_videos(self):
        files = filedialog.askopenfilenames(filetypes=[("MP4 files", "*.mp4")])
        if files:
            self.video_files = list(files)
            self.update_listbox()
            messagebox.showinfo("Vídeos selecionados", f"Foram selecionados {len(self.video_files)} vídeos")

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, file in enumerate(self.video_files):
            filename = os.path.basename(file)
            name = os.path.splitext(filename)[0]
            self.listbox.insert(tk.END, f"{i+1}. {name}")

    def move_up(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        index = selected[0]
        if index > 0:
            self.video_files[index], self.video_files[index-1] = self.video_files[index-1], self.video_files[index]
            self.update_listbox()
            self.listbox.selection_set(index-1)

    def move_down(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        index = selected[0]
        if index < len(self.video_files) - 1:
            self.video_files[index], self.video_files[index+1] = self.video_files[index+1], self.video_files[index]
            self.update_listbox()
            self.listbox.selection_set(index+1)

    def combine_videos(self):
        if not self.video_files:
            messagebox.showwarning("Nenhum vídeo selecionado", "Nenhum vídeo selecionado!")
            return

        output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
        if not output_file:
            return

        self.progress.pack(side=tk.BOTTOM, pady=20)
        self.progress.start()

        threading.Thread(target=self.concatenate_videos, args=(self.video_files, output_file)).start()

    def concatenate_videos(self, video_files, output_file):
        try:
            inputs = []
            filter_complex = ""

            for i, video in enumerate(video_files):
                inputs.extend(['-i', video])
                filter_complex += f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2[v{i}];"
                filter_complex += f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a{i}];"

            filter_complex += "".join([f"[v{i}][a{i}]" for i in range(len(video_files))])
            filter_complex += f"concat=n={len(video_files)}:v=1:a=1[v][a]"

            command = [
                self.ffmpeg_path,
                *inputs,
                '-filter_complex', filter_complex,
                '-map', '[v]',
                '-map', '[a]',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-strict', 'experimental',
                output_file
            ]

            subprocess.run(command, check=True)
            self.on_success(output_file)
        except Exception as e:
            self.on_error(e)

    def on_success(self, output_file):
        self.progress.stop()
        self.progress.pack_forget()
        os.startfile(output_file)

    def on_error(self, error):
        self.progress.stop()
        self.progress.pack_forget()
        messagebox.showerror("Erro", f"Ocorreu um erro: {error}")

    def is_ffmpeg_available(self):
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            return False

    def download_ffmpeg(self):
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        local_zip = os.path.join(tempfile.gettempdir(), "ffmpeg-release-essentials.zip")
        
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192

        with open(local_zip, 'wb') as f:
            for data in response.iter_content(block_size):
                f.write(data)
                downloaded_size = f.tell()
                progress_percent = downloaded_size / total_size * 100
                self.progress.step(progress_percent)
                self.progress.update()

        ffmpeg_extract_dir = os.path.join(tempfile.gettempdir(), "ffmpeg")
        with zipfile.ZipFile(local_zip, 'r') as zip_ref:
            zip_ref.extractall(ffmpeg_extract_dir)

        os.remove(local_zip)

        ffmpeg_dir = os.path.join(ffmpeg_extract_dir, os.listdir(ffmpeg_extract_dir)[0], "bin")
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")

        return ffmpeg_exe

    def check_ffmpeg(self):
        if not self.is_ffmpeg_available():
            if messagebox.askyesno("FFmpeg não encontrado", "FFmpeg não foi encontrado. Deseja baixá-lo e instalá-lo agora?"):
                try:
                    self.progress.pack(side=tk.BOTTOM, pady=20)
                    self.progress.start()
                    threading.Thread(target=self.download_ffmpeg_thread).start()
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro ao baixar e instalar o FFmpeg: {e}")
        else:
            self.ffmpeg_path = 'ffmpeg'

    def download_ffmpeg_thread(self):
        try:
            self.ffmpeg_path = self.download_ffmpeg()
            self.progress.stop()
            self.progress.pack_forget()
            messagebox.showinfo("Sucesso", "FFmpeg baixado e instalado com sucesso.")
        except Exception as e:
            self.progress.stop()
            self.progress.pack_forget()
            messagebox.showerror("Erro", f"Ocorreu um erro ao baixar e instalar o FFmpeg: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCombinerApp(root)
    root.mainloop()
