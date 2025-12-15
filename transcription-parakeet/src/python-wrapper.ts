/**
 * Python wrapper for Parakeet transcription using NeMo
 *
 * This approach calls the Python NeMo implementation via child_process,
 * providing a TypeScript-friendly interface while leveraging the official implementation.
 */

import { spawn } from 'child_process';
import { TranscriptionResult, TranscriptionOptions, ParakeetConfig } from './types.js';
import { existsSync } from 'fs';
import { resolve } from 'path';

export class PythonParakeetTranscriber {
  private config: ParakeetConfig;
  private pythonScriptPath: string;

  constructor(config: ParakeetConfig = {}) {
    this.config = config;
    this.pythonScriptPath = resolve(process.cwd(), 'scripts', 'transcribe.py');
  }

  /**
   * Verify that Python and required packages are available
   */
  async checkDependencies(): Promise<boolean> {
    return new Promise((resolve) => {
      const python = spawn('python3', ['-c', 'import nemo.collections.asr; print("OK")']);

      let output = '';
      python.stdout.on('data', (data) => {
        output += data.toString();
      });

      python.on('close', (code) => {
        resolve(code === 0 && output.includes('OK'));
      });
    });
  }

  /**
   * Transcribe an audio file using the Python NeMo implementation
   */
  async transcribe(options: TranscriptionOptions): Promise<TranscriptionResult> {
    if (!existsSync(options.audioPath)) {
      throw new Error(`Audio file not found: ${options.audioPath}`);
    }

    if (!existsSync(this.pythonScriptPath)) {
      throw new Error(`Python script not found: ${this.pythonScriptPath}`);
    }

    return new Promise((resolve, reject) => {
      const args = [
        this.pythonScriptPath,
        '--audio', options.audioPath,
      ];

      if (options.includeTimestamps) {
        args.push('--timestamps');
      }

      if (this.config.modelPath) {
        args.push('--model', this.config.modelPath);
      }

      const python = spawn('python3', args);

      let stdout = '';
      let stderr = '';

      python.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      python.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      python.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python process exited with code ${code}\nStderr: ${stderr}`));
          return;
        }

        try {
          const result: TranscriptionResult = JSON.parse(stdout);
          resolve(result);
        } catch (error) {
          reject(new Error(`Failed to parse output: ${stdout}\nError: ${error}`));
        }
      });

      python.on('error', (error) => {
        reject(new Error(`Failed to spawn Python process: ${error.message}`));
      });
    });
  }

  /**
   * Batch transcribe multiple audio files
   */
  async transcribeBatch(files: TranscriptionOptions[]): Promise<TranscriptionResult[]> {
    const results: TranscriptionResult[] = [];

    for (const file of files) {
      const result = await this.transcribe(file);
      results.push(result);
    }

    return results;
  }
}
