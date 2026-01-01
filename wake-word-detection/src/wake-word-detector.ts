/**
 * Wake Word Detector
 *
 * ONNX-based wake word detection using openWakeWord models.
 * Designed for use in Electron applications.
 */

import * as ort from 'onnxruntime-node';
import * as path from 'path';
import * as fs from 'fs';
import {
  WakeWordConfig,
  WakeWordDetection,
  WakeWordCallback,
  WakeWordEvent,
  WakeWordEngineState,
  ModelInfo,
  VADState,
  REQUIRED_MODELS
} from './types';

export class WakeWordDetector {
  private config: Required<WakeWordConfig>;
  private melSession: ort.InferenceSession | null = null;
  private embeddingSession: ort.InferenceSession | null = null;
  private vadSession: ort.InferenceSession | null = null;
  private keywordSessions: Map<string, ort.InferenceSession> = new Map();

  private listeners: WakeWordCallback[] = [];
  private isInitialized = false;
  private isListening = false;
  private framesProcessed = 0;
  private lastDetectionTime: Map<string, number> = new Map();

  // Audio buffer for accumulating samples
  private audioBuffer: Float32Array;
  private bufferIndex = 0;

  // Embedding history for temporal context (openWakeWord uses ~75 frames)
  private embeddingHistory: Float32Array[] = [];
  private readonly EMBEDDING_HISTORY_SIZE = 75;

  // VAD state
  private vadState: VADState = {
    isSpeaking: false,
    confidence: 0,
    duration: 0
  };
  private speechStartTime = 0;

  // ONNX session options
  private readonly sessionOptions: ort.InferenceSession.SessionOptions = {
    executionProviders: ['cpu'],
    graphOptimizationLevel: 'all'
  };

  constructor(config: WakeWordConfig) {
    this.config = {
      modelsPath: config.modelsPath,
      keywords: config.keywords,
      detectionThreshold: config.detectionThreshold ?? 0.5,
      cooldownMs: config.cooldownMs ?? 2000,
      enableVAD: config.enableVAD ?? true,
      vadThreshold: config.vadThreshold ?? 0.5,
      sampleRate: config.sampleRate ?? 16000,
      frameSize: config.frameSize ?? 1280, // 80ms at 16kHz
      debug: config.debug ?? false
    };

    this.audioBuffer = new Float32Array(this.config.frameSize);
  }

  /**
   * Initialize the wake word detector by loading all required models
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      this.log('Already initialized');
      return;
    }

    this.log('Initializing wake word detector...');

    // Validate models directory exists
    if (!fs.existsSync(this.config.modelsPath)) {
      throw new Error(`Models directory not found: ${this.config.modelsPath}`);
    }

    // Load core models
    await this.loadCoreModels();

    // Load keyword models
    await this.loadKeywordModels();

    this.isInitialized = true;
    this.emit({ type: 'ready' });
    this.log('Wake word detector initialized successfully');
  }

  private async loadCoreModels(): Promise<void> {
    // Load melspectrogram model
    const melPath = path.join(this.config.modelsPath, REQUIRED_MODELS.melspectrogram);
    if (!fs.existsSync(melPath)) {
      throw new Error(`Melspectrogram model not found: ${melPath}`);
    }
    this.melSession = await ort.InferenceSession.create(melPath, this.sessionOptions);
    this.log('Loaded melspectrogram model');

    // Load embedding model
    const embPath = path.join(this.config.modelsPath, REQUIRED_MODELS.embedding);
    if (!fs.existsSync(embPath)) {
      throw new Error(`Embedding model not found: ${embPath}`);
    }
    this.embeddingSession = await ort.InferenceSession.create(embPath, this.sessionOptions);
    this.log('Loaded embedding model');

    // Load VAD model if enabled
    if (this.config.enableVAD) {
      const vadPath = path.join(this.config.modelsPath, REQUIRED_MODELS.vad);
      if (!fs.existsSync(vadPath)) {
        this.log('VAD model not found, disabling VAD');
        this.config.enableVAD = false;
      } else {
        this.vadSession = await ort.InferenceSession.create(vadPath, this.sessionOptions);
        this.log('Loaded VAD model');
      }
    }
  }

  private async loadKeywordModels(): Promise<void> {
    for (const keyword of this.config.keywords) {
      // Try different naming conventions
      const possibleNames = [
        `${keyword}.onnx`,
        `${keyword}_v0.1.onnx`,
        `${keyword.replace('_', '-')}.onnx`
      ];

      let loaded = false;
      for (const fileName of possibleNames) {
        const modelPath = path.join(this.config.modelsPath, fileName);
        if (fs.existsSync(modelPath)) {
          const session = await ort.InferenceSession.create(modelPath, this.sessionOptions);
          this.keywordSessions.set(keyword, session);
          this.log(`Loaded keyword model: ${keyword}`);
          loaded = true;
          break;
        }
      }

      if (!loaded) {
        throw new Error(
          `Keyword model not found for "${keyword}". ` +
          `Expected one of: ${possibleNames.join(', ')} in ${this.config.modelsPath}`
        );
      }
    }
  }

  /**
   * Process an audio frame and check for wake words
   */
  async processAudioFrame(samples: Float32Array | Int16Array): Promise<WakeWordDetection | null> {
    if (!this.isInitialized) {
      throw new Error('Detector not initialized. Call initialize() first.');
    }

    // Convert Int16 to Float32 if necessary
    const floatSamples = samples instanceof Int16Array
      ? this.int16ToFloat32(samples)
      : samples;

    // Add samples to buffer
    for (let i = 0; i < floatSamples.length; i++) {
      this.audioBuffer[this.bufferIndex++] = floatSamples[i];

      // Process complete frame
      if (this.bufferIndex >= this.config.frameSize) {
        const detection = await this.processCompleteFrame(this.audioBuffer);
        this.bufferIndex = 0;
        this.framesProcessed++;

        if (detection) {
          return detection;
        }
      }
    }

    return null;
  }

