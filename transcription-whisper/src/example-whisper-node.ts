/**
 * Example using whisper-node package
 * Popular Node.js bindings with good community support
 */

import path from 'path';
// @ts-ignore - whisper-node doesn't have official TypeScript definitions
import whisper from 'whisper-node';

interface WhisperOptions {
  modelName: string;
  whisperOptions?: {
    language?: string;
    gen_file_txt?: boolean;
    gen_file_subtitle?: boolean;
    gen_file_vtt?: boolean;
    word_timestamps?: boolean;
    timestamp_size?: number;
  };
}

interface TranscriptionSegment {
  start: string;
  end: string;
  speech: string;
}

async function transcribeWithWhisperNode() {
  console.log('Starting transcription with whisper-node...\n');

  // Path to your audio file
  const audioFilePath = path.resolve(__dirname, '../examples/sample-audio.wav');

  const options: WhisperOptions = {
    modelName: 'base.en',  // Available: tiny, tiny.en, base, base.en, small, medium, large
    whisperOptions: {
      language: 'en',              // Language code (or 'auto' for auto-detection)
      gen_file_txt: false,         // Generate text file
      gen_file_subtitle: false,    // Generate subtitle file
      gen_file_vtt: false,         // Generate VTT file
      word_timestamps: true,       // Include word-level timestamps
      timestamp_size: 20,          // Timestamp segment size
    },
  };

  try {
    console.log(`Transcribing: ${audioFilePath}`);
    console.log(`Model: ${options.modelName}\n`);

    const transcript = await whisper(audioFilePath, options) as TranscriptionSegment[];

    console.log('Transcription completed!');
    console.log('Number of segments:', transcript.length);
    console.log('\nTranscript segments:');

    transcript.forEach((segment, index) => {
      console.log(`\n[${index + 1}] ${segment.start} --> ${segment.end}`);
      console.log(`    ${segment.speech}`);
    });

    return transcript;
  } catch (error) {
    console.error('Error during transcription:', error);
    throw error;
  }
}

// Run the example
if (require.main === module) {
  transcribeWithWhisperNode()
    .then(() => {
      console.log('\nTranscription finished successfully!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\nTranscription failed:', error);
      process.exit(1);
    });
}

export { transcribeWithWhisperNode };
