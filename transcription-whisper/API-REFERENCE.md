# API Reference

Quick reference for all three whisper.cpp integration approaches.

## nodejs-whisper

### Basic Usage

```typescript
import { nodewhisper } from 'nodejs-whisper';

const result = await nodewhisper(filePath, options);
```

### Options

```typescript
interface NodeWhisperOptions {
  // Model configuration
  modelName?: string;                    // Default: 'base.en'
  autoDownloadModelName?: string;        // Auto-download if missing

  // Processing
  removeWavFileAfterTranscription?: boolean;  // Default: false
  withCuda?: boolean;                    // Enable CUDA GPU acceleration

  // Logger
  logger?: Console;                      // Logger instance

  // Whisper-specific options
  whisperOptions?: {
    outputInText?: boolean;              // Output as .txt
    outputInVtt?: boolean;               // Output as .vtt
    outputInSrt?: boolean;               // Output as .srt
    outputInCsv?: boolean;               // Output as .csv
    translateToEnglish?: boolean;        // Translate to English
    language?: string;                   // Input language ('en', 'es', etc.)
    wordTimestamps?: boolean;            // Include word timestamps
    timestamps_length?: number;          // Timestamp segment length
    splitOnWord?: boolean;               // Split on word boundaries
  };
}
```

### Return Value

```typescript
interface NodeWhisperResult {
  text?: string;                         // Full transcription text
  srt?: string;                          // SRT format output
  vtt?: string;                          // VTT format output
  csv?: string;                          // CSV format output
}
```

### Example

```typescript
const result = await nodewhisper('audio.wav', {
  modelName: 'base.en',
  autoDownloadModelName: 'base.en',
  logger: console,
  whisperOptions: {
    language: 'en',
    wordTimestamps: true,
    outputInSrt: true,
  },
});

console.log(result.text);  // Full transcription
console.log(result.srt);   // SRT subtitles
```

---

## whisper-node

### Basic Usage

```typescript
import whisper from 'whisper-node';

const transcript = await whisper(filePath, options);
```

### Options

```typescript
interface WhisperNodeOptions {
  modelName: string;                     // Required: model to use
  whisperOptions?: {
    language?: string;                   // Language or 'auto'
    gen_file_txt?: boolean;              // Generate .txt file
    gen_file_subtitle?: boolean;         // Generate subtitle file
    gen_file_vtt?: boolean;              // Generate .vtt file
    word_timestamps?: boolean;           // Word-level timestamps
    timestamp_size?: number;             // Timestamp segment size
  };
}
```

### Return Value

```typescript
interface TranscriptionSegment {
  start: string;                         // Start time (e.g., "00:00:00")
  end: string;                           // End time
  speech: string;                        // Transcribed text
}

type WhisperNodeResult = TranscriptionSegment[];
```

### Example

```typescript
const transcript = await whisper('audio.wav', {
  modelName: 'base.en',
  whisperOptions: {
    language: 'en',
    word_timestamps: true,
  },
});

transcript.forEach(segment => {
  console.log(`[${segment.start} --> ${segment.end}]`);
  console.log(segment.speech);
});
```

---

## Official Addon

### Basic Usage

```typescript
import { promisify } from 'util';
const { whisper } = require('./path/to/addon.node');
const whisperAsync = promisify(whisper);

const result = await whisperAsync(params);
```

### Parameters

```typescript
interface WhisperParams {
  // Required
  language: string;                      // Language code
  model: string;                         // Path to model file
  fname_inp: string;                     // Path to audio file

  // Core options
  use_gpu?: boolean;                     // Enable GPU (default: true)
  flash_attn?: boolean;                  // Flash attention (default: false)
  no_prints?: boolean;                   // Disable console output
  no_timestamps?: boolean;               // Disable timestamps
  detect_language?: boolean;             // Auto-detect language

  // Advanced options
  audio_ctx?: number;                    // Audio context size
  max_len?: number;                      // Max segment length
  max_context?: number;                  // Max context size
  prompt?: string;                       // Initial decoder prompt
  comma_in_time?: boolean;               // Comma in timestamps
  print_progress?: boolean;              // Print progress

  // Callbacks
  progress_callback?: (progress: number) => void;

  // Voice Activity Detection (VAD)
  vad?: boolean;                         // Enable VAD
  vad_model?: string;                    // Path to VAD model
  vad_threshold?: number;                // Speech threshold (0.0-1.0)
  vad_min_speech_duration_ms?: number;   // Min speech duration
  vad_min_silence_duration_ms?: number;  // Min silence duration
  vad_max_speech_duration_s?: number;    // Max speech duration
  vad_speech_pad_ms?: number;            // Speech padding
  vad_samples_overlap?: number;          // Sample overlap (0.0-1.0)
}
```