  private async processCompleteFrame(frame: Float32Array): Promise<WakeWordDetection | null> {
    try {
      // Step 1: Compute melspectrogram
      const melspec = await this.computeMelspectrogram(frame);

      // Step 2: Compute embedding
      const embedding = await this.computeEmbedding(melspec);

      // Add to history
      this.embeddingHistory.push(embedding);
      if (this.embeddingHistory.length > this.EMBEDDING_HISTORY_SIZE) {
        this.embeddingHistory.shift();
      }

      // Step 3: Run VAD if enabled
      if (this.config.enableVAD && this.vadSession) {
        await this.runVAD(frame);
      }

      // Step 4: Check keywords (need enough embedding history)
      if (this.embeddingHistory.length >= this.EMBEDDING_HISTORY_SIZE) {
        return await this.checkKeywords();
      }

      return null;
    } catch (error) {
      this.emit({ type: 'error', data: error as Error });
      return null;
    }
  }

  private async computeMelspectrogram(frame: Float32Array): Promise<Float32Array> {
    if (!this.melSession) {
      throw new Error('Melspectrogram session not loaded');
    }

    // Create input tensor
    const inputTensor = new ort.Tensor('float32', frame, [1, frame.length]);

    // Run inference
    const results = await this.melSession.run({ input: inputTensor });

    // Get output (shape depends on model, typically [1, n_mels, time_steps])
    const outputName = this.melSession.outputNames[0];
    const output = results[outputName];

    return output.data as Float32Array;
  }

  private async computeEmbedding(melspec: Float32Array): Promise<Float32Array> {
    if (!this.embeddingSession) {
      throw new Error('Embedding session not loaded');
    }

    // Create input tensor - shape depends on the model's expected input
    // openWakeWord embedding model typically expects [batch, time, n_mels]
    const inputTensor = new ort.Tensor('float32', melspec, [1, melspec.length / 32, 32]);

    // Run inference
    const results = await this.embeddingSession.run({ input: inputTensor });

    const outputName = this.embeddingSession.outputNames[0];
    const output = results[outputName];

    return output.data as Float32Array;
  }

  private async runVAD(frame: Float32Array): Promise<void> {
    if (!this.vadSession) return;

    try {
      // Silero VAD expects specific input format
      const inputTensor = new ort.Tensor('float32', frame, [1, frame.length]);

      // Run VAD inference
      const results = await this.vadSession.run({ input: inputTensor });

      const outputName = this.vadSession.outputNames[0];
      const probability = (results[outputName].data as Float32Array)[0];

      const wasSpeaking = this.vadState.isSpeaking;
      this.vadState.confidence = probability;
      this.vadState.isSpeaking = probability >= this.config.vadThreshold;

      if (this.vadState.isSpeaking) {
        if (!wasSpeaking) {
          this.speechStartTime = Date.now();
          this.emit({ type: 'speech-start', data: { ...this.vadState } });
        }
        this.vadState.duration = Date.now() - this.speechStartTime;
      } else if (wasSpeaking) {
        this.emit({ type: 'speech-end', data: { ...this.vadState } });
        this.vadState.duration = 0;
      }
    } catch (error) {
      // VAD errors are non-fatal
      this.log(`VAD error: ${error}`);
    }
  }

