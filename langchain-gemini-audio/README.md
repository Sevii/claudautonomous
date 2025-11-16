# LangChain TypeScript Audio Transcription with Google Gemini

This example demonstrates how to use LangChain with Google Gemini API to transcribe audio files and bind tools for function calling in TypeScript.

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Your Google API Key

Set your Gemini API key as an environment variable:

```bash
export GOOGLE_API_KEY=your-api-key-here
```

Or create a `.env` file:

```
GOOGLE_API_KEY=your-api-key-here
```

### 3. Prepare Your Audio File

Place your audio file (MP3, WAV, etc.) in the project directory and update the file path in the example code.

## Usage

The example file (`gemini-audio-example.ts`) includes several usage patterns:

### 1. Audio Transcription with Tool Binding

```typescript
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { HumanMessage } from "@langchain/core/messages";
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import * as fs from "fs";

// Define a tool
const myTool = tool(
  async ({ action }) => {
    return `Executed action: ${action}`;
  },
  {
    name: "my_tool",
    description: "Tool description",
    schema: z.object({
      action: z.string(),
    }),
  }
);

// Create model and bind tools
const llm = new ChatGoogleGenerativeAI({
  model: "gemini-2.0-flash-exp",
  apiKey: process.env.GOOGLE_API_KEY,
});

const modelWithTools = llm.bindTools([myTool]);

// Convert audio to base64
const audioBase64 = fs.readFileSync("./audio.mp3").toString("base64");

// Invoke with audio
const result = await modelWithTools.invoke([
  new HumanMessage({
    content: [
      {
        type: "media",
        mimeType: "audio/mp3",
        data: audioBase64,
      },
      {
        type: "text",
        text: "Transcribe this audio and select appropriate tool.",
      },
    ],
  }),
]);
```

### 2. Simple Audio Transcription (No Tools)

```typescript
const llm = new ChatGoogleGenerativeAI({
  model: "gemini-2.0-flash-exp",
  apiKey: process.env.GOOGLE_API_KEY,
});

const audioBase64 = fs.readFileSync("./audio.mp3").toString("base64");

const result = await llm.invoke([
  new HumanMessage({
    content: [
      {
        type: "media",
        mimeType: "audio/mp3",
        data: audioBase64,
      },
      {
        type: "text",
        text: "Transcribe this audio.",
      },
    ],
  }),
]);

console.log(result.content);
```

### 3. Text-Only with Tool Binding (Matching Python Example)

```typescript
const llm = new ChatGoogleGenerativeAI({
  model: "gemini-2.0-flash-exp",
  temperature: 1.0,
  apiKey: process.env.GOOGLE_API_KEY,
});

const modelWithTools = llm.bindTools([tool1, tool2]);

const result = await modelWithTools.invoke("Your text prompt here");
```

## Supported Audio Formats

Google Gemini supports the following audio formats:
- MP3 (`audio/mp3` or `audio/mpeg`)
- WAV (`audio/wav`)
- WEBM (`audio/webm`)
- FLAC (`audio/flac`)

## Key Differences from Python

### Python Version
```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=1.0,
    google_api_key=api_key,
)

model = llm.bind_tools(tools)
result = model.invoke(prompt)
```

### TypeScript Version
```typescript
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";

const llm = new ChatGoogleGenerativeAI({
  model: "gemini-2.0-flash-exp",
  temperature: 1.0,
  apiKey: process.env.GOOGLE_API_KEY,
});

const modelWithTools = llm.bindTools(tools);
const result = await modelWithTools.invoke(prompt);
```

## Audio Content Format

When using audio files, structure the HumanMessage content as follows:

```typescript
new HumanMessage({
  content: [
    {
      type: "media",           // Indicates multimodal content
      mimeType: "audio/mp3",   // MIME type of audio file
      data: audioBase64,        // Base64-encoded audio data
    },
    {
      type: "text",            // Optional text prompt
      text: "Your instructions here",
    },
  ],
})
```

## Running the Examples

```bash
npm start
```

Or run specific functions by uncommenting the `main()` call at the bottom of `gemini-audio-example.ts`.

## Troubleshooting

### Error: API Key Not Set
Make sure you've set the `GOOGLE_API_KEY` environment variable.

### Error: File Not Found
Verify the audio file path is correct and the file exists.

### Error: Unsupported Format
Ensure your audio file is in a supported format (MP3, WAV, WEBM, or FLAC).

## Additional Resources

- [LangChain.js Documentation](https://js.langchain.com/)
- [@langchain/google-genai Package](https://www.npmjs.com/package/@langchain/google-genai)
- [Google Gemini API Audio Understanding](https://ai.google.dev/gemini-api/docs/audio)
- [LangChain Multimodal Documentation](https://js.langchain.com/docs/concepts/multimodality/)

## Alternative: Using Direct Google GenAI SDK

If you need more control, you can use the `@google/genai` SDK directly:

```typescript
import { GoogleGenerativeAI } from "@google/genai";

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

// Upload audio file and generate content
```

## License

MIT
