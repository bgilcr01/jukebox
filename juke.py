import os
import glob
import tkinter as tk
import customtkinter as ctk
import pygame

# 1. INITIALIZE AUDIO ENGINE
pygame.mixer.init()

class JukeboxApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Pressing the Escape key will safely close the app
        self.bind("<Escape>", lambda event: self.destroy())
        
        # get monitor dimensions ; needed for raspberry pi desktop; may have to adjust for touchscreen 

        # 1. Remove the standard title bar, close buttons, and window borders
        self.overrideredirect(True)
        
        # 2. Query the monitor's exact hardware dimensions
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # 3. Force the window to fit the screen exactly at top-left coordinates (0,0)
        self.geometry(f"{screen_w}x{screen_h}+0+0")
        
        # TRY ENABLE THIS ON TOUCHSCREEN LATER
        # self.attributes('-fullscreen', True)    
        # self.geometry("800x480")
        
        # Configure window for a standard 7" Pi Touchscreen (800x480)
        self.title("Kids Jukebox")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # State tracking
        self.music_dir = "./music"  # Change to your MP3 folder path
        self.playlist = self.load_mp3s()
        self.current_index = 0
        self.is_playing = False
        
        # Create UI Grid Layout (Top section scrolls, bottom is fixed controls)
        self.grid_rowconfigure(0, weight=1)  # Song selection zone
        self.grid_rowconfigure(1, weight=0)  # Playback bar zone
        self.grid_columnconfigure(0, weight=1)
        
        self.build_song_picker()
        self.build_controls()
        
        
        
    def load_mp3s(self):
        """Scans the music directory for local MP3 files."""
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir)
        # Returns a list of absolute file paths
        return sorted(glob.glob(os.path.join(self.music_dir, "*.mp3")))

    def build_song_picker(self):
        """Creates a scrollable area filled with giant song selection buttons."""
        self.scroll_frame = ctk.CTkScrollableFrame(self, orientation="vertical")
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure the scrollable frame to have 2 wide columns for massive touch targets
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=1)
        
        if not self.playlist:
            no_songs_label = ctk.CTkLabel(
                self.scroll_frame, 
                text="Drop some MP3 files into the './music' folder!", 
                font=("Arial", 20)
            )
            no_songs_label.grid(row=0, column=0, columnspan=2, pady=50)
            return

        for idx, track_path in enumerate(self.playlist):
            song_title = os.path.basename(track_path).replace(".mp3", "")
            
            # Massive touch target button
            btn = ctk.CTkButton(
                self.scroll_frame,
                text=song_title,
                font=("Arial", 18, "bold"),
                height=80,  # Generous vertical padding for touchaccuracy
                command=lambda i=idx: self.play_song(i)
            )
            
            # Arrange in a 2-column grid row by row
            row = idx // 2
            col = idx % 2
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

    def build_controls(self):
        """Creates the giant navigation bar at the bottom of the screen."""
        self.controls_frame = ctk.CTkFrame(self, height=110, corner_radius=0)
        self.controls_frame.grid(row=1, column=0, sticky="ew")
        
        # 4 columns for Back, Play/Pause, Next, and Status text
        self.controls_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.controls_frame.grid_columnconfigure(3, weight=2)
        
        # Giant Back Button
        self.btn_back = ctk.CTkButton(
            self.controls_frame, text="⏮ BACK", font=("Arial", 22, "bold"),
            height=80, fg_color="#E67E22", hover_color="#D35400", command=self.prev_song
        )
        self.btn_back.grid(row=0, column=0, padx=10, pady=15, sticky="ew")
        
        # Giant Play/Pause Button
        self.btn_toggle = ctk.CTkButton(
            self.controls_frame, text="▶ PLAY", font=("Arial", 22, "bold"),
            height=80, fg_color="#2ECC71", hover_color="#27AE60", command=self.toggle_play
        )
        self.btn_toggle.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        
        # Giant Next Button
        self.btn_next = ctk.CTkButton(
            self.controls_frame, text="NEXT ⏭", font=("Arial", 22, "bold"),
            height=80, fg_color="#E67E22", hover_color="#D35400", command=self.next_song
        )
        self.btn_next.grid(row=0, column=2, padx=10, pady=15, sticky="ew")
        
        # Status Label showing what's currently playing
        self.lbl_status = ctk.CTkLabel(
            self.controls_frame, text="Jukebox Ready", font=("Arial", 16, "italic"),
            anchor="w", justify="left"
        )
        self.lbl_status.grid(row=0, column=3, padx=20, pady=15, sticky="ew")

    # 3. AUDIO CONTROL LOGIC
    def play_song(self, index):
        if not self.playlist: return
        self.current_index = index
        track = self.playlist[self.current_index]
        
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play()
            self.is_playing = True
            self.btn_toggle.configure(text="⏸ PAUSE", fg_color="#E74C3C", hover_color="#C0392B")
            
            # Trim the file path to show just the song name to the kids
            song_name = os.path.basename(track).replace(".mp3", "")
            self.lbl_status.configure(text=f"Playing:\n{song_name}")
        except Exception as e:
            self.lbl_status.configure(text="Error playing file")

    def toggle_play(self):
        if not self.playlist: return
        
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.btn_toggle.configure(text="▶ PLAY", fg_color="#2ECC71", hover_color="#27AE60")
        else:
            # If music was paused, unpause it. If nothing was playing yet, start track 0.
            if pygame.mixer.music.get_pos() > 0:
                pygame.mixer.music.unpause()
                self.is_playing = True
                self.btn_toggle.configure(text="⏸ PAUSE", fg_color="#E74C3C", hover_color="#C0392B")
            else:
                self.play_song(self.current_index)

    def next_song(self):
        if not self.playlist: return
        next_idx = (self.current_index + 1) % len(self.playlist)
        self.play_song(next_idx)

    def prev_song(self):
        if not self.playlist: return
        prev_idx = (self.current_index - 1) % len(self.playlist)
        self.play_song(prev_idx)

if __name__ == "__main__":
    app = JukeboxApp()
    app.mainloop()