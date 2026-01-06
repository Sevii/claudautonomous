# Clawdbot Investigation: Tool Calls and Voice Control

## Executive Summary

Clawdbot is a personal AI assistant that operates across multiple platforms (macOS, iOS, Android) with a unique architecture centered around a **Gateway WebSocket control plane**. The system enables voice-activated AI interactions through wake words and continuous "Talk Mode", while providing a comprehensive tool system for browser automation, device control, and cross-platform communication.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Communication Platforms                       │
│   (WhatsApp, Telegram, Slack, Discord, Signal, iMessage, Web)   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         GATEWAY                                  │
│              WebSocket: ws://127.0.0.1:18789                    │
│              Bridge: tcp://0.0.0.0:18790                        │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Voice Wake   │  │ Tool Router  │  │ Session Mgr  │          │
│  │ Management   │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  macOS App    │      │   iOS App     │      │  Android App  │
│  (Menu Bar)   │      │   (Node)      │      │   (Node)      │
│               │      │               │      │               │
│ - Voice Wake  │      │ - Voice Wake  │      │ - Voice Wake  │
│ - Talk Mode   │      │ - Talk Mode   │      │ - Talk Mode   │
│ - Canvas      │      │ - Camera      │      │ - Camera      │
│ - System.run  │      │ - Location    │      │ - SMS         │
└───────────────┘      └───────────────┘      └───────────────┘
```

---

## Voice Control System

### 1. Voice Wake (Wake Word Detection)

The voice wake system is **centrally managed by the Gateway**, ensuring all devices share synchronized trigger words.

#### Configuration Storage
```json
// ~/.clawdbot/settings/voicewake.json
{
  "triggers": ["clawd", "claude", "computer"],
  "updatedAtMs": 1730000000000
}
```

#### Protocol Methods
| Method | Description |
|--------|-------------|
| `voicewake.get` | Retrieves current trigger word list |
| `voicewake.set` | Updates triggers with validation |

#### Event Broadcasting
- `voicewake.changed` - Broadcasts updated triggers to all connected clients
- Changes propagate automatically to macOS, iOS, and Android via bridge protocol

#### Platform Implementation
- **macOS**: Controls `VoiceWakeRuntime` activation from menu bar app
- **iOS**: Integrates with `VoiceWakeManager` for detection
- **Android**: Settings editor syncs changes via bridge

### 2. Talk Mode (Continuous Voice Conversation)

Talk mode provides an **always-on overlay** for hands-free conversations.

#### Conversation Loop
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   LISTENING  │ ──▶ │   THINKING   │ ──▶ │   SPEAKING   │
│              │     │              │     │              │
│ (Speech →    │     │ (chat.send   │     │ (ElevenLabs  │
│  Transcript) │     │  to model)   │     │  TTS output) │
└──────────────┘     └──────────────┘     └──────────────┘
        ▲                                        │
        └────────────────────────────────────────┘
```

#### Key Features
- **Silence Detection**: Submits transcript after brief pause
- **Interrupt Capability**: Halts playback when user speaks during response
- **Streaming Playback**: ElevenLabs API with incremental audio for low latency

#### Voice Control Protocol
Assistants can customize voice parameters by prefixing responses with JSON:
```json
{"voice":"<voice-id>","once":true}
```

Available parameters:
- `voice` - Voice identifier
- `model` - ElevenLabs model selection
- `speed`/`rate` - Playback speed
- `stability`, `similarity`, `style` - Voice characteristics
- `once` - Apply settings only to current reply

#### Configuration
```json
// clawdbot.json
{
  "elevenlabs": {
    "voiceId": "...",
    "modelId": "eleven_v3",
    "outputFormat": "pcm_16000",
    "apiKey": "...",
    "interruptOnSpeech": true
  }
}
```

---

## Tool Call System

### Tool Architecture

Tools operate as **first-class agent functions** rather than shell-based commands. The system uses two parallel channels:

1. **System Prompt Text** - Human-readable tool descriptions
2. **Provider Tool Schema** - Typed function declarations for model APIs (OpenAI, Anthropic, Gemini)

### Core Tool Categories

#### 1. `bash` - Shell Command Execution
```typescript
{
  command: string,      // Required
  yieldMs?: number,     // Auto-background timeout (default 10000ms)
  background?: boolean, // Immediate background execution
  timeout?: number,     // Process timeout in seconds (default 1800)
  elevated?: boolean    // Run on host if elevation enabled
}
```

#### 2. `process` - Background Session Management
Actions: `list`, `poll`, `log`, `write`, `kill`, `clear`, `remove`

#### 3. `browser` - UI Automation
Core actions:
- `status`, `start`, `stop`, `tabs`
- `open`, `focus`, `close`
- `snapshot`, `screenshot`
- `act` - UI interactions (click/type/press/hover/drag/select/fill)

