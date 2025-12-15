/**
 * Example using the official whisper.cpp addon.node
 * Requires manually building whisper.cpp from source
 *
 * Setup:
 * 1. Clone whisper.cpp: git clone https://github.com/ggml-org/whisper.cpp
 * 2. Navigate to examples/addon.node
 * 3. Build: npm install && npx cmake-js compile -T addon.node -B Release
 * 4. Copy the built addon to your project or adjust the path below
 */

import path from 'path';
import { promisify } from 'util';

interface WhisperParams {
  language: string;
  model: string;
  fname_inp: string;
  use_gpu?: boolean;
  flash_attn?: boolean;
  no_prints?: boolean;
  no_timestamps?: boolean;
  detect_language?: boolean;
  audio_ctx?: number;
  max_len?: number;
  max_context?: number;
  prompt?: string;
  comma_in_time?: boolean;
  print_progress?: boolean;
  progress_callback?: (progress: number) => void;

  // Voice Activity Detection (VAD) options
  vad?: boolean;
  vad_model?: string;
  vad_threshold?: number;
  vad_min_speech_duration_ms?: number;
  vad_min_silence_duration_ms?: number;
  vad_max_speech_duration_s?: number;
  vad_speech_pad_ms?: number;
  vad_samples_overlap?: number;
}

interface WhisperResult {
  text: string;
  segments?: Array<{
    start: number;
    end: number;
    text: string;
  }>;
}

async function transcribeWithOfficialAddon() {
  console.log('Starting transcription with official whisper.cpp addon...\n');

  try {
    // Load the official addon (adjust path to where you built it)
    // This will throw an error if not built - see instructions at top of file
    const addonPath = path.join(
      __dirname,
      '../../../whisper.cpp/build/Release/addon.node'
    );

    console.log(`Looking for addon at: ${addonPath}`);

    // Import the addon
    const { whisper } = require(addonPath);
    const whisperAsync = promisify(whisper) as (params: WhisperParams) => Promise<WhisperResult>;

    // Configuration
    const params: WhisperParams = {
      language: 'en',
      model: path.join(__dirname, '../../../whisper.cpp/models/ggml-base.en.bin'),
      fname_inp: path.resolve(__dirname, '../examples/sample-audio.wav'),
      use_gpu: true,                  // Enable GPU acceleration if available
      flash_attn: false,              // Enable flash attention
      no_prints: false,               // Disable console output
      no_timestamps: false,           // Disable timestamps
      detect_language: false,         // Auto-detect language
      comma_in_time: true,           // Use comma in timestamps
      print_progress: true,           // Print progress
      progress_callback: (progress: number) => {
        console.log(`Progress: ${progress.toFixed(1)}%`);
      },
    };

    console.log('Transcription parameters:');
    console.log(`  Model: ${params.model}`);
    console.log(`  Audio: ${params.fname_inp}`);
    console.log(`  Language: ${params.language}`);
    console.log(`  GPU: ${params.use_gpu}\n`);

    const result = await whisperAsync(params);

    console.log('\nTranscription completed!');
    console.log('Result:', JSON.stringify(result, null, 2));

    return result;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'MODULE_NOT_FOUND') {
      console.error('\n❌ Error: Official addon not found!');
      console.error('\nTo use the official addon, you need to:');
      console.error('1. Clone whisper.cpp: git clone https://github.com/ggml-org/whisper.cpp');
      console.error('2. cd whisper.cpp/examples/addon.node');
      console.error('3. npm install');
      console.error('4. npx cmake-js compile -T addon.node -B Release');
      console.error('5. Download a model: bash ../../models/download-ggml-model.sh base.en');
      console.error('\nAlternatively, use one of the npm packages (nodejs-whisper or whisper-node)');
    } else {
      console.error('Error during transcription:', error);
    }
    throw error;
  }
}

async function transcribeWithVAD() {
  console.log('Starting transcription with VAD (Voice Activity Detection)...\n');

  try {
    const addonPath = path.join(
      __dirname,
      '../../../whisper.cpp/build/Release/addon.node'
    );

    const { whisper } = require(addonPath);
    const whisperAsync = promisify(whisper) as (params: WhisperParams) => Promise<WhisperResult>;

    // VAD significantly improves performance by processing only speech segments
    const params: WhisperParams = {
      language: 'en',
      model: path.join(__dirname, '../../../whisper.cpp/models/ggml-base.en.bin'),
      fname_inp: path.resolve(__dirname, '../examples/sample-audio.wav'),

      // Enable VAD
      vad: true,
      vad_model: path.join(__dirname, '../../../whisper.cpp/models/ggml-silero-v6.2.0.bin'),
      vad_threshold: 0.5,                    // Speech detection threshold (0.0-1.0)
      vad_min_speech_duration_ms: 250,       // Minimum speech duration
      vad_min_silence_duration_ms: 100,      // Minimum silence duration
      vad_speech_pad_ms: 30,                 // Speech padding
      vad_samples_overlap: 0.1,              // Sample overlap (0.0-1.0)

      progress_callback: (progress: number) => {
        console.log(`Progress: ${progress.toFixed(1)}%`);
      },
    };

    console.log('Transcription with VAD enabled...\n');

    const result = await whisperAsync(params);

    console.log('\nTranscription completed!');
    console.log('Result:', JSON.stringify(result, null, 2));

    return result;
  } catch (error) {
    console.error('Error during transcription with VAD:', error);
    throw error;
  }
}

// Run the example
if (require.main === module) {
  transcribeWithOfficialAddon()
    .then(() => {
      console.log('\nTranscription finished successfully!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\nTranscription failed:', error);
      process.exit(1);
    });
}

export { transcribeWithOfficialAddon, transcribeWithVAD };
