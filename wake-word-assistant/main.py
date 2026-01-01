#!/usr/bin/env python3
"""
Wake Word Assistant - A Tkinter application with wake word detection

This application listens for a wake word (default: "hey jarvis") and then
captures user voice commands using speech recognition.

Usage:
    python main.py [--wake-word MODEL_NAME] [--custom-model PATH]

Examples:
    python main.py                           # Uses default "hey_jarvis"
    python main.py --wake-word alexa         # Uses "alexa" wake word
    python main.py --custom-model computer.tflite  # Uses custom model
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import argparse
from datetime import datetime
from typing import Optional

from wake_word_detector import WakeWordDetector
from speech_recognizer import SpeechRecognizer


class WakeWordAssistantApp:
    """
    A Tkinter GUI application for wake word detection and voice commands.

    Features:
    - Real-time wake word detection status
    - Voice command capture after wake word
    - Command history log
    - Start/Stop controls
    """

    def __init__(
        self,
        root: tk.Tk,
        wake_words: Optional[list] = None,
        custom_model_path: Optional[str] = None,
        threshold: float = 0.5,
    ):
        """
        Initialize the application.

        Args:
            root: The Tkinter root window
            wake_words: List of wake words to detect
            custom_model_path: Path to a custom .tflite model
            threshold: Detection confidence threshold
        """
        self.root = root
        self.wake_words = wake_words or ["hey_jarvis"]
        self.custom_model_path = custom_model_path
        self.threshold = threshold

        # State
        self._detector: Optional[WakeWordDetector] = None
        self._recognizer: Optional[SpeechRecognizer] = None
        self._is_running = False

        # Setup UI
        self._setup_window()
        self._create_widgets()
        self._setup_detector()
        self._setup_recognizer()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_window(self):
        """Configure the main window."""
        self.root.title("Wake Word Assistant")
        self.root.geometry("600x500")
        self.root.minsize(400, 350)

        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

    def _create_widgets(self):
        """Create all UI widgets."""
        # --- Status Frame ---
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        status_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        status_frame.columnconfigure(1, weight=1)

        # Wake word indicator
        ttk.Label(status_frame, text="Wake Word:").grid(row=0, column=0, sticky="w")
        self.wake_word_label = ttk.Label(
            status_frame,
            text=", ".join(self.wake_words),
            font=("TkDefaultFont", 10, "bold")
        )
        self.wake_word_label.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Detection status
        ttk.Label(status_frame, text="Status:").grid(row=1, column=0, sticky="w")
        self.status_label = ttk.Label(
            status_frame,
            text="Stopped",
            foreground="gray"
        )
        self.status_label.grid(row=1, column=1, sticky="w", padx=(10, 0))

        # Activity indicator (colored circle)
        self.canvas = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.canvas.grid(row=1, column=2, sticky="e")
        self.indicator = self.canvas.create_oval(2, 2, 18, 18, fill="gray", outline="darkgray")

        # --- Control Frame ---
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.start_button = ttk.Button(
            control_frame,
            text="Start Listening",
            command=self._toggle_listening
        )
        self.start_button.pack(side="left", padx=(0, 10))

        self.clear_button = ttk.Button(
            control_frame,
            text="Clear Log",
            command=self._clear_log
        )
        self.clear_button.pack(side="left")

        # Threshold slider
        ttk.Label(control_frame, text="Threshold:").pack(side="left", padx=(20, 5))
        self.threshold_var = tk.DoubleVar(value=self.threshold)
        self.threshold_slider = ttk.Scale(
            control_frame,
            from_=0.1,
            to=0.9,
            variable=self.threshold_var,
            orient="horizontal",
            length=100
        )
        self.threshold_slider.pack(side="left")
        self.threshold_label = ttk.Label(control_frame, text=f"{self.threshold:.1f}")
        self.threshold_label.pack(side="left", padx=(5, 0))
        self.threshold_var.trace_add("write", self._on_threshold_change)

        # --- Log Frame ---
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding=10)
        log_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("TkFixedFont", 9),
            state="disabled"
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # Configure text tags for colored output
        self.log_text.tag_configure("info", foreground="black")
        self.log_text.tag_configure("wake", foreground="green", font=("TkFixedFont", 9, "bold"))
        self.log_text.tag_configure("command", foreground="blue")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("listening", foreground="orange")

        # --- Info Frame ---
        info_frame = ttk.Frame(self.root, padding=5)
        info_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        info_text = (
            'Say the wake word to activate, then speak your command. '
            'Available wake words: alexa, hey_jarvis, hey_mycroft, hey_rhasspy, ok_nabu'
        )
        info_label = ttk.Label(info_frame, text=info_text, foreground="gray", wraplength=550)
        info_label.pack()

    def _setup_detector(self):
        """Initialize the wake word detector."""
        custom_models = [self.custom_model_path] if self.custom_model_path else []

        self._detector = WakeWordDetector(
            wake_words=self.wake_words,
            custom_model_paths=custom_models,
            threshold=self.threshold,
            on_wake_word=self._on_wake_word_detected,
            enable_vad=True,
            vad_threshold=0.5,
        )

    def _setup_recognizer(self):
        """Initialize the speech recognizer."""
        self._recognizer = SpeechRecognizer(
            timeout=5.0,
            phrase_time_limit=10.0,
            on_result=self._on_command_recognized,
            on_error=self._on_recognition_error,
            on_listening_start=self._on_listening_start,
            on_listening_end=self._on_listening_end,
        )

    def _toggle_listening(self):
        """Start or stop the wake word detection."""
        if self._is_running:
            self._stop_listening()
        else:
            self._start_listening()

    def _start_listening(self):
        """Start wake word detection."""
        self._log("Starting wake word detection...", "info")
        self.start_button.configure(state="disabled")

        # Start detector in background to not block UI
        def start():
            try:
                self._detector.threshold = self.threshold_var.get()
                self._detector.start()
                self._is_running = True
                self.root.after(0, self._update_ui_started)
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Failed to start: {e}", "error"))
                self.root.after(0, lambda: self.start_button.configure(state="normal"))

        threading.Thread(target=start, daemon=True).start()

    def _update_ui_started(self):
        """Update UI after detection started."""
        self.start_button.configure(text="Stop Listening", state="normal")
        self.status_label.configure(text="Listening for wake word...", foreground="green")
        self.canvas.itemconfig(self.indicator, fill="green")
        self._log(f"Listening for: {', '.join(self.wake_words)}", "info")

    def _stop_listening(self):
        """Stop wake word detection."""
        self._log("Stopping wake word detection...", "info")
        self._detector.stop()
        self._is_running = False

        self.start_button.configure(text="Start Listening")
        self.status_label.configure(text="Stopped", foreground="gray")
        self.canvas.itemconfig(self.indicator, fill="gray")
        self._log("Stopped.", "info")

    def _on_wake_word_detected(self, wake_word: str, score: float):
        """Handle wake word detection."""
        # Update UI from main thread
        self.root.after(0, lambda: self._handle_wake_word(wake_word, score))

    def _handle_wake_word(self, wake_word: str, score: float):
        """Process wake word detection in main thread."""
        self._log(f"Wake word detected: '{wake_word}' (confidence: {score:.2f})", "wake")

        # Update status
        self.status_label.configure(text="Wake word detected! Listening for command...", foreground="orange")
        self.canvas.itemconfig(self.indicator, fill="orange")

        # Pause wake word detection while listening for command
        self._detector.pause()

        # Start listening for command
        self._recognizer.listen_for_command()

    def _on_listening_start(self):
        """Called when speech recognition starts listening."""
        self.root.after(0, lambda: self._log("Listening for your command...", "listening"))

    def _on_listening_end(self):
        """Called when speech recognition stops listening."""
        # Resume wake word detection
        self.root.after(0, self._resume_detection)

    def _resume_detection(self):
        """Resume wake word detection after command processing."""
        if self._is_running:
            self._detector.resume()
            self.status_label.configure(text="Listening for wake word...", foreground="green")
            self.canvas.itemconfig(self.indicator, fill="green")

    def _on_command_recognized(self, text: str):
        """Handle recognized voice command."""
        self.root.after(0, lambda: self._process_command(text))

    def _process_command(self, text: str):
        """Process the recognized command."""
        self._log(f"Command: \"{text}\"", "command")

        # Here you would process the command
        # For example, integrate with an LLM, control smart home, etc.
        self._log("(Command processing would happen here)", "info")

    def _on_recognition_error(self, error: str):
        """Handle speech recognition error."""
        self.root.after(0, lambda: self._log(f"Recognition error: {error}", "error"))

    def _on_threshold_change(self, *args):
        """Handle threshold slider change."""
        value = self.threshold_var.get()
        self.threshold_label.configure(text=f"{value:.1f}")
        if self._detector:
            self._detector.threshold = value

    def _log(self, message: str, tag: str = "info"):
        """Add a message to the activity log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, formatted, tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        """Clear the activity log."""
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")

    def _on_close(self):
        """Handle window close event."""
        if self._is_running:
            self._detector.stop()
        self.root.destroy()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Wake Word Assistant - Voice-activated command interface"
    )
    parser.add_argument(
        "--wake-word",
        type=str,
        default="hey_jarvis",
        help="Wake word to use (alexa, hey_jarvis, hey_mycroft, hey_rhasspy, ok_nabu)"
    )
    parser.add_argument(
        "--custom-model",
        type=str,
        default=None,
        help="Path to a custom .tflite wake word model"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Detection confidence threshold (0.0 to 1.0)"
    )

    args = parser.parse_args()

    # Create main window
    root = tk.Tk()

    # Create application
    app = WakeWordAssistantApp(
        root,
        wake_words=[args.wake_word],
        custom_model_path=args.custom_model,
        threshold=args.threshold,
    )

    # Run main loop
    root.mainloop()


if __name__ == "__main__":
    main()
