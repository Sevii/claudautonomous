/**
 * Example using nodejs-whisper package
 * This is a stable, production-ready option with TypeScript support
 */

import path from 'path';
import { nodewhisper } from 'nodejs-whisper';

async function transcribeWithNodeJsWhisper() {
  console.log('Starting transcription with nodejs-whisper...\n');

  // Path to your audio file (supports: wav, mp3, mp4, etc.)
  const audioFilePath = path.resolve(__dirname, '../examples/sample-audio.wav');

  try {
    const result = await nodewhisper(audioFilePath, {
      // Model options
      modelName: 'base.en',              // Model to use: tiny, base, small, medium, large
      autoDownloadModelName: 'base.en',   // Auto-download if model not found

      // Processing options
      removeWavFileAfterTranscription: false,
      withCuda: false,                    // Set to true for GPU acceleration (requires CUDA)

      // Logger
      logger: console,

      // Whisper options
      whisperOptions: {
        outputInText: false,              // Output in txt format
        outputInVtt: false,               // Output in vtt format
        outputInSrt: true,                // Output in srt format
        outputInCsv: false,               // Output in csv format
        translateToEnglish: false,        // Translate to English
        language: 'en',                   // Input language
        wordTimestamps: true,             // Include word-level timestamps
        timestamps_length: 20,            // Timestamp segment length
        splitOnWord: true,                // Split on word boundaries
      },
    });

    console.log('Transcription completed!');
    console.log('Result:', result);

    return result;
  } catch (error) {
    console.error('Error during transcription:', error);
    throw error;
  }
}

// Run the example
if (require.main === module) {
  transcribeWithNodeJsWhisper()
    .then(() => {
      console.log('\nTranscription finished successfully!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\nTranscription failed:', error);
      process.exit(1);
    });
}

export { transcribeWithNodeJsWhisper };
