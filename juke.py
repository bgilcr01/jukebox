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
              
        # Configure window size & force borderless fullscreen for Pi displays
        self.title("Kids Jukebox")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.overrideredirect(True)
                
        # 3. Force Tkinter to calculate full screen size natively
        # self.attributes('-fullscreen', True)
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")
        
        # Safe exit button for development testing (Press ESC to close app)
        self.bind("<Escape>", lambda event: self.destroy())
        
        # Directory Management State
        self.base_dir = os.path.abspath("./music")
        self.current_dir = self.base_dir
        
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            
        # Playback Management State
        self.playlist = []
        self.current_index = 0
        self.is_playing = False
        
        # Layout Hierarchy
        self.grid_rowconfigure(0, weight=1)  # Dynamic grid selection area
        self.grid_rowconfigure(1, weight=0)  # Persistent bottom audio controls
        self.grid_columnconfigure(0, weight=1)
        
        # Build out the layout elements
        self.build_song_picker()
        self.build_controls()
        
        # Initial scan of the root folder
        self.refresh_grid()

    def scan_directory(self):
        """Scans the current folder path for subdirectories and MP3 files."""
        # Find folders first
        items = os.listdir(self.current_dir)
        folders = []
        files = []
        
        for item in sorted(items):
            full_path = os.path.join(self.current_dir, item)
            if os.path.isdir(full_path):
                folders.append(full_path)
            elif item.lower().endswith(".mp3"):
                files.append(full_path)
                
        return folders, files

    def refresh_grid(self):
        """Clears out the scrolling panel and rebuilds the visual interface layout."""
        # Wipe clean any existing elements inside the frame scroll architecture
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        folders, files = self.scan_directory()
        # The playlist used for Next/Back buttons updates to only include current folder's files
        self.playlist = files 
        
        current_row = 0
        
        # 1. Provide an escape route button if we are inside a subfolder
        if self.current_dir != self.base_dir:
            btn_up = ctk.CTkButton(
                self.scroll_frame,
                text="⬅ BACK TO MAIN MENU",
                font=("Arial", 20, "bold"),
                height=90,
                fg_color="#8E44AD",
                hover_color="#732890",
                command=self.go_to_parent_dir
            )
            btn_up.grid(row=current_row, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
            current_row += 1

        # 2. Render Subfolders (styled distinctly so kids know they open up paths)
        for idx, folder_path in enumerate(folders):
            folder_name = os.path.basename(folder_path)
            btn_folder = ctk.CTkButton(
                self.scroll_frame,
                text=f"📁 {folder_name.upper()}",
                font=("Arial", 18, "bold"),
                height=85,
                fg_color="#2980B9",
                hover_color="#1F618D",
                command=lambda p=folder_path: self.change_dir(p)
            )
            row = current_row + (idx // 2)
            col = idx % 2
            btn_folder.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            
        # Offset the row counter by the number of folders drawn
        if folders:
            current_row += (len(folders) + 1) // 2

        # 3. Render Playable Audio Files
        for idx, track_path in enumerate(files):
            song_title = os.path.basename(track_path).replace(".mp3", "")
            btn_track = ctk.CTkButton(
                self.scroll_frame,
                text=song_title,
                font=("Arial", 18),
                height=85,
                fg_color="#34495E",
                hover_color="#2C3E50",
                command=lambda i=idx: self.play_song(i)
            )
            row = current_row + (idx // 2)
            col = idx % 2
            btn_track.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

    def build_song_picker(self):
        """Prepares the main structural viewport box for the scrolling list."""
        self.scroll_frame = ctk.CTkScrollableFrame(self, orientation="vertical")
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=1)

    def build_controls(self):
        """Draws the big media playback hub layout locked directly to the screen bottom."""
        self.controls_frame = ctk.CTkFrame(self, height=120, corner_radius=0)
        self.controls_frame.grid(row=1, column=0, sticky="ew")
        
        self.controls_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.controls_frame.grid_columnconfigure(3, weight=2)
        
        self.btn_back = ctk.CTkButton(
            self.controls_frame, text="⏮ BACK", font=("Arial", 22, "bold"),
            height=85, fg_color="#E67E22", hover_color="#D35400", command=self.prev_song
        )
        self.btn_back.grid(row=0, column=0, padx=10, pady=15, sticky="ew")
        
        self.btn_toggle = ctk.CTkButton(
            self.controls_frame, text="▶ PLAY", font=("Arial", 22, "bold"),
            height=85, fg_color="#2ECC71", hover_color="#27AE60", command=self.toggle_play
        )
        self.btn_toggle.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        
        self.btn_next = ctk.CTkButton(
            self.controls_frame, text="NEXT ⏭", font=("Arial", 22, "bold"),
            height=85, fg_color="#E67E22", hover_color="#D35400", command=self.next_song
        )
        self.btn_next.grid(row=0, column=2, padx=10, pady=15, sticky="ew")
        
        self.lbl_status = ctk.CTkLabel(
            self.controls_frame, text="Select a folder or song!", font=("Arial", 16, "bold"),
            anchor="w", justify="left"
        )
        self.lbl_status.grid(row=0, column=3, padx=20, pady=15, sticky="ew")

    # 3. INTERACTIVE LOGIC PIPELINES
    def change_dir(self, target_directory):
        """Enters a subfolder and redraws the display."""
        self.current_dir = target_directory
        self.refresh_grid()

    def go_to_parent_dir(self):
        """Exits back up to the primary base directory structure."""
        self.current_dir = self.base_dir
        self.refresh_grid()

    def play_song(self, index):
        if not self.playlist: return
        self.current_index = index
        track = self.playlist[self.current_index]
        
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play()
            self.is_playing = True
            self.btn_toggle.configure(text="⏸ PAUSE", fg_color="#E74C3C", hover_color="#C0392B")
            
            song_name = os.path.basename(track).replace(".mp3", "")
            self.lbl_status.configure(text=f"Playing Now:\n{song_name}")
        except Exception as e:
            self.lbl_status.configure(text="Error playing file")

    def toggle_play(self):
        if not self.playlist: return
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.btn_toggle.configure(text="▶ PLAY", fg_color="#2ECC71", hover_color="#27AE60")
        else:
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