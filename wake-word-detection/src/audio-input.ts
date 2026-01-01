/**
 * Audio Input Handling
 *
 * Provides microphone input capture for wake word detection.
 * Supports both Node.js (using node-record-lpcm16) and Electron renderer (Web Audio API).
 */

import { EventEmitter } from 'events';
import { spawn, ChildProcess } from 'child_process';

export interface AudioInputConfig {
  /** Sample rate in Hz, default 16000 */
  sampleRate?: number;

  /** Number of audio channels, default 1 (mono) */
  channels?: number;

  /** Bits per sample, default 16 */
  bitsPerSample?: number;

  /** Recording device name (platform specific) */
  device?: string;

  /** Audio gain multiplier, default 1.0 */
  gain?: number;

  /** Buffer size in samples per callback */
  bufferSize?: number;
}

export type AudioInputCallback = (samples: Int16Array) => void;

/**
 * Node.js audio input using system recording tools
 */
export class NodeAudioInput extends EventEmitter {
  private config: Required<AudioInputConfig>;
  private recordProcess: ChildProcess | null = null;
  private isRecording = false;
  private callbacks: AudioInputCallback[] = [];

  constructor(config: AudioInputConfig = {}) {
    super();
    this.config = {
      sampleRate: config.sampleRate ?? 16000,
      channels: config.channels ?? 1,
      bitsPerSample: config.bitsPerSample ?? 16,
      device: config.device ?? 'default',
      gain: config.gain ?? 1.0,
      bufferSize: config.bufferSize ?? 1280 // 80ms at 16kHz
    };
  }

  /**
   * Start recording from microphone
   */
  async start(): Promise<void> {
    if (this.isRecording) {
      return;
    }

    // Detect available recording tool
    const recorder = await this.detectRecorder();

    const args = this.getRecorderArgs(recorder);
    this.recordProcess = spawn(recorder, args);

    this.recordProcess.stdout?.on('data', (data: Buffer) => {
      const samples = this.bufferToInt16(data);
      this.emit('audio', samples);
      for (const callback of this.callbacks) {
        callback(samples);
      }
    });

    this.recordProcess.stderr?.on('data', (data: Buffer) => {
      // Some recorders output status to stderr
      const message = data.toString();
      if (!message.includes('Recording')) {
        this.emit('error', new Error(message));
      }
    });

    this.recordProcess.on('error', (error) => {
      this.emit('error', error);
    });

    this.recordProcess.on('close', (code) => {
      this.isRecording = false;
      if (code !== 0 && code !== null) {
        this.emit('error', new Error(`Recorder exited with code ${code}`));
      }
      this.emit('end');
    });

    this.isRecording = true;
    this.emit('start');
  }

  /**
   * Stop recording
   */
  stop(): void {
    if (this.recordProcess) {
      this.recordProcess.kill('SIGTERM');
      this.recordProcess = null;
    }
    this.isRecording = false;
  }

  /**
   * Add callback for audio data
   */
  onAudio(callback: AudioInputCallback): void {
    this.callbacks.push(callback);
  }

  /**
   * Remove audio callback
   */
  offAudio(callback: AudioInputCallback): void {
    const index = this.callbacks.indexOf(callback);
    if (index !== -1) {
      this.callbacks.splice(index, 1);
    }
  }

  get recording(): boolean {
    return this.isRecording;
  }

  private async detectRecorder(): Promise<string> {
    const recorders = ['arecord', 'sox', 'rec', 'ffmpeg'];

    for (const recorder of recorders) {
      try {
        const result = spawn('which', [recorder]);
        await new Promise<void>((resolve, reject) => {
          result.on('close', (code) => {
            if (code === 0) resolve();
            else reject(new Error(`${recorder} not found`));
          });
          result.on('error', reject);
        });
        return recorder;
      } catch {
        continue;
      }
    }

    throw new Error(
      'No audio recorder found. Please install one of: arecord (alsa-utils), sox, or ffmpeg'
    );
  }

  private getRecorderArgs(recorder: string): string[] {
    const { sampleRate, channels, device } = this.config;

    switch (recorder) {
      case 'arecord':
        return [
          '-D', device,
          '-c', channels.toString(),
          '-r', sampleRate.toString(),
          '-f', 'S16_LE',
          '-t', 'raw',
          '-'
        ];

      case 'sox':
      case 'rec':
        return [
          '-d',
          '-t', 'raw',
          '-b', '16',
          '-c', channels.toString(),
          '-r', sampleRate.toString(),
          '-e', 'signed-integer',
          '-'
        ];

      case 'ffmpeg':
        return [
          '-f', 'alsa',
          '-i', device,
          '-ar', sampleRate.toString(),
          '-ac', channels.toString(),
          '-f', 's16le',
          '-'
        ];

      default:
        throw new Error(`Unknown recorder: ${recorder}`);
    }
  }

