import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import subprocess
import threading
import os
import requests
import zipfile
import tempfile
from decimal import Decimal, getcontext

class VideoCombinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LM - Video Combiner")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        self.root.configure(bg='#282c34')
        self.video_files = []
        self.banner_files = []

        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 12), padding=10, background='#61afef', foreground='#000')
        style.configure("TLabel", font=("Helvetica", 14, "bold"), background='#282c34', foreground='#61afef')
        style.configure("TFrame", background='#282c34')

        self.frame = ttk.Frame(root, padding="20 20 20 20", style='TFrame')
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.label = ttk.Label(self.frame, text="LM - Video Combiner", style='TLabel')
        self.label.pack(pady=20)

        self.select_video_button = ttk.Button(self.frame, text="Selecione os vídeos", command=self.select_videos, style='TButton')
        self.select_video_button.pack(fill=tk.X, pady=10)

        self.select_banner_button = ttk.Button(self.frame, text="Selecione os banners", command=self.select_banners, style='TButton')
        self.select_banner_button.pack(fill=tk.X, pady=10)

        lists_frame = ttk.Frame(self.frame, style='TFrame')
        lists_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.listbox_videos = tk.Listbox(lists_frame, font=("Helvetica", 12), selectmode=tk.SINGLE)
        self.listbox_videos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.listbox_banners = tk.Listbox(lists_frame, font=("Helvetica", 12), selectmode=tk.SINGLE)
        self.listbox_banners.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        button_frame = ttk.Frame(self.frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=10)

        self.up_button = ttk.Button(button_frame, text="↑ Mover para Cima", command=lambda: self.move_item("up"), style='TButton')
        self.up_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.down_button = ttk.Button(button_frame, text="↓ Mover para Baixo", command=lambda: self.move_item("down"), style='TButton')
        self.down_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.delete_button = ttk.Button(button_frame, text="Deletar Selecionado", command=self.delete_selected, style='TButton')
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.create_videos_button = ttk.Button(button_frame, text="Criar Vídeos", command=self.create_videos, style='TButton')
        self.create_videos_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.combine_button = ttk.Button(button_frame, text="Agrupar vídeos", command=self.combine_videos, style='TButton')
        self.combine_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.progress = ttk.Progressbar(self.frame, orient=tk.HORIZONTAL, length=400, mode='indeterminate')
        self.progress.pack(side=tk.BOTTOM, pady=20)
        self.progress.pack_forget()

        self.ffmpeg_path = os.path.join(tempfile.gettempdir(), "ffmpeg", "ffmpeg.exe")
        self.ffprobe_path = os.path.join(tempfile.gettempdir(), "ffmpeg", "ffprobe.exe")
        self.check_ffmpeg()

    def select_videos(self):
        files = filedialog.askopenfilenames(filetypes=[("MP4 files", "*.mp4")])
        if files:
            self.video_files.extend(files)
            self.update_listbox_videos()
            messagebox.showinfo("Vídeos selecionados", f"Foram selecionados {len(files)} vídeos")

    def select_banners(self):
        files = filedialog.askopenfilenames(filetypes=[("PNG files", "*.png")])
        if files:
            self.banner_files.extend(files)
            self.update_listbox_banners()
            messagebox.showinfo("Banners selecionados", f"Foram selecionados {len(files)} banners")

    def update_listbox_videos(self):
        self.listbox_videos.delete(0, tk.END)
        for i, file in enumerate(self.video_files):
            filename = os.path.basename(file)
            name = os.path.splitext(filename)[0]
            self.listbox_videos.insert(tk.END, f"{i+1}. {name}")

    def update_listbox_banners(self):
        self.listbox_banners.delete(0, tk.END)
        for i, file in enumerate(self.banner_files):
            filename = os.path.basename(file)
            name = os.path.splitext(filename)[0]
            self.listbox_banners.insert(tk.END, f"{i+1}. {name}")

    def move_item(self, direction):
        if self.listbox_videos.curselection():
            selected = self.listbox_videos.curselection()
            index = selected[0]
            if direction == "up" and index > 0:
                self.video_files[index], self.video_files[index - 1] = self.video_files[index - 1], self.video_files[index]
                self.update_listbox_videos()
                self.listbox_videos.selection_set(index - 1)
            elif direction == "down" and index < len(self.video_files) - 1:
                self.video_files[index], self.video_files[index + 1] = self.video_files[index + 1], self.video_files[index]
                self.update_listbox_videos()
                self.listbox_videos.selection_set(index + 1)
        elif self.listbox_banners.curselection():
            selected = self.listbox_banners.curselection()
            index = selected[0]
            if direction == "up" and index > 0:
                self.banner_files[index], self.banner_files[index - 1] = self.banner_files[index - 1], self.banner_files[index]
                self.update_listbox_banners()
                self.listbox_banners.selection_set(index - 1)
            elif direction == "down" and index < len(self.banner_files) - 1:
                self.banner_files[index], self.banner_files[index + 1] = self.banner_files[index + 1], self.banner_files[index]
                self.update_listbox_banners()
                self.listbox_banners.selection_set(index + 1)

    def delete_selected(self):
        if self.listbox_videos.curselection():
            selected = self.listbox_videos.curselection()
            index = selected[0]
            del self.video_files[index]
            self.update_listbox_videos()
        elif self.listbox_banners.curselection():
            selected = self.listbox_banners.curselection()
            index = selected[0]
            del self.banner_files[index]
            self.update_listbox_banners()

    def create_videos(self):
        if not self.video_files or not self.banner_files:
            messagebox.showwarning("Faltam vídeos ou banners", "Você deve selecionar vídeos e banners para criar os vídeos.")
            return

        if len(self.banner_files) != len(self.video_files):
            messagebox.showwarning("Número de banners incorreto", "O número de banners deve ser igual ao número de vídeos selecionados!")
            return

        output_folder = filedialog.askdirectory()
        if not output_folder:
            messagebox.showwarning("Pasta de saída não selecionada", "Você deve selecionar uma pasta de saída para salvar os vídeos.")
            return

        self.progress.pack(side=tk.BOTTOM, pady=20)
        self.progress.start()

        threading.Thread(target=self.create_videos_with_banners, args=(output_folder,)).start()

    def create_videos_with_banners(self, output_folder):
        try:
            for i, (video, banner) in enumerate(zip(self.video_files, self.banner_files)):
                output_file = os.path.join(output_folder, f"banner_video_{i}.mov")
                self.create_mov_with_banner(video, banner, output_file)
            messagebox.showinfo("Sucesso", "Vídeos MOV com banners foram criados com sucesso.")
        except Exception as e:
            self.on_error(e)
        finally:
            self.progress.stop()
            self.progress.pack_forget()

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
                '-r', '59.94',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-strict', 'experimental',
                output_file
            ]

            subprocess.run(command, check=True)
            self.on_success(output_file)
        except Exception as e:
            self.on_error(e)

    def create_mov_with_banner(self, video_file, banner_file, output_file):
        try:
            getcontext().prec = 10;
            result = subprocess.run([self.ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            duration = Decimal(result.stdout.decode().strip())


            command = [
                self.ffmpeg_path,
                '-loop', '1',
                '-i', banner_file,
                '-t', str(duration),
                '-r', '59.94',
                '-c:v', 'prores_ks',
                '-c:a', 'aac',
                '-shortest',
                output_file
            ]
            subprocess.run(command, check=True)
        except Exception as e:
            raise RuntimeError(f"Erro ao criar vídeo MOV com banner: {e}")

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
            subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
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
        ffprobe_exe = os.path.join(ffmpeg_dir, "ffprobe.exe")

        return ffmpeg_exe, ffprobe_exe

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
            self.ffprobe_path = 'ffprobe'

    def download_ffmpeg_thread(self):
        try:
            self.ffmpeg_path, self.ffprobe_path = self.download_ffmpeg()
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
