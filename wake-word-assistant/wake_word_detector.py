"""
Wake Word Detection Module using openWakeWord

This module provides a thread-based wake word detector that continuously
listens for a specified wake word and triggers a callback when detected.
"""

import threading
import numpy as np
import pyaudio
from typing import Callable, Optional, List
import openwakeword
from openwakeword.model import Model


class WakeWordDetector:
    """
    A wake word detector that runs in a background thread.

    Uses openWakeWord for efficient, local wake word detection.
    Supports multiple wake word models simultaneously.
    """

    # Audio configuration for openWakeWord
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1280  # ~80ms of audio at 16kHz

    def __init__(
        self,
        wake_words: Optional[List[str]] = None,
        custom_model_paths: Optional[List[str]] = None,
        threshold: float = 0.5,
        inference_framework: str = "tflite",
        on_wake_word: Optional[Callable[[str, float], None]] = None,
        enable_vad: bool = True,
        vad_threshold: float = 0.5,
    ):
        """
        Initialize the wake word detector.

        Args:
            wake_words: List of built-in wake words to detect.
                       Available: "alexa", "hey_jarvis", "hey_mycroft",
                                  "hey_rhasspy", "ok_nabu"
            custom_model_paths: Paths to custom .tflite or .onnx models
            threshold: Detection confidence threshold (0.0 to 1.0)
            inference_framework: "tflite" or "onnx"
            on_wake_word: Callback function(wake_word_name, score)
            enable_vad: Enable voice activity detection to reduce false positives
            vad_threshold: VAD sensitivity (0.0 to 1.0)
        """
        self.wake_words = wake_words or ["hey_jarvis"]
        self.custom_model_paths = custom_model_paths or []
        self.threshold = threshold
        self.inference_framework = inference_framework
        self.on_wake_word = on_wake_word
        self.enable_vad = enable_vad
        self.vad_threshold = vad_threshold

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._audio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._model: Optional[Model] = None
        self._paused = False
        self._lock = threading.Lock()

    def _download_models(self):
        """Download pre-trained models if not already present."""
        print("Checking/downloading openWakeWord models...")
        openwakeword.utils.download_models()
        print("Models ready.")

    def _init_audio(self):
        """Initialize PyAudio and microphone stream."""
        self._audio = pyaudio.PyAudio()
        self._stream = self._audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

    def _init_model(self):
        """Initialize the openWakeWord model."""
        # Build list of models to load
        wakeword_models = list(self.custom_model_paths)

        # Create model with VAD if enabled
        vad_threshold = self.vad_threshold if self.enable_vad else None

        self._model = Model(
            wakeword_models=wakeword_models if wakeword_models else None,
            inference_framework=self.inference_framework,
            vad_threshold=vad_threshold,
        )

        print(f"Loaded models: {list(self._model.models.keys())}")

    def _detection_loop(self):
        """Main detection loop running in background thread."""
        while self._running:
            try:
                with self._lock:
                    if self._paused:
                        continue

                # Read audio chunk
                audio_data = self._stream.read(self.CHUNK, exception_on_overflow=False)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # Run prediction
                predictions = self._model.predict(audio_array)

                # Check each model's prediction
                for model_name, scores in self._model.prediction_buffer.items():
                    current_score = scores[-1]

                    if current_score >= self.threshold:
                        print(f"Wake word detected: {model_name} (score: {current_score:.3f})")

                        # Reset the prediction buffer to prevent repeated triggers
                        self._model.reset()

                        # Call the callback
                        if self.on_wake_word:
                            self.on_wake_word(model_name, current_score)
                        break

            except Exception as e:
                if self._running:  # Only log if we're supposed to be running
                    print(f"Error in detection loop: {e}")

    def start(self):
        """Start the wake word detection in a background thread."""
        if self._running:
            print("Detector is already running.")
            return

        self._download_models()
        self._init_audio()
        self._init_model()

        self._running = True
        self._thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._thread.start()

        print(f"Wake word detector started. Listening for: {list(self._model.models.keys())}")

    def stop(self):
        """Stop the wake word detection."""
        self._running = False

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        if self._audio:
            self._audio.terminate()
            self._audio = None

        print("Wake word detector stopped.")

    def pause(self):
        """Temporarily pause detection (e.g., while processing a command)."""
        with self._lock:
            self._paused = True

    def resume(self):
        """Resume detection after pause."""
        with self._lock:
            self._paused = False
            # Reset model to clear any buffered predictions
            if self._model:
                self._model.reset()

    @property
    def is_running(self) -> bool:
        """Check if the detector is running."""
        return self._running

    @property
    def is_paused(self) -> bool:
        """Check if the detector is paused."""
        return self._paused
