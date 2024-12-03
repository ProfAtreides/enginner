import tkinter as tk
import numpy as np
import threading
import time

from tkinter import filedialog, ttk
from ffpyplayer.player import MediaPlayer
from PIL import Image, ImageTk
from tools import translate_speech, create_histogram, eng_to_pol, extract_audio_from_mp4


class VideoPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("")
        self.root.state("zoomed")  # Start maximized
        self.root.bind("<Configure>", self.resize_window)

        # Main container frame
        self.main_frame = tk.Frame(self.root, bg="black")
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # Video frame for the canvas
        self.video_frame = tk.Frame(self.main_frame, bg="black")
        self.video_frame.pack(expand=True, fill=tk.BOTH)

        # Video canvas
        self.canvas = tk.Canvas(self.video_frame, bg="black", highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Downpanel frame for controls
        self.downpanel = tk.Frame(self.root, bg="gray")
        self.downpanel.pack(fill=tk.X, side=tk.BOTTOM)

        # Seek Slider
        self.seek_slider = ttk.Scale(self.downpanel, from_=0, to=100, orient="horizontal")
        self.seek_slider.pack(fill=tk.X, padx=10, pady=5)
        self.seek_slider.bind("<Button-1>", self.slider_clicked)  # Pause on click
        self.seek_slider.bind("<ButtonRelease-1>", self.slider_released)  # Seek and resume on release
        self.is_user_seeking = False

        # Controls Frame
        controls = tk.Frame(self.downpanel, bg="gray")
        controls.pack(fill=tk.X, pady=5)

        self.open_button = ttk.Button(controls, text="Open Video", command=self.open_video)
        self.open_button.pack(side=tk.LEFT, padx=5)

        self.play_button = ttk.Button(controls, text="Play", command=self.play_video)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = ttk.Button(controls, text="Pause", command=self.pause_video)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(controls, text="Stop", command=self.stop_video)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Video player attributes
        self.player = None
        self.is_playing = False
        self.thread = None
        self.stop_flag = False
        self.frame_delay = 0.01
        self.duration = 0
        self.video_width = 1920
        self.video_height = 1080
        self.resized_width = 1920
        self.resized_height = 1080

        self.subtitle_text_id = None
        self.subtitles = [
            {"start": 0, "end": 100000000000000, "text": "If you're seeing this there has been an error :(", "color": "white"}
        ]
        self.translate_subtitles = False
        self.number_of_speakers = -1
        self.histogram = None
        self.colors = [
            {"start": 0, "end": 100000000000000, "color": "black"}
        ]

    def open_video(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Video Files", "*.mp4;*.avi;*.mov;*.mkv"), ("All Files", "*.*")]
        )
        if file_path:
            self.stop_video()
            self.video_path = file_path
            self.load_metadata(file_path)
            self.seek_slider.config(to=self.duration)
            self.open_settings_dialog()

    def open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("300x200")
        dialog.grab_set()

        ttk.Label(dialog, text="Number of Speakers:").pack(pady=10)
        speakers_var = tk.StringVar(value="")
        speakers_entry = ttk.Entry(dialog, textvariable=speakers_var)
        speakers_entry.pack()

        ttk.Label(dialog, text="Translate to Polish:").pack(pady=10)
        translation_var = tk.StringVar(value="")
        translation_combobox = ttk.Combobox(dialog, textvariable=translation_var, values=["Yes", "No"], state="readonly")
        translation_combobox.pack()

        ttk.Button(
            dialog,
            text="Apply",
            command=lambda: self.retrieve_settings(dialog, speakers_var, translation_var)
        ).pack(pady=20)

    def retrieve_settings(self, dialog, speakers_var, translation_var):
        audio = extract_audio_from_mp4(self.video_path)

        self.number_of_speakers = int(speakers_var.get())
        self.translate_subtitles = translation_var.get() == "Yes"

        self.subtitles = translate_speech(audio)
        self.colors = create_histogram(self.video_path, self.number_of_speakers)

        if self.translate_subtitles:
            print("Use with caution the API costs money")
            self.subtitles = eng_to_pol(self.subtitles)

        dialog.destroy()

    def play_video(self):
        if self.player is None and hasattr(self, "video_path"):
            self.player = MediaPlayer(self.video_path)
            self.is_playing = True
            self.stop_flag = False
            self.thread = threading.Thread(target=self.run_player)
            self.thread.start()
        elif self.player and not self.is_playing:
            self.player.set_pause(False)
            self.is_playing = True

    def pause_video(self):
        if self.player and self.is_playing:
            self.player.set_pause(True)
            self.is_playing = False

    def stop_video(self):
        if self.player:
            self.stop_flag = True
            self.player.close_player()
            self.player = None
            self.is_playing = False
            self.canvas.delete("all")
            self.seek_slider.set(0)

    def video_frame_callback(self):
        while self.player and not self.stop_flag:
            frame, val = self.player.get_frame()
            if frame is not None:
                img, t = frame
                array = np.array(img.to_bytearray()[0]).reshape(img.get_size()[::-1] + (3,))
                image = Image.fromarray(array, "RGB")

                # Adjust aspect ratio and resize image
                aspect_ratio = img.get_size()[0] / img.get_size()[1]
                if self.resized_width / aspect_ratio <= self.resized_height:
                    new_width = self.resized_width
                    new_height = int(self.resized_width / aspect_ratio)
                else:
                    new_height = self.resized_height
                    new_width = int(self.resized_height * aspect_ratio)

                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_image)
                self.canvas.create_image(
                    self.canvas.winfo_width() // 2,
                    self.canvas.winfo_height() // 2,
                    image=photo,
                    anchor=tk.CENTER,
                    tag="video_frame"
                )
                self.canvas.image = photo

                # Update subtitles
                pos = self.player.get_pts()
                self.update_subtitles(pos)

                # Update seek slider position
                if not self.is_user_seeking and pos is not None and pos <= self.duration:
                    self.seek_slider.set(pos)

            time.sleep(self.frame_delay)

    def update_subtitles(self, current_time):
        subtitle_text = ""
        subtitle_color = "white"

        # Find the matching subtitle for the current time
        for subtitle in self.subtitles:
            if subtitle["start"] <= current_time <= subtitle["end"]:
                subtitle_text = subtitle["text"]
                break

        # Find the matching color for the current time
        for color_entry in self.colors:
            if color_entry["start"] <= current_time <= color_entry["end"]:
                subtitle_color = color_entry["color"]
                break

        # Clear the previous subtitle
        if self.subtitle_text_id:
            self.canvas.delete(self.subtitle_text_id)

        # Display the current subtitle
        if subtitle_text:
            self.subtitle_text_id = self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.resized_height - 50,  # Position near the bottom of the video
                text=subtitle_text,
                fill=subtitle_color,
                font=("Helvetica", 16),
                tag="subtitle"
            )

    def run_player(self):
        self.video_frame_callback()

    def load_metadata(self, file_path):
        temp_player = MediaPlayer(file_path)
        while True:
            metadata = temp_player.get_metadata()
            if metadata:
                duration = metadata.get("duration", 0)
                if duration:
                    self.duration = duration
                    fps = metadata.get("video", {}).get("fps", 24)
                    self.frame_delay = 1 / fps if fps > 0 else 0.03
                    break
            time.sleep(0.1)
        temp_player.close_player()

    def slider_clicked(self, event):
        self.is_user_seeking = True
        if self.player and self.is_playing:
            self.player.set_pause(True)

    def slider_released(self, event):
        if self.player:
            target_time = self.seek_slider.get()
            self.player.seek(target_time, relative=False)
            self.player.set_pause(False)
            self.is_user_seeking = False

    def resize_window(self, event):
        # Get the full window size
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        # Get the height of the control panel (downpanel)
        downpanel_height = self.downpanel.winfo_height()

        # Calculate the available height for the video
        available_height = window_height - downpanel_height
        available_width = window_width

        # Maintain the video's aspect ratio (assuming 1920x1080 for the original video)
        aspect_ratio = 1920 / 1080

        # Adjust video size to fit within the available area
        if available_width / aspect_ratio <= available_height:
            self.resized_width = available_width
            self.resized_height = int(available_width / aspect_ratio)
        else:
            self.resized_height = available_height
            self.resized_width = int(available_height * aspect_ratio)

        # Resize the canvas to match the resized video dimensions
        self.canvas.config(width=self.resized_width, height=self.resized_height)

        # Center the video within the window
        self.canvas.place(
            x=(window_width - self.resized_width) // 2,
            y=(available_height - self.resized_height) // 2
        )


# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoPlayerApp(root)
    root.mainloop()
