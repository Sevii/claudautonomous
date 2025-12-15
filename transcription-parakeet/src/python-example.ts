/**
 * Example usage of the Python wrapper for Parakeet transcription
 */

import { PythonParakeetTranscriber } from './python-wrapper.js';
import { resolve } from 'path';

async function main() {
  console.log('=== Parakeet Transcription Example (Python Wrapper) ===\n');

  // Create transcriber instance
  const transcriber = new PythonParakeetTranscriber();

  // Check if dependencies are available
  console.log('Checking Python dependencies...');
  const depsAvailable = await transcriber.checkDependencies();

  if (!depsAvailable) {
    console.error('❌ Python dependencies not available!');
    console.error('\nPlease install required packages:');
    console.error('  pip install nemo_toolkit[asr]\n');
    process.exit(1);
  }

  console.log('✓ Python dependencies OK\n');

  // Example audio file path
  // Replace with your actual audio file
  const audioPath = process.argv[2] || resolve(process.cwd(), 'examples', 'sample.wav');

  try {
    console.log(`Transcribing: ${audioPath}`);
    console.log('(This may take a moment...)\n');

    // Basic transcription
    const result = await transcriber.transcribe({
      audioPath,
      includeTimestamps: false,
    });

    console.log('=== Transcription Result ===');
    console.log(result.text);
    console.log('');

    // Transcription with timestamps
    console.log('Transcribing with timestamps...\n');
    const resultWithTimestamps = await transcriber.transcribe({
      audioPath,
      includeTimestamps: true,
    });

    console.log('=== Transcription with Timestamps ===');
    console.log('Text:', resultWithTimestamps.text);
    console.log('\nWord Timestamps:');

    if (resultWithTimestamps.timestamps) {
      resultWithTimestamps.timestamps.forEach((ts, idx) => {
        console.log(`  ${idx + 1}. "${ts.word}" [${ts.start.toFixed(2)}s - ${ts.end.toFixed(2)}s]`);
      });
    }

  } catch (error) {
    console.error('Error during transcription:', error);
    process.exit(1);
  }
}

main();