Profile management: `profiles`, `create-profile`, `delete-profile`, `reset-profile`

#### 4. `canvas` - Node.js Canvas Control
Actions: `present`, `hide`, `navigate`, `eval`, `snapshot`, `a2ui_push`, `a2ui_reset`

Uses gateway `node.invoke` internally to communicate with devices.

#### 5. `nodes` - Device Targeting
```typescript
// Discovery and pairing
actions: ['status', 'describe', 'pending', 'approve', 'reject']

// Media capture
actions: ['camera_snap', 'camera_clip', 'screen_record', 'location_get']

// Communication
actions: ['notify', 'sms.send']  // SMS Android only
```

#### 6. `image` - Vision Analysis
```typescript
{
  image: string,    // Path or URL (required)
  prompt?: string,  // Analysis prompt
  model?: string,   // Model override
  maxBytesMb?: number
}
```

#### 7. `cron` - Job Scheduling
Actions: `status`, `list`, `add`, `update`, `remove`, `run`, `runs`, `wake`

#### 8. Session Tools
- `sessions_list` - Fetch sessions with filters
- `sessions_history` - Inspect transcripts
- `sessions_send` - Cross-session messaging

### Tool Routing to Devices

Tool calls can be routed to specific paired devices:

```bash
# Invoke tool on specific node
clawdbot nodes invoke \
  --node <device-id> \
  --command canvas.eval \
  --params '{"javaScript":"location.href"}'
```

### Configuration & Security

#### Allowlist/Denylist Model
```json
// clawdbot.json
{
  "agent": {
    "tools": {
      "deny": ["browser", "bash"],
      "allow": ["read", "write", "image"]
    }
  }
}
```

- Non-main sessions (groups/channels) can run in Docker sandboxes
- Restricted tool access based on session type
- `system.run` is not exposed as a tool by default

---

## Gateway Communication Protocol

### WebSocket Message Structure

#### Request/Response Pattern
```typescript
// Request
{ type: "req", id: string, method: string, params: object }

// Response
{ type: "res", id: string, ok: boolean, payload?: object, error?: object }

// Event
{ type: "event", event: string, payload: object, seq?: number }
```

### Core Gateway Methods

| Method | Description |
|--------|-------------|
| `health/status` | System state information |
| `send` | Message delivery via providers |
| `agent` | Initiates agent turns (streams events) |
| `node.list` | List connected devices |
| `node.describe` | Get device details |
| `node.invoke` | Execute tool on device |
| `node.pair.*` | Device pairing lifecycle |

### Event Broadcasting
- `agent` - Streamed tool/output events
- `presence` - Connectivity updates
- `tick` - Keepalive confirmations
- `shutdown` - Graceful termination notice

---

## Agent Runtime (Pi-mono)

### Bootstrap Files
The agent injects these workspace files on first turn:
- `AGENTS.md` - Operating instructions/memory
- `SOUL.md` - Persona and boundaries
- `TOOLS.md` - Tool usage notes
- `BOOTSTRAP.md` - One-time setup ritual
- `IDENTITY.md` - Agent name/vibe
- `USER.md` - User profile information

### Streaming & Message Queuing
- Block streaming sends completed assistant blocks
- Queue mode "steer" injects messages mid-turn after each tool call
- Remaining calls skipped if queued message arrives

### Session Storage
```
~/.clawdbot/sessions/<SessionId>.jsonl
```

---

## Key Implementation Files

| Component | Location |
|-----------|----------|
| Gateway | `src/gateway/` |
| CLI | `src/cli/` |
| Tool definitions | Various under `src/` |
| Node CLI | `src/cli/nodes-cli.ts` |
| iOS Node Model | `apps/ios/Sources/Model/NodeAppModel.swift` |
| Android Node | `apps/android/app/src/main/java/com/clawdbot/android/node/` |
| Shared Kit | `apps/Shared/ClawdbotKit/` |

---

## Summary: How Voice + Tool Calls Work Together

1. **Voice Activation**: User speaks wake word → detected by companion app → triggers agent turn

2. **Speech to Text**: Talk mode converts speech to transcript during "listening" phase

3. **Agent Processing**: Transcript sent via `chat.send` → model processes with available tools

4. **Tool Execution**: Model requests tool calls → Gateway routes to appropriate handler:
   - Local tools (bash, read, write) execute on host
   - Device tools routed via `node.invoke` to paired devices
   - Browser tools interact with dedicated Chromium instance

5. **Response Synthesis**: Model response → ElevenLabs TTS → streamed audio playback

6. **Interrupt Handling**: If user speaks during playback → audio stops → new listening cycle begins

This creates a seamless voice-controlled AI assistant that can execute complex multi-step tasks across multiple devices while maintaining natural conversation flow.
