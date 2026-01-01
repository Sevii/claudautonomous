/**
 * Model Downloader
 *
 * Downloads openWakeWord ONNX models from the official repository.
 */

import * as https from 'https';
import * as fs from 'fs';
import * as path from 'path';

const MODELS_BASE_URL = 'https://github.com/dscripka/openWakeWord/raw/main/openwakeword/resources/models';

interface ModelDefinition {
  name: string;
  url: string;
  required: boolean;
}

const MODELS: ModelDefinition[] = [
  // Core models
  {
    name: 'melspectrogram.onnx',
    url: `${MODELS_BASE_URL}/melspectrogram.onnx`,
    required: true
  },
  {
    name: 'embedding_model.onnx',
    url: `${MODELS_BASE_URL}/embedding_model.onnx`,
    required: true
  },
  {
    name: 'silero_vad.onnx',
    url: 'https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.onnx',
    required: false
  },
  // Wake word models
  {
    name: 'alexa_v0.1.onnx',
    url: `${MODELS_BASE_URL}/alexa_v0.1.onnx`,
    required: false
  },
  {
    name: 'hey_jarvis_v0.1.onnx',
    url: `${MODELS_BASE_URL}/hey_jarvis_v0.1.onnx`,
    required: false
  },
  {
    name: 'hey_mycroft_v0.1.onnx',
    url: `${MODELS_BASE_URL}/hey_mycroft_v0.1.onnx`,
    required: false
  },
  {
    name: 'hey_rhasspy_v0.1.onnx',
    url: `${MODELS_BASE_URL}/hey_rhasspy_v0.1.onnx`,
    required: false
  }
];

async function downloadFile(url: string, destPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    console.log(`Downloading: ${path.basename(destPath)}`);

    const file = fs.createWriteStream(destPath);

    const request = (urlStr: string) => {
      https.get(urlStr, (response) => {
        // Handle redirects
        if (response.statusCode === 302 || response.statusCode === 301) {
          const redirectUrl = response.headers.location;
          if (redirectUrl) {
            request(redirectUrl);
            return;
          }
        }

        if (response.statusCode !== 200) {
          reject(new Error(`Failed to download: ${response.statusCode}`));
          return;
        }

        response.pipe(file);

        file.on('finish', () => {
          file.close();
          console.log(`  Downloaded: ${path.basename(destPath)}`);
          resolve();
        });
      }).on('error', (err) => {
        fs.unlink(destPath, () => {});
        reject(err);
      });
    };

    request(url);
  });
}

async function downloadModels(destDir: string, keywords: string[] = []): Promise<void> {
  // Create destination directory
  if (!fs.existsSync(destDir)) {
    fs.mkdirSync(destDir, { recursive: true });
  }

  console.log(`\nDownloading openWakeWord models to: ${destDir}\n`);

  // Determine which models to download
  const modelsToDownload = MODELS.filter(model => {
    // Always download required models
    if (model.required) return true;

    // Download keyword models if specified or download all if none specified
    if (keywords.length === 0) return true;

    return keywords.some(kw =>
      model.name.toLowerCase().includes(kw.toLowerCase().replace('_', '-')) ||
      model.name.toLowerCase().includes(kw.toLowerCase())
    );
  });

  // Download each model
  for (const model of modelsToDownload) {
    const destPath = path.join(destDir, model.name);

    // Skip if already exists
    if (fs.existsSync(destPath)) {
      console.log(`  Skipping (exists): ${model.name}`);
      continue;
    }

    try {
      await downloadFile(model.url, destPath);
    } catch (error) {
      if (model.required) {
        throw error;
      }
      console.log(`  Warning: Failed to download optional model ${model.name}: ${error}`);
    }
  }

  console.log('\nModel download complete!');
  console.log('\nNote: The "computer" wake word is not available as a pre-trained model.');
  console.log('You can train a custom model using the openWakeWord training notebook:');
  console.log('https://github.com/dscripka/openWakeWord/blob/main/notebooks/automatic_model_training.ipynb');
}

// Run if executed directly
if (require.main === module) {
  const destDir = process.argv[2] || path.join(__dirname, '..', 'models');
  const keywords = process.argv.slice(3);

  downloadModels(destDir, keywords)
    .then(() => process.exit(0))
    .catch((error) => {
      console.error('Error downloading models:', error);
      process.exit(1);
    });
}

export { downloadModels, MODELS };