### Return Value

```typescript
interface WhisperResult {
  text: string;                          // Full transcription
  segments?: Array<{
    start: number;                       // Start time (seconds)
    end: number;                         // End time (seconds)
    text: string;                        // Segment text
  }>;
}
```

### Basic Example

```typescript
const result = await whisperAsync({
  language: 'en',
  model: './models/ggml-base.en.bin',
  fname_inp: './audio.wav',
  use_gpu: true,
  progress_callback: (progress) => {
    console.log(`Progress: ${progress}%`);
  },
});

console.log(result.text);
```

### VAD Example

```typescript
const result = await whisperAsync({
  language: 'en',
  model: './models/ggml-base.en.bin',
  fname_inp: './audio.wav',

  // Enable VAD for faster processing
  vad: true,
  vad_model: './models/ggml-silero-v6.2.0.bin',
  vad_threshold: 0.5,
  vad_min_speech_duration_ms: 250,
  vad_min_silence_duration_ms: 100,
  vad_speech_pad_ms: 30,

  progress_callback: (progress) => {
    console.log(`Progress: ${progress}%`);
  },
});
```

---

## Language Codes

Common language codes for the `language` parameter:

| Code | Language |
|------|----------|
| `en` | English |
| `es` | Spanish |
| `fr` | French |
| `de` | German |
| `it` | Italian |
| `pt` | Portuguese |
| `nl` | Dutch |
| `pl` | Polish |
| `ru` | Russian |
| `ja` | Japanese |
| `zh` | Chinese |
| `ko` | Korean |
| `ar` | Arabic |
| `hi` | Hindi |
| `auto` | Auto-detect (whisper-node only) |

Full list: https://github.com/openai/whisper#available-models-and-languages

---

## Model Names

| Model | English-only | Multilingual | Size |
|-------|--------------|--------------|------|
| Tiny | `tiny.en` | `tiny` | ~75 MB |
| Base | `base.en` | `base` | ~142 MB |
| Small | `small.en` | `small` | ~466 MB |
| Medium | `medium.en` | `medium` | ~1.5 GB |
| Large | - | `large-v3` | ~2.9 GB |

**Recommendation:** Use `base.en` for English audio as a good balance between speed and accuracy.

---

## Error Handling

### nodejs-whisper

```typescript
try {
  const result = await nodewhisper(filePath, options);
} catch (error) {
  if (error.message.includes('Model not found')) {
    console.error('Model needs to be downloaded');
  } else if (error.message.includes('Audio file')) {
    console.error('Invalid audio file format');
  } else {
    console.error('Transcription error:', error);
  }
}
```

### whisper-node

```typescript
try {
  const transcript = await whisper(filePath, options);
} catch (error) {
  console.error('Transcription failed:', error);
  // Errors are typically related to:
  // - Missing model
  // - Invalid audio format
  // - Insufficient memory
}
```

### Official Addon

```typescript
try {
  const result = await whisperAsync(params);
} catch (error) {
  if (error.code === 'MODULE_NOT_FOUND') {
    console.error('Addon not built - run compilation first');
  } else {
    console.error('Transcription error:', error);
  }
}
```

---

## Performance Comparison

| Package | Setup Time | Transcription Speed | Features |
|---------|-----------|---------------------|----------|
| nodejs-whisper | Fast | Medium | Auto-download, SRT output |
| whisper-node | Fast | Medium | Simple API, auto-download |
| Official Addon | Slow (build) | Fast | Latest features, VAD, GPU |

**Speed benchmark (60s audio, base.en model, CPU):**
- nodejs-whisper: ~30-60s
- whisper-node: ~30-60s
- Official addon: ~20-40s
- Official addon + VAD: ~10-20s
- Official addon + GPU: ~5-10s

*Actual speeds vary by hardware and audio complexity*
