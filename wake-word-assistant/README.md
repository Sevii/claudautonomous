# Wake Word Assistant

A Python Tkinter application that listens for a wake word and then captures voice commands using speech recognition.

## Features

- **Local wake word detection** using [openWakeWord](https://github.com/dscripka/openWakeWord)
- **Voice command capture** using Google Speech Recognition
- **Tkinter GUI** with real-time status indicators
- **Customizable threshold** for detection sensitivity
- **Support for custom wake word models**

## Available Wake Words

openWakeWord includes these pre-trained wake words:

| Wake Word | Model Name |
|-----------|------------|
| "Alexa" | `alexa` |
| "Hey Jarvis" | `hey_jarvis` |
| "Hey Mycroft" | `hey_mycroft` |
| "Hey Rhasspy" | `hey_rhasspy` |
| "Ok Nabu" | `ok_nabu` |

**Note:** A "computer" wake word is NOT included by default. See the [Custom Wake Word](#training-a-custom-computer-wake-word) section below to train one.

## Installation

### Prerequisites

- Python 3.8+
- PortAudio (required for PyAudio)
- Working microphone

### Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-dev
```

**macOS:**
```bash
brew install portaudio
```

**Windows:**
PyAudio wheels are usually available, but you may need to install from a pre-built wheel.

### Install Python Dependencies

```bash
cd wake-word-assistant
pip install -r requirements.txt
```

The first run will automatically download the openWakeWord models (~50MB).

## Usage

### Basic Usage (default: "hey jarvis")

```bash
python main.py
```

### Use a Different Wake Word

```bash
python main.py --wake-word alexa
python main.py --wake-word hey_mycroft
```

### Use a Custom Wake Word Model

```bash
python main.py --custom-model /path/to/computer.tflite
```

### Adjust Detection Threshold

```bash
python main.py --threshold 0.6
```

Lower threshold = more sensitive (more false positives)
Higher threshold = less sensitive (may miss some activations)

## How It Works

1. **Wake Word Detection**: The app continuously listens for the wake word using openWakeWord
2. **Wake Word Detected**: When the wake word is heard, the app pauses wake word detection
3. **Command Capture**: The app listens for your voice command (up to 10 seconds)
4. **Speech Recognition**: Your command is transcribed using Google Speech Recognition
5. **Resume**: The app resumes listening for the wake word

## Training a Custom "Computer" Wake Word

Since openWakeWord doesn't include a pre-trained "computer" model, you can train your own:

### Option 1: Google Colab (Recommended - No ML Experience Needed)

1. Open the [openWakeWord Training Notebook](https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb)
2. Enter "computer" as your wake word
3. Run all cells (takes ~1 hour with free Colab)
4. Download the generated `.tflite` model
5. Use it with this app:
   ```bash
   python main.py --custom-model computer.tflite
   ```

### Option 2: Advanced Training

For better quality models, use the [detailed training notebook](https://github.com/dscripka/openWakeWord/blob/main/notebooks/automatic_model_training.ipynb) which allows:
- Custom synthetic voice generation
- Real voice sample integration
- Fine-tuning for better accuracy

## Architecture

```
wake-word-assistant/
├── main.py                 # Tkinter GUI application
├── wake_word_detector.py   # openWakeWord integration
├── speech_recognizer.py    # Speech-to-text module
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### Key Components

- **WakeWordDetector**: Runs in a background thread, continuously processing audio for wake word detection
- **SpeechRecognizer**: Captures and transcribes voice commands after wake word activation
- **WakeWordAssistantApp**: Tkinter GUI that coordinates detection and recognition

## Customization

### Adding Command Processing

Edit `main.py` and modify the `_process_command` method:

```python
def _process_command(self, text: str):
    """Process the recognized command."""
    self._log(f"Command: \"{text}\"", "command")

    # Add your command processing logic here
    if "weather" in text.lower():
        self._log("Fetching weather...", "info")
        # ... get weather
    elif "lights" in text.lower():
        self._log("Controlling lights...", "info")
        # ... control smart home
    else:
        # Send to LLM for general queries
        pass
```

### Using Local Speech Recognition

For offline speech recognition, replace Google with Whisper:

```bash
pip install openai-whisper
```

Then modify `speech_recognizer.py` to use Whisper instead of Google's API.

## Troubleshooting

### "No module named 'pyaudio'"
Install PortAudio first (see Installation section), then:
```bash
pip install pyaudio
```

### "Could not find input device"
Ensure your microphone is connected and recognized by the system.

### High false positive rate
Increase the detection threshold:
```bash
python main.py --threshold 0.7
```

### Wake word not detected
- Speak clearly and at normal volume
- Lower the threshold: `--threshold 0.3`
- Ensure you're using the exact wake phrase (e.g., "hey jarvis" not just "jarvis")

## License

This project uses openWakeWord models which are licensed under CC BY-NC-SA 4.0 (non-commercial use).

## Resources

- [openWakeWord GitHub](https://github.com/dscripka/openWakeWord)
- [openWakeWord Models on HuggingFace](https://huggingface.co/davidscripka/openwakeword)
- [Training Custom Wake Words](https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb)
- [SpeechRecognition Library](https://pypi.org/project/SpeechRecognition/)