  private async checkKeywords(): Promise<WakeWordDetection | null> {
    // Prepare embedding history as input
    const embeddingSize = this.embeddingHistory[0].length;
    const historyData = new Float32Array(this.EMBEDDING_HISTORY_SIZE * embeddingSize);

    for (let i = 0; i < this.EMBEDDING_HISTORY_SIZE; i++) {
      historyData.set(this.embeddingHistory[i], i * embeddingSize);
    }

    const now = Date.now();
    let bestDetection: WakeWordDetection | null = null;

    for (const [keyword, session] of this.keywordSessions) {
      // Check cooldown
      const lastDetection = this.lastDetectionTime.get(keyword) ?? 0;
      if (now - lastDetection < this.config.cooldownMs) {
        continue;
      }

      try {
        // Create input tensor for keyword model
        const inputTensor = new ort.Tensor(
          'float32',
          historyData,
          [1, this.EMBEDDING_HISTORY_SIZE, embeddingSize]
        );

        // Run keyword detection
        const results = await session.run({ input: inputTensor });

        const outputName = session.outputNames[0];
        const score = (results[outputName].data as Float32Array)[0];

        if (score >= this.config.detectionThreshold) {
          const detection: WakeWordDetection = {
            keyword,
            score,
            timestamp: now,
            frameIndex: this.framesProcessed
          };

          this.lastDetectionTime.set(keyword, now);
          this.log(`Detected "${keyword}" with score ${score.toFixed(3)}`);

          if (!bestDetection || score > bestDetection.score) {
            bestDetection = detection;
          }
        }
      } catch (error) {
        this.log(`Error checking keyword "${keyword}": ${error}`);
      }
    }

    if (bestDetection) {
      this.emit({ type: 'detect', data: bestDetection });
    }

    return bestDetection;
  }

  /**
   * Start listening for wake words
   */
  start(): void {
    if (!this.isInitialized) {
      throw new Error('Detector not initialized. Call initialize() first.');
    }
    this.isListening = true;
    this.log('Started listening for wake words');
  }

  /**
   * Stop listening for wake words
   */
  stop(): void {
    this.isListening = false;
    this.log('Stopped listening for wake words');
  }

  /**
   * Check if detector is currently listening
   */
  get listening(): boolean {
    return this.isListening;
  }

  /**
   * Get current engine state
   */
  getState(): WakeWordEngineState {
    const models: ModelInfo[] = [
      {
        name: 'melspectrogram',
        path: path.join(this.config.modelsPath, REQUIRED_MODELS.melspectrogram),
        loaded: this.melSession !== null,
        type: 'melspectrogram'
      },
      {
        name: 'embedding',
        path: path.join(this.config.modelsPath, REQUIRED_MODELS.embedding),
        loaded: this.embeddingSession !== null,
        type: 'embedding'
      },
      {
        name: 'vad',
        path: path.join(this.config.modelsPath, REQUIRED_MODELS.vad),
        loaded: this.vadSession !== null,
        type: 'vad'
      }
    ];

    for (const keyword of this.config.keywords) {
      models.push({
        name: keyword,
        path: path.join(this.config.modelsPath, `${keyword}.onnx`),
        loaded: this.keywordSessions.has(keyword),
        type: 'keyword'
      });
    }

    return {
      initialized: this.isInitialized,
      listening: this.isListening,
      models,
      vadState: { ...this.vadState },
      framesProcessed: this.framesProcessed
    };
  }

  /**
   * Add event listener
   */
  on(callback: WakeWordCallback): void {
    this.listeners.push(callback);
  }

  /**
   * Remove event listener
   */
  off(callback: WakeWordCallback): void {
    const index = this.listeners.indexOf(callback);
    if (index !== -1) {
      this.listeners.splice(index, 1);
    }
  }

  private emit(event: WakeWordEvent): void {
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch (error) {
        console.error('Error in wake word event listener:', error);
      }
    }
  }

  /**
   * Clean up resources
   */
  async dispose(): Promise<void> {
    this.stop();

    await this.melSession?.release();
    await this.embeddingSession?.release();
    await this.vadSession?.release();

    for (const session of this.keywordSessions.values()) {
      await session.release();
    }

    this.keywordSessions.clear();
    this.melSession = null;
    this.embeddingSession = null;
    this.vadSession = null;
    this.isInitialized = false;
    this.embeddingHistory = [];

    this.log('Wake word detector disposed');
  }

  private int16ToFloat32(int16: Int16Array): Float32Array {
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) {
      float32[i] = int16[i] / 32768.0;
    }
    return float32;
  }

  private log(message: string): void {
    if (this.config.debug) {
      console.log(`[WakeWord] ${message}`);
    }
  }
}
