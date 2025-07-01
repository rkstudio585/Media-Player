import subprocess
import curses
import argparse
import json
import os
from mutagen import File
from mutagen.id3 import ID3NoHeaderError
import requests
import time

# Configuration for Genius API (replace with your actual client access token)
GENIUS_API_TOKEN = os.environ.get("GENIUS_API_TOKEN")
GENIUS_API_URL = "https://api.genius.com"

class MediaController:
    def __init__(self):
        self.current_file = ""
        self.metadata = {}
        self.is_playing = False
        self.volume = 50  # Default volume
        self.playlist = []
        self.current_track_index = -1
        self.repeat_mode = False
        self.shuffle_mode = False
        self.last_position = 0
        self.playback_start_time = 0
        self.paused_time = 0
        self.config_file = os.path.expanduser("~/.termux_media_controller_config.json")

        self.load_config()

    def _run_termux_command(self, command, timeout=5, blocking=True):
        try:
            if blocking:
                result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)
                return result.stdout.strip()
            else:
                # For non-blocking commands (like play, pause, stop), just start the process
                subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return ""
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            print(f"Command not found. Make sure '{command[0]}' is installed and in your PATH.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while running command {' '.join(command)}: {e}")
            return None

    def play(self, file_path=None):
        if file_path:
            self.current_file = os.path.expanduser(file_path)
            self.current_track_index = -1 # Reset index if playing a specific file
            self.last_position = 0 # Reset position for new file
        elif self.playlist and self.current_track_index != -1:
            self.current_file = self.playlist[self.current_track_index]
        elif not self.current_file:
            print("No file specified to play.")
            return

        if not os.path.exists(self.current_file):
            print(f"Error: File not found: {self.current_file}")
            return

        print(f"Playing: {self.current_file}")
        self._run_termux_command(["termux-media-player", "play", self.current_file], blocking=False)
        self.is_playing = True
        self.playback_start_time = time.time() - self.last_position # Account for resuming
        self.load_metadata()
        self.send_notification(f"Playing: {self.metadata.get('artist', 'Unknown')} - {self.metadata.get('title', 'Unknown')}")
        self.save_config()

    def pause(self):
        if self.is_playing:
            self._run_termux_command(["termux-media-player", "pause"], blocking=False)
            self.is_playing = False
            self.paused_time = time.time()
            self.last_position += (self.paused_time - self.playback_start_time)
            self.send_notification("Paused")
            self.save_config()

    def stop(self):
        if self.is_playing:
            self._run_termux_command(["termux-media-player", "stop"], blocking=False)
            self.is_playing = False
            self.last_position = 0  # Reset position on stop
            self.send_notification("Stopped")
            self.save_config()

    def next_track(self):
        if not self.playlist:
            print("No playlist loaded.")
            return

        if self.shuffle_mode:
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist) # Simple shuffle for now
        else:
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)

        if self.current_track_index == 0 and not self.repeat_mode:
            self.stop()
            print("Playlist finished.")
            return

        self.play()

    def prev_track(self):
        if not self.playlist:
            print("No playlist loaded.")
            return

        self.current_track_index = (self.current_track_index - 1 + len(self.playlist)) % len(self.playlist)
        self.play()

    def load_metadata(self):
        try:
            audio = File(self.current_file)
            self.metadata = {
                'title': audio.get('title', ['Unknown Title'])[0],
                'artist': audio.get('artist', ['Unknown Artist'])[0],
                'album': audio.get('album', ['Unknown Album'])[0],
                'duration': audio.info.length if audio.info.length else 0
            }
        except ID3NoHeaderError:
            print(f"No ID3 tags found for {self.current_file}. Trying to extract basic info.")
            self.metadata = {
                'title': os.path.basename(self.current_file),
                'artist': 'Unknown Artist',
                'album': 'Unknown Album',
                'duration': 0 # Cannot get duration without proper tags or ffmpeg parsing
            }
        except Exception as e:
            print(f"Error loading metadata for {self.current_file}: {e}")
            self.metadata = {
                'title': os.path.basename(self.current_file),
                'artist': 'Unknown Artist',
                'album': 'Unknown Album',
                'duration': 0
            }

    def get_playback_info(self):
        current_seconds = self.last_position
        total_seconds = self.metadata.get('duration', 0)

        if self.is_playing:
            current_seconds = self.last_position + (time.time() - self.playback_start_time)
            if current_seconds > total_seconds and total_seconds > 0:
                current_seconds = total_seconds # Cap at total duration

        return current_seconds, total_seconds

    def set_volume(self, level):
        self.volume = max(0, min(100, level))
        self._run_termux_command(["termux-volume", "music", str(self.volume)], blocking=False)
        self.save_config()

    def get_lyrics(self, artist, title):
        if not GENIUS_API_TOKEN:
            print("Genius API token not set. Please set the GENIUS_API_TOKEN environment variable.")
            return []

        search_url = f"{GENIUS_API_URL}/search"
        headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
        params = {"q": f"{artist} {title}"}

        try:
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            song_id = None
            for hit in data["response"]["hits"]:
                if hit["result"]["primary_artist"]["name"].lower() == artist.lower() and \
                   hit["result"]["title"].lower() == title.lower():
                    song_id = hit["result"]["id"]
                    break
            
            if song_id:
                song_url = f"{GENIUS_API_URL}/songs/{song_id}"
                song_response = requests.get(song_url, headers=headers)
                song_response.raise_for_status()
                song_data = song_response.json()
                
                # Genius API does not provide synchronized lyrics directly.
                # We would typically scrape the lyrics from the song_data['response']['song']['url']
                # For this example, we'll just return a placeholder.
                print("Genius API found song, but synchronized lyrics scraping is complex and not implemented.")
                return ["Lyrics not available or scraping not implemented.", "Please visit the Genius page for full lyrics."]
            else:
                print(f"No lyrics found on Genius for {artist} - {title}")
                return ["No lyrics found."]

        except requests.exceptions.RequestException as e:
            print(f"Error fetching lyrics from Genius API: {e}")
            return ["Error fetching lyrics."]
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return ["An unexpected error occurred."]

    def load_playlist(self, playlist_path):
        playlist_path = os.path.expanduser(playlist_path)
        if not os.path.exists(playlist_path):
            print(f"Playlist file not found: {playlist_path}")
            return

        self.playlist = []
        with open(playlist_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'): # Ignore comments and empty lines
                    self.playlist.append(os.path.abspath(line)) # Store absolute paths

        if self.playlist:
            self.current_track_index = 0
            print(f"Loaded playlist with {len(self.playlist)} tracks.")
        else:
            print("Playlist is empty.")
        self.save_config()

    def save_playlist(self, playlist_path):
        playlist_path = os.path.expanduser(playlist_path)
        with open(playlist_path, 'w') as f:
            for track in self.playlist:
                f.write(f"{track}\n")
        print(f"Playlist saved to {playlist_path}")

    def shuffle_playlist(self):
        import random
        random.shuffle(self.playlist)
        self.current_track_index = 0
        print("Playlist shuffled.")
        self.save_config()

    def toggle_repeat(self):
        self.repeat_mode = not self.repeat_mode
        print(f"Repeat mode: {'On' if self.repeat_mode else 'Off'}")
        self.save_config()

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        print(f"Shuffle mode: {'On' if self.shuffle_mode else 'Off'}")
        self.save_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_file = config.get('current_file', '')
                    self.last_position = config.get('last_position', 0)
                    self.volume = config.get('volume', 50)
                    self.playlist = config.get('playlist', [])
                    self.current_track_index = config.get('current_track_index', -1)
                    self.repeat_mode = config.get('repeat_mode', False)
                    self.shuffle_mode = config.get('shuffle_mode', False)
                print("Configuration loaded.")
            except json.JSONDecodeError:
                print("Error decoding config file. Starting with default settings.")
        else:
            print("No config file found. Starting with default settings.")

    def save_config(self):
        config = {
            'current_file': self.current_file,
            'last_position': self.last_position,
            'volume': self.volume,
            'playlist': self.playlist,
            'current_track_index': self.current_track_index,
            'repeat_mode': self.repeat_mode,
            'shuffle_mode': self.shuffle_mode
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def resume_playback(self):
        if self.current_file and os.path.exists(self.current_file):
            print(f"Resuming playback of {self.current_file} from {self.last_position} seconds.")
            self._run_termux_command(["termux-media-player", "play", self.current_file])
            self.is_playing = True
            self.playback_start_time = time.time() - self.last_position
            self.load_metadata()
            self.send_notification(f"Playing: {self.metadata.get('artist', 'Unknown')} - {self.metadata.get('title', 'Unknown')}")
            self.save_config()
        else:
            print("No previous session to resume.")

    def send_notification(self, message):
        self._run_termux_command(["termux-notification", "--content", message], blocking=False)

    def curses_ui(self, stdscr):
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True) # Non-blocking input
        stdscr.timeout(100) # Refresh every 100ms
        stdscr.keypad(True) # Enable interpretation of special keys

        lyrics_lines = []
        lyrics_scroll_pos = 0

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            # Handle input
            key = stdscr.getch()
            if key == curses.ERR:
                key = -1 # No key pressed

            if key == ord('q'):
                break
            elif key == ord(' '):
                if self.is_playing:
                    self.pause()
                else:
                    self.play()
            elif key == curses.KEY_RIGHT:
                self.next_track()
            elif key == curses.KEY_LEFT:
                self.prev_track()
            elif key == curses.KEY_UP:
                self.set_volume(self.volume + 5)
            elif key == curses.KEY_DOWN:
                self.set_volume(self.volume - 5)
            elif key == ord('s'):
                self.toggle_shuffle()
            elif key == ord('r'):
                self.toggle_repeat()
            elif key == ord('l'):
                # Fetch and display lyrics
                if self.metadata.get('artist') and self.metadata.get('title'):
                    lyrics_lines = self.get_lyrics(self.metadata['artist'], self.metadata['title'])
                    lyrics_scroll_pos = 0
                else:
                    lyrics_lines = ["No metadata available for lyrics."]

            # Display metadata
            if self.current_file:
                self.load_metadata() # Refresh metadata in case it changed
                current_pos, total_duration = self.get_playback_info()
                
                status = "[▶]" if self.is_playing else "[⏸]"
                
                title_artist = f"{self.metadata.get('artist', 'Unknown')} - {self.metadata.get('title', 'Unknown')}"
                
                # Time display
                elapsed_time = time.strftime('%M:%S', time.gmtime(current_pos))
                total_time = time.strftime('%M:%S', time.gmtime(total_duration))
                time_display = f"{elapsed_time}/{total_time}"

                stdscr.addstr(0, 0, f"{status} {title_artist} ({time_display})")

                # Progress bar
                if total_duration > 0:
                    progress_percent = current_pos / total_duration
                    bar_length = width - 20 # Adjust bar length based on terminal width
                    filled_length = int(bar_length * progress_percent)
                    progress_bar = "█" * filled_length + "░" * (bar_length - filled_length)
                    stdscr.addstr(1, 0, f"Progress: [{progress_bar}] {int(progress_percent*100)}%")

                # Volume display
                volume_bar_length = 20
                filled_volume = int(volume_bar_length * (self.volume / 100))
                volume_bar = "█" * filled_volume + "░" * (volume_bar_length - filled_volume)
                stdscr.addstr(2, 0, f"Volume: [{volume_bar}] {self.volume}%")

                # Playback modes
                stdscr.addstr(3, 0, f"Shuffle: {'On' if self.shuffle_mode else 'Off'} | Repeat: {'On' if self.repeat_mode else 'Off'}")

                # Lyrics display
                if lyrics_lines:
                    stdscr.addstr(5, 0, "--- Lyrics ---")
                    display_lines = min(height - 7, len(lyrics_lines) - lyrics_scroll_pos)
                    for i in range(display_lines):
                        line_to_display = lyrics_lines[lyrics_scroll_pos + i]
                        stdscr.addstr(6 + i, 0, line_to_display[:width-1]) # Truncate to fit width

                    # Simple scroll for lyrics (for now, just scroll down if more lines than screen height)
                    if len(lyrics_lines) > (height - 7):
                        lyrics_scroll_pos = (lyrics_scroll_pos + 1) % (len(lyrics_lines) - (height - 7) + 1)
                        if lyrics_scroll_pos < 0: lyrics_scroll_pos = 0 # Prevent negative index

            else:
                stdscr.addstr(0, 0, "No media loaded. Use 'python media_controller.py <file_or_playlist>'")
            
            stdscr.refresh()
            time.sleep(0.1) # Small delay to prevent busy-waiting

def main():
    parser = argparse.ArgumentParser(description="Termux Media Controller")
    parser.add_argument("path", nargs="?", help="Path to media file or playlist (.m3u)")
    parser.add_argument("--lyrics", action="store_true", help="Fetch and display lyrics for the current track")
    parser.add_argument("--resume", action="store_true", help="Resume playback from last session")
    parser.add_argument("--volume", type=int, help="Set initial volume (0-100)")
    parser.add_argument("--playlist", help="Load a playlist file (.m3u)")
    parser.add_argument("--save-playlist", help="Save current playlist to a file (.m3u)")
    parser.add_argument("--shuffle", action="store_true", help="Enable shuffle mode")
    parser.add_argument("--repeat", action="store_true", help="Enable repeat mode")

    args = parser.parse_args()

    controller = MediaController()

    if args.volume is not None:
        controller.set_volume(args.volume)

    if args.playlist:
        controller.load_playlist(args.playlist)
    
    if args.shuffle:
        controller.toggle_shuffle()

    if args.repeat:
        controller.toggle_repeat()

    if args.path:
        if args.path.endswith(".m3u"):
            controller.load_playlist(args.path)
            controller.play()
        else:
            controller.play(args.path)
    elif args.resume:
        controller.resume_playback()
    elif not controller.current_file and not controller.playlist:
        print("No media specified. Use 'python media_controller.py <file_or_playlist>' or '--resume'.")
        return

    if args.lyrics:
        # If --lyrics is used without a UI, just print them
        if controller.metadata.get('artist') and controller.metadata.get('title'):
            lyrics = controller.get_lyrics(controller.metadata['artist'], controller.metadata['title'])
            for line in lyrics:
                print(line)
        else:
            print("No media loaded or metadata available to fetch lyrics.")
        return # Exit after displaying lyrics if no UI is intended

    if args.save_playlist:
        controller.save_playlist(args.save_playlist)
        return # Exit after saving playlist if no UI is intended

    try:
        curses.wrapper(controller.curses_ui)
    except curses.error as e:
        print(f"Curses error: {e}. This might happen if your terminal does not support curses or is too small.")
        print("Try running without the UI by specifying a file directly or using --lyrics.")
    finally:
        controller.stop() # Ensure media player is stopped on exit

if __name__ == "__main__":
    main()
