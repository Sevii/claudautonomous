"""
Speech Recognition Module

This module provides speech-to-text functionality for capturing
user commands after a wake word is detected.
"""

import threading
import speech_recognition as sr
from typing import Callable, Optional


class SpeechRecognizer:
    """
    A speech recognizer that captures and transcribes user speech.

    Uses the SpeechRecognition library with Google's free API by default.
    Can be configured to use other backends like Whisper, Sphinx, etc.
    """

    def __init__(
        self,
        timeout: float = 5.0,
        phrase_time_limit: float = 10.0,
        on_result: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_listening_start: Optional[Callable[[], None]] = None,
        on_listening_end: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the speech recognizer.

        Args:
            timeout: Maximum seconds to wait for speech to begin
            phrase_time_limit: Maximum seconds for a single phrase
            on_result: Callback function(transcribed_text)
            on_error: Callback function(error_message)
            on_listening_start: Callback when listening begins
            on_listening_end: Callback when listening ends
        """
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        self.on_result = on_result
        self.on_error = on_error
        self.on_listening_start = on_listening_start
        self.on_listening_end = on_listening_end

        self._recognizer = sr.Recognizer()
        self._microphone = sr.Microphone()
        self._is_listening = False

        # Adjust for ambient noise on init
        self._calibrate()

    def _calibrate(self):
        """Calibrate the recognizer for ambient noise."""
        print("Calibrating microphone for ambient noise...")
        try:
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Microphone calibrated.")
        except Exception as e:
            print(f"Warning: Could not calibrate microphone: {e}")

    def listen_for_command(self):
        """
        Listen for a voice command in a background thread.

        This is non-blocking and will call the appropriate callback
        when finished.
        """
        thread = threading.Thread(target=self._listen_thread, daemon=True)
        thread.start()

    def _listen_thread(self):
        """Background thread for listening."""
        self._is_listening = True

        if self.on_listening_start:
            self.on_listening_start()

        try:
            with self._microphone as source:
                print("Listening for command...")
                audio = self._recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit
                )

            print("Processing speech...")

            # Use Google's free speech recognition API
            # For production, consider using Whisper or other local solutions
            text = self._recognizer.recognize_google(audio)

            print(f"Recognized: {text}")

            if self.on_result:
                self.on_result(text)

        except sr.WaitTimeoutError:
            error_msg = "No speech detected within timeout"
            print(error_msg)
            if self.on_error:
                self.on_error(error_msg)

        except sr.UnknownValueError:
            error_msg = "Could not understand speech"
            print(error_msg)
            if self.on_error:
                self.on_error(error_msg)

        except sr.RequestError as e:
            error_msg = f"Speech recognition service error: {e}"
            print(error_msg)
            if self.on_error:
                self.on_error(error_msg)

        except Exception as e:
            error_msg = f"Speech recognition error: {e}"
            print(error_msg)
            if self.on_error:
                self.on_error(error_msg)

        finally:
            self._is_listening = False
            if self.on_listening_end:
                self.on_listening_end()

    def listen_for_command_sync(self) -> Optional[str]:
        """
        Listen for a voice command synchronously (blocking).

        Returns:
            The transcribed text, or None if recognition failed.
        """
        self._is_listening = True

        try:
            with self._microphone as source:
                print("Listening for command...")
                audio = self._recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit
                )

            print("Processing speech...")
            text = self._recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text

        except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError) as e:
            print(f"Recognition failed: {e}")
            return None

        finally:
            self._is_listening = False

    @property
    def is_listening(self) -> bool:
        """Check if currently listening for speech."""
        return self._is_listening
