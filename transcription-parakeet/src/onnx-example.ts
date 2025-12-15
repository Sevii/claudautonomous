/**
 * Example usage of ONNX Runtime for Parakeet transcription
 *
 * NOTE: This is a placeholder implementation demonstrating the API structure.
 * For a working ONNX implementation, you would need to:
 * 1. Download the ONNX models from https://huggingface.co/onnx-community/parakeet-tdt-0.6b-v2-ONNX
 * 2. Implement audio preprocessing (see sherpa-onnx or onnx-asr for reference)
 * 3. Implement the TDT decoder logic
 */

import { ONNXParakeetTranscriber } from './onnx-transcriber.js';
import { resolve } from 'path';

async function main() {
  console.log('=== Parakeet Transcription Example (ONNX Runtime) ===\n');

  const transcriber = new ONNXParakeetTranscriber({
    encoderPath: resolve(process.cwd(), 'models', 'encoder.onnx'),
    decoderPath: resolve(process.cwd(), 'models', 'decoder.onnx'),
  });

  try {
    console.log('Initializing ONNX models...');
    await transcriber.initialize();

    const audioPath = process.argv[2] || resolve(process.cwd(), 'examples', 'sample.wav');

    const result = await transcriber.transcribe({
      audioPath,
      includeTimestamps: false,
    });

    console.log('Transcription:', result.text);

  } catch (error) {
    if (error instanceof Error) {
      console.error('\n❌ Error:', error.message);

      if (error.message.includes('Full ONNX implementation')) {
        console.log('\n📝 Note: For a working implementation, consider:');
        console.log('  1. Using the Python wrapper (recommended)');
        console.log('  2. Using sherpa-onnx library');
        console.log('  3. Implementing audio preprocessing with libraries like:');
        console.log('     - @tensorflow/tfjs-node (for audio processing)');
        console.log('     - node-audio (for reading audio files)');
        console.log('     - wav-decoder (for WAV file parsing)');
      }
    }
  } finally {
    await transcriber.dispose();
  }
}

main();
