/**
 * Electron Integration Example
 *
 * Shows how to integrate wake word detection in an Electron application.
 * This includes main process, preload, and renderer process code.
 */

// ============================================================================
// MAIN PROCESS (main.ts)
// ============================================================================

export const MainProcessCode = `
/**
 * Electron Main Process
 *
 * Handles wake word detection in the main process.
 */

import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { WakeWordDetector, NodeAudioInput } from 'wake-word-detection';

let mainWindow: BrowserWindow | null = null;
let detector: WakeWordDetector | null = null;
let audioInput: NodeAudioInput | null = null;

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile('index.html');
}

async function initializeWakeWord() {
  detector = new WakeWordDetector({
    modelsPath: path.join(app.getPath('userData'), 'models'),
    keywords: ['hey_jarvis'],  // Or use custom 'computer' model when available
    detectionThreshold: 0.5,
    debug: process.env.NODE_ENV === 'development'
  });

  await detector.initialize();

  // Listen for wake word events
  detector.on((event) => {
    if (event.type === 'detect') {
      // Notify renderer process
      mainWindow?.webContents.send('wake-word-detected', event.data);
    } else if (event.type === 'speech-start') {
      mainWindow?.webContents.send('speech-start');
    } else if (event.type === 'speech-end') {
      mainWindow?.webContents.send('speech-end');
    }
  });

  // Setup audio input
  audioInput = new NodeAudioInput({ sampleRate: 16000 });

  audioInput.onAudio(async (samples) => {
    if (detector?.listening) {
      await detector.processAudioFrame(samples);
    }
  });

  detector.start();
  await audioInput.start();

  console.log('Wake word detection initialized');
}

// IPC handlers
ipcMain.handle('start-listening', async () => {
  detector?.start();
  return true;
});

ipcMain.handle('stop-listening', async () => {
  detector?.stop();
  return true;
});

ipcMain.handle('get-detector-state', async () => {
  return detector?.getState() ?? null;
});

// App lifecycle
app.whenReady().then(async () => {
  await createWindow();
  await initializeWakeWord();
});

app.on('window-all-closed', () => {
  audioInput?.stop();
  detector?.dispose();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
`;

// ============================================================================
// PRELOAD SCRIPT (preload.ts)
// ============================================================================

export const PreloadCode = `
/**
 * Electron Preload Script
 *
 * Exposes safe IPC methods to the renderer process.
 */

import { contextBridge, ipcRenderer } from 'electron';

export interface WakeWordAPI {
  startListening: () => Promise<boolean>;
  stopListening: () => Promise<boolean>;
  getState: () => Promise<any>;
  onWakeWord: (callback: (data: any) => void) => void;
  onSpeechStart: (callback: () => void) => void;
  onSpeechEnd: (callback: () => void) => void;
}

const wakeWordAPI: WakeWordAPI = {
  startListening: () => ipcRenderer.invoke('start-listening'),
  stopListening: () => ipcRenderer.invoke('stop-listening'),
  getState: () => ipcRenderer.invoke('get-detector-state'),
  onWakeWord: (callback) => {
    ipcRenderer.on('wake-word-detected', (_event, data) => callback(data));
  },
  onSpeechStart: (callback) => {
    ipcRenderer.on('speech-start', () => callback());
  },
  onSpeechEnd: (callback) => {
    ipcRenderer.on('speech-end', () => callback());
  }
};

contextBridge.exposeInMainWorld('wakeWord', wakeWordAPI);

declare global {
  interface Window {
    wakeWord: WakeWordAPI;
  }
}
`;

// ============================================================================
// RENDERER PROCESS (renderer.ts)
// ============================================================================

export const RendererCode = `
/**
 * Electron Renderer Process
 *
 * UI and user interaction handling.
 */

// State
let isListeningForCommand = false;

// UI elements (assuming these exist in index.html)
const statusElement = document.getElementById('status');
const commandDisplay = document.getElementById('command-display');
const waveformCanvas = document.getElementById('waveform') as HTMLCanvasElement;

// Update UI status
function updateStatus(message: string, type: 'idle' | 'listening' | 'detected' = 'idle') {
  if (statusElement) {
    statusElement.textContent = message;
    statusElement.className = \`status \${type}\`;
  }
}

// Handle wake word detection
window.wakeWord.onWakeWord((data) => {
  console.log('Wake word detected:', data);
  updateStatus(\`Wake word detected: \${data.keyword} (\${(data.score * 100).toFixed(1)}%)\`, 'detected');
  isListeningForCommand = true;

  // Visual feedback
  document.body.classList.add('wake-word-active');

  // Play a sound or show animation
  playActivationSound();

  // Set timeout to return to idle
  setTimeout(() => {
    if (isListeningForCommand) {
      isListeningForCommand = false;
      document.body.classList.remove('wake-word-active');
      updateStatus('Listening for wake word...', 'idle');
    }
  }, 5000);
});

window.wakeWord.onSpeechStart(() => {
  if (isListeningForCommand) {
    updateStatus('Listening to your command...', 'listening');
  }
});

window.wakeWord.onSpeechEnd(() => {
  if (isListeningForCommand) {
    updateStatus('Processing command...', 'listening');
    // Here you would send the recorded audio to a speech-to-text service
    processVoiceCommand();
  }
});

async function processVoiceCommand() {
  // In a real app, send audio to speech-to-text API
  // Then process the transcribed text

  // Example: simulate processing
  updateStatus('Processing...', 'listening');

  // After processing, show result
  setTimeout(() => {
    if (commandDisplay) {
      commandDisplay.textContent = 'Command received!';
    }
    isListeningForCommand = false;
    document.body.classList.remove('wake-word-active');
    updateStatus('Listening for wake word...', 'idle');
  }, 1000);
}

function playActivationSound() {
  // Play a short beep or activation sound
  const audioContext = new AudioContext();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();

  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);

  oscillator.frequency.value = 800;
  oscillator.type = 'sine';
  gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

  oscillator.start(audioContext.currentTime);
  oscillator.stop(audioContext.currentTime + 0.2);
}

// Initialize
async function init() {
  updateStatus('Initializing wake word detection...', 'idle');

  try {
    await window.wakeWord.startListening();
    updateStatus('Listening for wake word...', 'idle');
  } catch (error) {
    console.error('Failed to start wake word detection:', error);
    updateStatus('Error: Failed to start listening', 'idle');
  }
}

init();
`;

