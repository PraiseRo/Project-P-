# Project P — Voice-Controlled Desktop AI Operator

A hybrid, voice-first desktop AI assistant for Windows that enables hands-free local PC operation (100% offline-ready) alongside online web research and browsing.

Built by **Praise**.

---

## What Project P Can Do

### 1. 100% Offline Local PC Automation (Zero Internet / Zero API Keys Needed)
- **Launch & Close Apps**: *"Open Notepad"*, *"Launch Calculator"*, *"Open VS Code"*, *"Close Chrome"*.
- **File System Management**: *"Create a folder called Projects on my desktop"*, *"Create a text file notes.txt"*.
- **System Metrics & Diagnostics**: *"What is my CPU usage?"*, *"Show system info"*.
- **Screenshots**: *"Take a screenshot"*.
- **Emergency Stop**: Press `Ctrl + Alt + Esc` at any time.

### 2. Online Web Research & Browsing (When Internet is Available)
- **Web Navigation**: *"Open YouTube"*, *"Open github.com"*.
- **Web Searches**: *"Search Google for Python tutorials"*, *"Search YouTube for relaxing lofi"*.
- **Online Research & Instant Answers**: Queries live web facts and summarizes research cleanly.
- **Conversational AI**: Powered by OpenAI / Gemini / Local LLMs for intelligent planning and Q&A.

### 3. Sleek Floating Orb HUD
- A borderless, glowing circular orb widget anchored at the bottom-right corner of your desktop.
- Animated dynamic soundwaves reacting to your voice in real time (`Idle`, `Listening`, `Thinking`, `Executing`, `Speaking`).

---

## Quick Start Guide

### 1. Run Project P
```powershell
python -m app.main
```

### 2. How to Interact
- **Voice Mode**: Press and hold **`Ctrl + Space`**, speak your request, and release.
- **Emergency Stop**: Press **`Ctrl + Alt + Esc`** to immediately abort any running action.

---

## Project Structure
```text
Project-P/
├── app/
│   ├── main.py              # Application lifecycle & runner
│   ├── ai/                  # Hybrid router & LLM provider
│   ├── core/                # Orchestrator, events, state & conversation
│   ├── tools/               # PC automation, apps, files, web research
│   ├── ui/                  # Circular glowing soundwave orb HUD
│   └── voice/               # Microphone, Hotkeys, STT, and TTS
├── tests/                   # Automated unit & integration test suites
├── requirements.txt         # Project dependencies
├── .gitignore               # Security & secrets protection
└── README.md
```
