/**
 * Wake Word Detection Example
 *
 * Demonstrates using wake word detection in a Node.js/Electron environment.
 * This example shows the complete flow from wake word detection to listening for commands.
 */

import * as path from 'path';
import * as readline from 'readline';
import { WakeWordDetector } from './wake-word-detector';
import { NodeAudioInput } from './audio-input';
import { WakeWordEvent, WakeWordDetection } from './types';

// Configuration
const MODELS_PATH = path.join(__dirname, '..', 'models');
const KEYWORD = 'hey_jarvis'; // Change to your preferred wake word

// State
let isListeningForCommand = false;
let commandTimeout: NodeJS.Timeout | null = null;
const COMMAND_TIMEOUT_MS = 5000; // Listen for 5 seconds after wake word

async function main() {
  console.log('='.repeat(60));
  console.log('   Wake Word Detection Example');
  console.log('='.repeat(60));
  console.log();
  console.log(`Wake word: "${KEYWORD}"`);
  console.log(`Models path: ${MODELS_PATH}`);
  console.log();

  // Check for models
  const fs = await import('fs');
  if (!fs.existsSync(MODELS_PATH)) {
    console.log('Models not found. Please run: npm run download-models');
    console.log();
    console.log('Or download models manually from:');
    console.log('https://github.com/dscripka/openWakeWord/tree/main/openwakeword/resources/models');
    process.exit(1);
  }

  // Create wake word detector
  const detector = new WakeWordDetector({
    modelsPath: MODELS_PATH,
    keywords: [KEYWORD],
    detectionThreshold: 0.5,
    cooldownMs: 2000,
    enableVAD: true,
    debug: true
  });

  // Create audio input
  const audioInput = new NodeAudioInput({
    sampleRate: 16000
  });

  // Handle wake word events
  detector.on((event: WakeWordEvent) => {
    switch (event.type) {
      case 'ready':
        console.log('\n✓ Wake word detector ready');
        console.log(`\nSay "${KEYWORD}" to activate...`);
        break;

      case 'detect':
        handleWakeWordDetected(event.data as WakeWordDetection);
        break;

      case 'speech-start':
        if (!isListeningForCommand) {
          console.log('  [Speech detected]');
        }
        break;

      case 'speech-end':
        if (isListeningForCommand) {
          console.log('  [Speech ended - processing command...]');
          // In a real app, you would send the recorded audio to a speech-to-text service
        }
        break;

      case 'error':
        console.error('Error:', event.data);
        break;
    }
  });

  // Handle audio input events
  audioInput.on('start', () => {
    console.log('✓ Audio input started');
  });

  audioInput.on('error', (error) => {
    console.error('Audio input error:', error.message);
    console.log('\nMake sure you have a microphone connected and audio recording tools installed.');
    console.log('On Linux, install: sudo apt-get install alsa-utils');
    process.exit(1);
  });

  // Connect audio to detector
  audioInput.onAudio(async (samples) => {
    if (detector.listening) {
      await detector.processAudioFrame(samples);
    }
  });

  // Initialize detector
  try {
    console.log('Initializing wake word detector...');
    await detector.initialize();
  } catch (error) {
    console.error('Failed to initialize detector:', error);
    console.log('\nMake sure you have downloaded the required models.');
    process.exit(1);
  }

  // Start listening
  try {
    detector.start();
    await audioInput.start();
  } catch (error) {
    console.error('Failed to start audio input:', error);
    process.exit(1);
  }

  // Handle graceful shutdown
  const cleanup = async () => {
    console.log('\nShutting down...');
    audioInput.stop();
    await detector.dispose();
    process.exit(0);
  };

  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);

  // Keep process alive
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  console.log('\nPress Ctrl+C to exit\n');

  rl.on('close', cleanup);
}

function handleWakeWordDetected(detection: WakeWordDetection) {
  console.log();
  console.log('═'.repeat(40));
  console.log(`  🎤 Wake word detected: "${detection.keyword}"`);
  console.log(`     Confidence: ${(detection.score * 100).toFixed(1)}%`);
  console.log('═'.repeat(40));
  console.log();

  // Start listening for command
  isListeningForCommand = true;
  console.log('  Listening for your command...');

  // Clear any existing timeout
  if (commandTimeout) {
    clearTimeout(commandTimeout);
  }

  // Set timeout to stop listening for command
  commandTimeout = setTimeout(() => {
    if (isListeningForCommand) {
      isListeningForCommand = false;
      console.log('  [Command timeout - returning to wake word listening]');
      console.log();
      console.log(`Say "${KEYWORD}" to activate...`);
    }
  }, COMMAND_TIMEOUT_MS);
}

// Run example
main().catch(console.error);
