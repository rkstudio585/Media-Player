# Termux Media Controller

A feature-rich media player for Termux, built with Python, offering comprehensive media control, metadata display, playlist management, and a curses-based terminal UI.

## Features

- **Media Playback**: Play, pause, stop, next, and previous track control using `termux-media-player`.
- **Metadata Display**: Extracts and displays track metadata (Title, Artist, Album, Duration) using `mutagen`.
- **Volume Control**: Adjusts system volume via `termux-volume`.
- **Playlist Management**: Create, load, and manage `.m3u` playlists with shuffle and repeat modes.
- **Curses-based UI**: Interactive terminal interface with:
    - Playback status and current track information.
    - Progress bar with elapsed and total time.
    - Volume level visualization.
    - Shuffle and repeat mode indicators.
    - Basic lyrics display (requires Genius API token).
- **Keyboard Controls**: 
    - `Space`: Play/Pause
    - `Right Arrow`: Next Track
    - `Left Arrow`: Previous Track
    - `Up Arrow`: Increase Volume
    - `Down Arrow`: Decrease Volume
    - `s`: Toggle Shuffle Mode
    - `r`: Toggle Repeat Mode
    - `l`: Fetch and Display Lyrics
    - `q`: Quit
- **Notification Integration**: Sends Termux notifications for playback status.
- **Auto-Resume**: Resumes playback from the last played track and position on launch.
- **Command-line Arguments**: Supports direct file playback, lyrics-only mode, playlist loading/saving, and initial settings for volume, shuffle, and repeat.

## Requirements

### Termux Packages

Ensure you have the following Termux packages installed:

```bash
pkg install termux-api ffmpeg
```

- `termux-api`: Provides access to Termux API functionalities like notifications and volume control.
- `ffmpeg`: Used by `termux-media-player` for media playback and information.

### Python Dependencies

Install the required Python libraries using `pip`:

```bash
pip install mutagen requests
```

- `mutagen`: For reading and manipulating audio metadata tags.
- `requests`: For making HTTP requests to the Genius API.

### Genius API (Optional, for Lyrics)

To fetch lyrics, you need a Genius API Client Access Token. 

1. Go to [Genius API](https://genius.com/api-clients).
2. Create a new API client.
3. Generate a Client Access Token.
4. Set the `GENIUS_API_TOKEN` environment variable with your token:

```bash
export GENIUS_API_TOKEN="YOUR_GENIUS_CLIENT_ACCESS_TOKEN"
```

## Usage

### Basic Playback

To play a single media file:

```bash
python media_controller.py ~/storage/music/my_song.mp3
```

### Resume Last Session

To resume playback from where you left off:

```bash
python media_controller.py --resume
```

### Load and Play a Playlist

To load and start playing an `.m3u` playlist:

```bash
python media_controller.py --playlist ~/storage/playlists/my_playlist.m3u
```

### Save Current Playlist

To save the currently loaded playlist to a new `.m3u` file:

```bash
python media_controller.py --save-playlist ~/storage/playlists/new_playlist.m3u
```

### Lyrics Only Mode

To fetch and display lyrics for a track without launching the UI (useful for debugging or quick lookups):

```bash
python media_controller.py ~/storage/music/my_song.mp3 --lyrics
```

### Set Initial Volume

```bash
python media_controller.py ~/storage/music/my_song.mp3 --volume 75
```

### Enable Shuffle/Repeat on Launch

```bash
python media_controller.py --playlist ~/storage/playlists/my_playlist.m3u --shuffle --repeat
```

### Full UI Mode

If you don't specify a file or playlist, and no previous session is found, the UI will launch in an idle state:

```bash
python media_controller.py
```

Then use the keyboard controls to interact.

## Known Issues and Future Improvements

- **Synchronized Lyrics**: The current Genius API integration fetches lyrics but does not provide synchronized display. Implementing this would require advanced parsing and timing mechanisms, potentially involving web scraping or a different API.
- **Progress Bar Accuracy**: The accuracy of the progress bar depends on the update frequency of `termux-media-player info`.
- **UI Enhancements**: Further refinements to the curses UI can include better layout, more dynamic scrolling for lyrics, and additional visual elements.
- **Error Handling**: More robust error handling and user feedback can be implemented.
- **Sleep Timer**: A sleep timer feature could be added.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
