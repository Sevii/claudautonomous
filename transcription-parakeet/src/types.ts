/**
 * Type definitions for Parakeet transcription
 */

export interface TranscriptionResult {
  text: string;
  timestamps?: WordTimestamp[];
}

export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
}

export interface TranscriptionOptions {
  /**
   * Path to the audio file to transcribe
   * Supported formats: .wav, .flac (16kHz monochannel recommended)
   */
  audioPath: string;

  /**
   * Whether to include word-level timestamps in the output
   * @default false
   */
  includeTimestamps?: boolean;

  /**
   * Sample rate of the audio (Hz)
   * @default 16000
   */
  sampleRate?: number;
}

export interface ParakeetConfig {
  /**
   * Path to the ONNX encoder model
   */
  encoderPath?: string;

  /**
   * Path to the ONNX decoder model
   */
  decoderPath?: string;

  /**
   * Path to the model directory (for NeMo Python approach)
   */
  modelPath?: string;
}
