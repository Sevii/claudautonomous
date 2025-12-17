#!/bin/bash

# Simple script to install an audio player for the elevator music extension

echo "Installing audio player for elevator music extension..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v apt-get >/dev/null 2>&1; then
        echo "Detected Debian/Ubuntu system"
        echo "Installing ffmpeg..."
        sudo apt-get update && sudo apt-get install -y ffmpeg
    elif command -v yum >/dev/null 2>&1; then
        echo "Detected RedHat/CentOS system"
        echo "Installing ffmpeg..."
        sudo yum install -y ffmpeg
    elif command -v pacman >/dev/null 2>&1; then
        echo "Detected Arch Linux system"
        echo "Installing ffmpeg..."
        sudo pacman -S --noconfirm ffmpeg
    else
        echo "Unknown package manager. Please install ffmpeg, mpv, or vlc manually."
        exit 1
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew >/dev/null 2>&1; then
        echo "Detected macOS with Homebrew"
        echo "Installing ffmpeg..."
        brew install ffmpeg
    else
        echo "Homebrew not found. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "Then run this script again."
        exit 1
    fi
else
    echo "Unknown operating system: $OSTYPE"
    echo "Please install ffmpeg, mpv, or vlc manually."
    exit 1
fi

echo ""
echo "Installation complete! Testing audio player..."
if command -v ffplay >/dev/null 2>&1; then
    echo "✓ ffplay is now available"
    echo ""
    echo "Run './elevator-music.sh test' to test the extension"
else
    echo "✗ Installation may have failed. Please check for errors above."
    exit 1
fi
