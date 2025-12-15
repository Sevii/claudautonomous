/**
 * Whisper.cpp TypeScript Examples
 *
 * This module provides examples of using whisper.cpp for local audio transcription
 * using different Node.js bindings and approaches.
 */

export { transcribeWithNodeJsWhisper } from './example-nodejs-whisper';
export { transcribeWithWhisperNode } from './example-whisper-node';
export { transcribeWithOfficialAddon, transcribeWithVAD } from './example-official-addon';

/**
 * Supported audio formats:
 * - WAV (PCM 16-bit)
 * - MP3
 * - MP4/M4A
 * - OGG
 * - FLAC
 *
 * Note: Audio is internally converted to 16kHz mono for processing
 */

/**
 * Available Whisper models (by size and performance):
 *
 * - tiny.en / tiny      (~75 MB)  - Fastest, least accurate
 * - base.en / base      (~142 MB) - Good balance for most use cases
 * - small.en / small    (~466 MB) - Better accuracy
 * - medium.en / medium  (~1.5 GB) - High accuracy
 * - large               (~2.9 GB) - Best accuracy, slowest
 *
 * Models with .en suffix are English-only and faster for English audio
 */