// ============================================================================
// HTML TEMPLATE (index.html)
// ============================================================================

export const HTMLTemplate = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Wake Word Detection</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      color: #fff;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      transition: background 0.3s ease;
    }

    body.wake-word-active {
      background: linear-gradient(135deg, #1a2e1a 0%, #162e16 100%);
    }

    .container {
      text-align: center;
      padding: 40px;
    }

    h1 {
      font-size: 2.5rem;
      margin-bottom: 20px;
    }

    .status {
      font-size: 1.2rem;
      padding: 15px 30px;
      border-radius: 50px;
      background: rgba(255, 255, 255, 0.1);
      margin: 20px 0;
      transition: all 0.3s ease;
    }

    .status.listening {
      background: rgba(76, 175, 80, 0.3);
      box-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
    }

    .status.detected {
      background: rgba(33, 150, 243, 0.3);
      box-shadow: 0 0 30px rgba(33, 150, 243, 0.7);
      animation: pulse 0.5s ease;
    }

    @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.05); }
      100% { transform: scale(1); }
    }

    .microphone-icon {
      width: 100px;
      height: 100px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.1);
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 30px auto;
      font-size: 3rem;
      transition: all 0.3s ease;
    }

    body.wake-word-active .microphone-icon {
      background: rgba(76, 175, 80, 0.3);
      box-shadow: 0 0 40px rgba(76, 175, 80, 0.5);
      animation: glow 1.5s ease infinite;
    }

    @keyframes glow {
      0%, 100% { box-shadow: 0 0 20px rgba(76, 175, 80, 0.5); }
      50% { box-shadow: 0 0 40px rgba(76, 175, 80, 0.8); }
    }

    #command-display {
      font-size: 1.5rem;
      margin-top: 30px;
      min-height: 50px;
    }

    .hint {
      color: rgba(255, 255, 255, 0.6);
      margin-top: 40px;
      font-size: 0.9rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Wake Word Detection</h1>
    <div class="microphone-icon">🎤</div>
    <div id="status" class="status idle">Initializing...</div>
    <div id="command-display"></div>
    <p class="hint">Say "Hey Jarvis" to activate</p>
  </div>
  <script src="renderer.js"></script>
</body>
</html>
`;

// Print integration guide when run directly
if (require.main === module) {
  console.log('='.repeat(70));
  console.log('   Electron Integration Guide for Wake Word Detection');
  console.log('='.repeat(70));
  console.log();
  console.log('This module provides code templates for integrating wake word detection');
  console.log('into an Electron application.');
  console.log();
  console.log('Files to create:');
  console.log('  1. src/main.ts       - Main process (wake word detection)');
  console.log('  2. src/preload.ts    - Preload script (IPC bridge)');
  console.log('  3. src/renderer.ts   - Renderer process (UI handling)');
  console.log('  4. index.html        - HTML template');
  console.log();
  console.log('See the exported code templates in this file for implementation details.');
  console.log();
  console.log('Architecture Overview:');
  console.log('  ┌─────────────────────────────────────────────────────────┐');
  console.log('  │                    MAIN PROCESS                         │');
  console.log('  │  ┌───────────────┐    ┌────────────────────────────┐   │');
  console.log('  │  │ NodeAudioInput│───▶│    WakeWordDetector        │   │');
  console.log('  │  │  (Microphone) │    │  (ONNX inference)          │   │');
  console.log('  │  └───────────────┘    └────────────┬───────────────┘   │');
  console.log('  │                                     │                   │');
  console.log('  │                              IPC Events                 │');
  console.log('  │                                     │                   │');
  console.log('  └─────────────────────────────────────│───────────────────┘');
  console.log('                                        │');
  console.log('  ┌─────────────────────────────────────▼───────────────────┐');
  console.log('  │                   RENDERER PROCESS                       │');
  console.log('  │  ┌───────────────────────────────────────────────────┐  │');
  console.log('  │  │                    UI Updates                      │  │');
  console.log('  │  │  • Show "listening" indicator                      │  │');
  console.log('  │  │  • Play activation sound                           │  │');
  console.log('  │  │  • Display detected command                        │  │');
  console.log('  │  └───────────────────────────────────────────────────┘  │');
  console.log('  └─────────────────────────────────────────────────────────┘');
  console.log();
}
