/**
 * Wake Word Detection for Electron
 *
 * Main entry point and exports.
 */

export { WakeWordDetector } from './wake-word-detector';
export { NodeAudioInput, ElectronRendererAudioInput } from './audio-input';
export { downloadModels, MODELS } from './download-models';
export * from './types';

/**
 * Example usage:
 *
 * ```typescript
 * import { WakeWordDetector, NodeAudioInput } from 'wake-word-detection';
 *
 * // Create detector
 * const detector = new WakeWordDetector({
 *   modelsPath: './models',
 *   keywords: ['hey_jarvis'],
 *   detectionThreshold: 0.5,
 *   debug: true
 * });
 *
 * // Initialize
 * await detector.initialize();
 *
 * // Listen for events
 * detector.on((event) => {
 *   if (event.type === 'detect') {
 *     console.log('Wake word detected!', event.data);
 *   }
 * });
 *
 * // Create audio input
 * const audioInput = new NodeAudioInput();
 *
 * // Connect audio to detector
 * audioInput.onAudio(async (samples) => {
 *   await detector.processAudioFrame(samples);
 * });
 *
 * // Start listening
 * detector.start();
 * await audioInput.start();
 * ```
 */
