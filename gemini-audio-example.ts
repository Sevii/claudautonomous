import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import * as fs from "fs";

// Define your tools similar to the Python example
const spaceWeatherScreen = tool(
  async ({ action }) => {
    // Implement your space weather screen logic
    console.log(`Space weather action: ${action}`);
    return `Executed space weather screen with action: ${action}`;
  },
  {
    name: "space_weather_screen",
    description: "Tool for handling space weather screen requests",
    schema: z.object({
      action: z.string().describe("The action to perform on space weather screen"),
    }),
  }
);

const doNothing = tool(
  async () => {
    console.log("Do nothing tool called");
    return "No action taken";
  },
  {
    name: "do_nothing",
    description: "A tool that does nothing",
    schema: z.object({}),
  }
);

// Function to convert audio file to base64
function audioFileToBase64(filePath: string): string {
  const audioBuffer = fs.readFileSync(filePath);
  return audioBuffer.toString("base64");
}

async function transcribeAudioWithTools() {
  const model = "gemini-2.0-flash-exp"; // or "gemini-1.5-pro"
  const tools = [spaceWeatherScreen, doNothing];

  // Create LLM instance
  const llm = new ChatGoogleGenerativeAI({
    model: model,
    temperature: 1.0,
    maxRetries: 1,
    apiKey: process.env.GOOGLE_API_KEY, // Set your API key in environment
  });

  // Bind tools to the model
  const modelWithTools = llm.bindTools(tools);

  // Load and encode audio file
  const audioFilePath = "./audio.mp3"; // Replace with your audio file path
  const audioBase64 = audioFileToBase64(audioFilePath);

  // Prepare prompts
  const preprompt = `
    AI Agent we are about to receive a request for a tool from a user. Please select the appropriate tool based on their request.

    Customer request:
  `;

  const postprompt = ` AI Agent the above is a request from a user for a specific UI option in the form of a tool call.
    Please end your response with the option the user requested.
  `;

  // Option 1: Using audio file with text prompt
  const result = await modelWithTools.invoke([
    new HumanMessage({
      content: [
        {
          type: "media",
          mimeType: "audio/mp3", // or "audio/wav", "audio/mpeg", etc.
          data: audioBase64,
        },
        {
          type: "text",
          text: preprompt + "Transcribe the audio and select appropriate tool." + postprompt,
        },
      ],
    }),
  ]);

  console.log("Response:", result);
  console.log("Content:", result.content);

  // Check if tools were called
  if (result.tool_calls && result.tool_calls.length > 0) {
    console.log("Tool calls:", result.tool_calls);
  }

  return result;
}

// Alternative example: Text-only with tool calling (matching your Python example more closely)
async function textOnlyWithTools(prompt: string) {
  const model = "gemini-2.0-flash-exp";
  const tools = [spaceWeatherScreen, doNothing];

  // Create LLM instance
  const llm = new ChatGoogleGenerativeAI({
    model: model,
    temperature: 1.0,
    maxRetries: 1,
    apiKey: process.env.GOOGLE_API_KEY,
  });

  // Bind tools to the model
  const modelWithTools = llm.bindTools(tools);

  // Prepare prompts
  const preprompt = `
    AI Agent we are about to receive a request for a tool from a user. Please select the appropriate tool based on their request.

    Customer request:
  `;

  const postprompt = ` AI Agent the above is a request from a user for a specific UI option in the form of a tool call.
    Please end your response with the option the user requested.
  `;

  // Invoke with text-only (like your Python example)
  const result = await llm.invoke(preprompt + prompt + postprompt);

  console.log("Response:", result);
  console.log("Content:", result.content);

  return result;
}

// Example: Audio transcription without tools
async function simpleAudioTranscription() {
  const llm = new ChatGoogleGenerativeAI({
    model: "gemini-2.0-flash-exp",
    temperature: 0,
    apiKey: process.env.GOOGLE_API_KEY,
  });

  const audioFilePath = "./audio.mp3";
  const audioBase64 = audioFileToBase64(audioFilePath);

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
          text: "Transcribe this audio file.",
        },
      ],
    }),
  ]);

  console.log("Transcription:", result.content);
  return result;
}

// Example: Using remote audio URL (if supported)
async function transcribeRemoteAudio() {
  const llm = new ChatGoogleGenerativeAI({
    model: "gemini-2.0-flash-exp",
    temperature: 0,
    apiKey: process.env.GOOGLE_API_KEY,
  });

  const result = await llm.invoke([
    new HumanMessage({
      content: [
        {
          type: "text",
          text: "Transcribe this audio file.",
        },
        {
          type: "media",
          mimeType: "audio/mp3",
          data: "https://example.com/audio.mp3", // Some providers support URLs
        },
      ],
    }),
  ]);

  console.log("Transcription:", result.content);
  return result;
}

// Run the examples
async function main() {
  try {
    // Example 1: Audio transcription with tool binding
    console.log("=== Audio Transcription with Tools ===");
    await transcribeAudioWithTools();

    // Example 2: Text-only with tools (matching your Python example)
    console.log("\n=== Text-Only with Tools ===");
    await textOnlyWithTools("Show me the space weather screen");

    // Example 3: Simple audio transcription
    console.log("\n=== Simple Audio Transcription ===");
    await simpleAudioTranscription();
  } catch (error) {
    console.error("Error:", error);
  }
}

// Uncomment to run
// main();

export {
  transcribeAudioWithTools,
  textOnlyWithTools,
  simpleAudioTranscription,
  transcribeRemoteAudio,
};
