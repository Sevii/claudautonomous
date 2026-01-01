/**
 * Wake Word Detection Types
 *
 * Type definitions for the openWakeWord integration with Electron
 */

export interface WakeWordConfig {
  /** Path to the directory containing ONNX models */
  modelsPath: string;

  /** Wake word model names to load (e.g., ['hey_jarvis', 'alexa']) */
  keywords: string[];

  /** Detection threshold (0.0-1.0), default 0.5 */
  detectionThreshold?: number;

  /** Cooldown period in ms to prevent duplicate detections, default 2000 */
  cooldownMs?: number;

  /** Enable Voice Activity Detection, default true */
  enableVAD?: boolean;

  /** VAD threshold (0.0-1.0), default 0.5 */
  vadThreshold?: number;

  /** Audio sample rate, default 16000 */
  sampleRate?: number;

  /** Frame size in samples (80ms at 16kHz = 1280), default 1280 */
  frameSize?: number;

  /** Enable debug logging */
  debug?: boolean;
}

export interface WakeWordDetection {
  /** Detected wake word name */
  keyword: string;

  /** Confidence score (0.0-1.0) */
  score: number;

  /** Timestamp of detection (ms since epoch) */
  timestamp: number;

  /** Frame index when detected */
  frameIndex: number;
}

export interface VADState {
  /** Whether speech is currently detected */
  isSpeaking: boolean;

  /** Confidence score of current speech detection */
  confidence: number;

  /** Duration of current speech segment in ms */
  duration: number;
}

export interface ModelInfo {
  /** Model name */
  name: string;

  /** Model file path */
  path: string;

  /** Whether model is loaded */
  loaded: boolean;

  /** Model type */
  type: 'melspectrogram' | 'embedding' | 'vad' | 'keyword';
}

export interface WakeWordEngineState {
  /** Whether engine is initialized */
  initialized: boolean;

  /** Whether engine is currently listening */
  listening: boolean;

  /** Loaded models info */
  models: ModelInfo[];

  /** Current VAD state */
  vadState: VADState;

  /** Total frames processed */
  framesProcessed: number;
}

export interface AudioFrame {
  /** Raw PCM samples (16-bit signed integers as Float32) */
  samples: Float32Array;

  /** Sample rate */
  sampleRate: number;

  /** Frame timestamp */
  timestamp: number;
}

export type WakeWordEventType = 'ready' | 'detect' | 'speech-start' | 'speech-end' | 'error';

export interface WakeWordEvent {
  type: WakeWordEventType;
  data?: WakeWordDetection | VADState | Error;
}

export type WakeWordCallback = (event: WakeWordEvent) => void;

/**
 * Required ONNX models for openWakeWord
 */
export const REQUIRED_MODELS = {
  melspectrogram: 'melspectrogram.onnx',
  embedding: 'embedding_model.onnx',
  vad: 'silero_vad.onnx'
} as const;

/**
 * Available pre-trained wake word models
 */
export const AVAILABLE_KEYWORDS = [
  'alexa',
  'hey_jarvis',
  'hey_mycroft',
  'hey_rhasspy',
  'timer',
  'weather'
] as const;

export type AvailableKeyword = typeof AVAILABLE_KEYWORDS[number];
