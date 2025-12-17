# Claude Code Elevator Music Extension

Play soothing elevator music while Claude Code is idle and waiting for your input!

## What It Does

This extension automatically:
- Plays elevator music when Claude finishes a task and is waiting for you
- Stops the music when you start typing or submitting a prompt
- Cleans up when your session ends

## Features

- **Automatic playback**: No manual intervention needed
- **Multiple audio player support**: Works with ffplay, mpv, afplay, cvlc, or paplay
- **Auto-download**: Downloads royalty-free elevator music on first run
- **Custom music**: Use your own audio files
- **Lightweight**: Simple bash script with minimal overhead
- **Session-aware**: Tracks music per Claude session

## Installation

### Prerequisites

Install an audio player (at least one of these):

**Linux:**
```bash
# FFmpeg (recommended)
sudo apt-get install ffmpeg

# Or MPV
sudo apt-get install mpv

# Or VLC
sudo apt-get install vlc
```

**macOS:**
```bash
# FFmpeg
brew install ffmpeg

# Or MPV
brew install mpv

# afplay is built-in
```

### Setup

1. **Navigate to your project directory** (or wherever you want to install this)

2. **The extension is already in `claude-elevator/` directory**

3. **Configure Claude Code hooks**:

   Choose one of these configuration methods:

   **Option A: Project-level (Recommended for sharing with team)**

   Create or edit `.claude/settings.json` in your project:
   ```json
   {
     "hooks": {
       "Stop": [
         {
           "matcher": "",
           "hooks": [
             {
               "type": "command",
               "command": "/home/user/claudautonomous/claude-elevator/elevator-music.sh",
               "timeout": 5
             }
           ]
         }
       ],
       "UserPromptSubmit": [
         {
           "matcher": "",
           "hooks": [
             {
               "type": "command",
               "command": "/home/user/claudautonomous/claude-elevator/elevator-music.sh",
               "timeout": 2
             }
           ]
         }
       ],
       "SessionEnd": [
         {
           "matcher": "",
           "hooks": [
             {
               "type": "command",
               "command": "/home/user/claudautonomous/claude-elevator/elevator-music.sh",
               "timeout": 2
             }
           ]
         }
       ]
     }
   }
   ```

   **Option B: User-level (For all your Claude Code sessions)**

   Edit `~/.claude/settings.json` with the same configuration above.

4. **Update the path in your configuration** to point to where you installed the script

5. **Test the installation**:
   ```bash
   ./claude-elevator/elevator-music.sh test
   ```

## Usage

### Automatic Mode (Default)

Once configured, the music plays automatically:
1. Claude finishes responding → Music starts
2. You start typing → Music stops
3. Session ends → Cleanup

### Manual Mode (For Testing)

```bash
# Start music
./claude-elevator/elevator-music.sh start my-session-id

# Stop music
./claude-elevator/elevator-music.sh stop my-session-id

# Run test
./claude-elevator/elevator-music.sh test
```

## Customization

### Use Your Own Music

1. Place your audio file in `claude-elevator/sounds/elevator-music.mp3`
2. Supported formats: MP3, WAV, OGG (depends on your audio player)

### Change the Music URL

Edit `elevator-music.sh` and change the `MUSIC_URL` variable:
```bash
MUSIC_URL="https://your-url-here.com/music.mp3"
```

### Enable Logging

Uncomment the logging line in `elevator-music.sh`:
```bash
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "${SCRIPT_DIR}/elevator-music.log"
}
```

### Adjust Volume

The script uses default system volume. Adjust your system volume or modify the script to add volume controls:

**For ffplay:**
```bash
ffplay -volume 30 -nodisp -autoexit -loop 0 "$audio_source"
```

**For mpv:**
```bash
mpv --volume=30 --no-video --loop=inf "$audio_source"
```

## How It Works

1. **Stop Hook**: When Claude finishes responding, the `Stop` hook fires
2. **Script Execution**: The script receives hook event data via stdin
3. **Audio Playback**: Starts background music player process
4. **PID Tracking**: Stores process ID in `/tmp/claude-elevator-music/`
5. **UserPromptSubmit Hook**: When you interact, this hook fires and stops the music
6. **Cleanup**: SessionEnd hook ensures no orphaned processes

## Troubleshooting

### No audio playing

1. Check if an audio player is installed:
   ```bash
   ffplay -version
   # or
   mpv --version
   ```

2. Test manually:
   ```bash
   ./claude-elevator/elevator-music.sh test
   ```

3. Check system volume is not muted

### Music doesn't stop

1. Check if PID files are stale:
   ```bash
   ls /tmp/claude-elevator-music/
   ```

2. Manually clean up:
   ```bash
   rm -rf /tmp/claude-elevator-music/
   pkill ffplay  # or pkill mpv
   ```

### Hook not triggering

1. Verify your `settings.json` syntax is valid JSON
2. Check the script path is absolute and correct
3. Ensure the script is executable:
   ```bash
   chmod +x claude-elevator/elevator-music.sh
   ```

### Music file download fails

The script will automatically stream from the URL if download fails. To manually download:
```bash
curl -L -o claude-elevator/sounds/elevator-music.mp3 "https://www.bensound.com/bensound-music/bensound-jazzyfrenchy.mp3"
```

## Configuration Reference

### Hook Types Used

- **Stop**: Fires when Claude finishes responding and is idle
- **UserPromptSubmit**: Fires when you submit input to Claude
- **SessionEnd**: Fires when the Claude Code session closes

### Script Arguments

- `start [session_id]`: Start music for a session
- `stop [session_id]`: Stop music for a session
- `test`: Run a 5-second test
- No args: Read hook event from stdin (hook mode)

### Environment Variables

The script creates these files:
- `/tmp/claude-elevator-music/<session_id>.pid`: Process ID tracking
- `claude-elevator/sounds/elevator-music.mp3`: Downloaded music file
- `claude-elevator/elevator-music.log`: Optional log file

## Uninstallation

1. Remove the hooks from your `settings.json`
2. Delete the `claude-elevator/` directory
3. Clean up PID files:
   ```bash
   rm -rf /tmp/claude-elevator-music/
   ```

## Credits

- Default music: "Jazzy Frenchy" by Bensound (royalty-free)
- Extension design based on Claude Code hooks system

## License

MIT License - Feel free to modify and share!

## Contributing

Found a bug or want to improve it? Feel free to submit issues or PRs to the repository!

---

Enjoy your elevator music experience with Claude Code! 🎵🎶