  private bufferToInt16(buffer: Buffer): Int16Array {
    const samples = new Int16Array(buffer.length / 2);
    for (let i = 0; i < samples.length; i++) {
      samples[i] = buffer.readInt16LE(i * 2);
    }

    // Apply gain
    if (this.config.gain !== 1.0) {
      for (let i = 0; i < samples.length; i++) {
        samples[i] = Math.max(-32768, Math.min(32767, samples[i] * this.config.gain));
      }
    }

    return samples;
  }
}

/**
 * Electron Renderer Process Audio Input using Web Audio API
 *
 * This class is designed to be used in the Electron renderer process.
 * It uses the Web Audio API with AudioWorklet for efficient audio capture.
 */
export const ElectronRendererAudioInput = `
/**
 * Electron Renderer Audio Input
 *
 * Usage in renderer process:
 *
 * const audioInput = new ElectronRendererAudioInput({ sampleRate: 16000 });
 * await audioInput.start();
 * audioInput.onAudio((samples) => {
 *   // Send to main process via IPC for wake word detection
 *   window.electronAPI.processAudio(samples);
 * });
 */

class ElectronRendererAudioInput {
  constructor(config = {}) {
    this.config = {
      sampleRate: config.sampleRate || 16000,
      bufferSize: config.bufferSize || 1280,
      gain: config.gain || 1.0
    };
    this.audioContext = null;
    this.mediaStream = null;
    this.workletNode = null;
    this.callbacks = [];
    this.isRecording = false;
  }

  async start() {
    if (this.isRecording) return;

    // Request microphone access
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: this.config.sampleRate,
        echoCancellation: true,
        noiseSuppression: true
      }
    });

    // Create audio context
    this.audioContext = new AudioContext({
      sampleRate: this.config.sampleRate
    });

    // Register audio worklet processor
    const workletCode = \`
      class AudioCaptureProcessor extends AudioWorkletProcessor {
        constructor() {
          super();
          this.buffer = new Float32Array(${1280});
          this.bufferIndex = 0;
        }

        process(inputs, outputs, parameters) {
          const input = inputs[0];
          if (input.length > 0) {
            const samples = input[0];
            for (let i = 0; i < samples.length; i++) {
              this.buffer[this.bufferIndex++] = samples[i];
              if (this.bufferIndex >= this.buffer.length) {
                // Convert to Int16 for transmission
                const int16 = new Int16Array(this.buffer.length);
                for (let j = 0; j < this.buffer.length; j++) {
                  int16[j] = Math.max(-32768, Math.min(32767, Math.round(this.buffer[j] * 32767)));
                }
                this.port.postMessage(int16.buffer, [int16.buffer]);
                this.buffer = new Float32Array(${1280});
                this.bufferIndex = 0;
              }
            }
          }
          return true;
        }
      }

      registerProcessor('audio-capture-processor', AudioCaptureProcessor);
    \`;

    const blob = new Blob([workletCode], { type: 'application/javascript' });
    const url = URL.createObjectURL(blob);

    await this.audioContext.audioWorklet.addModule(url);

    // Create nodes
    const source = this.audioContext.createMediaStreamSource(this.mediaStream);
    this.workletNode = new AudioWorkletNode(this.audioContext, 'audio-capture-processor');

    // Handle audio data from worklet
    this.workletNode.port.onmessage = (event) => {
      const samples = new Int16Array(event.data);
      for (const callback of this.callbacks) {
        callback(samples);
      }
    };

    // Connect audio graph
    source.connect(this.workletNode);
    this.workletNode.connect(this.audioContext.destination);

    this.isRecording = true;
  }

  stop() {
    if (this.workletNode) {
      this.workletNode.disconnect();
      this.workletNode = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    this.isRecording = false;
  }

  onAudio(callback) {
    this.callbacks.push(callback);
  }

  offAudio(callback) {
    const index = this.callbacks.indexOf(callback);
    if (index !== -1) {
      this.callbacks.splice(index, 1);
    }
  }

  get recording() {
    return this.isRecording;
  }
}
`;

// Export the renderer code as a string for injection
export { ElectronRendererAudioInput };
