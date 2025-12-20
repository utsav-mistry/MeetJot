# MeetJot

**"Don't just meet. Jot it down."**

**MeetJot** is a privacy-first, local desktop assistant that turns chaotic meeting conversations into structured JIRA tickets and Calendar events. It acts as a "Sidecar" to your meetings, listening in real-time and drafting actions for your approval.

## Key Features

### Universal "Loopback" Listening

* **Works with Everything:** Whether it's Zoom, Teams, Google Meet, or Discord—if you can hear it, MeetJot can hear it.
* **Dual-Stream Capture:** Captures both your Microphone (Input) and System Audio (Output) simultaneously for a complete transcript.

### Zero-Cost AI Intelligence

* **Powered by Groq:** Utilizes the ultra-fast Llama 3 and Whisper V3 models via Groq's free cloud API.
* **Smart Context:** Automatically understands relative dates (e.g., "Next Friday" becomes `2025-12-26`) and detects urgency tones.

### Privacy-First Architecture

* **Local Processing:** Audio is processed in RAM and sent directly to the AI engine. No audio files are stored on external servers.
* **BYOK (Bring Your Own Key):** Users own their API keys. No vendor lock-in, no hidden subscriptions.

### "Man-in-the-Middle" Workflow

* **Draft-Approve-Commit:** MeetJot never messes with your JIRA board automatically.
* **The Review Deck:** All AI-detected tasks appear as "Draft Cards." You can Edit, Approve, or Reject them before they go live.

### Seamless Integrations

* **JIRA Cloud:** Create Bug reports, Tasks, and Stories with one click.
* **Google Calendar:** Schedule follow-ups instantly based on verbal agreements.



## System Architecture

MeetJot uses the **Electron Sidecar Pattern**, bundling a powerful Python engine inside a lightweight desktop app.

* **Frontend (The Face):** `Electron` + `React` + `TailwindCSS`
* Handles the UI, System Tray, and User Interactions.


* **Backend (The Muscle):** `Python` (`meet-jotter`)
* **FastAPI:** Runs a local server on port 8000.
* **Soundcard:** Taps into OS audio drivers.
* **SQLite:** Stores pending tasks locally (`%APPDATA%/MeetJot/titan.db`).





## Getting Started (Dev Mode)

### Prerequisites

* Node.js (v18+)
* Python (v3.10+)
* **Free API Keys:**
* [Groq Console](https://console.groq.com) (For AI)
* [Atlassian Token](https://id.atlassian.com/manage/api-tokens) (For JIRA)



### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/MeetJot.git
cd MeetJot

```

### 2. Ignite the Backend (`meet-jotter`)

```bash
cd meet-jotter
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python main.py
# Server running at http://localhost:8000

```

### 3. Launch the App

Open a new terminal in the root folder:

```bash
npm install
npm run dev
# Electron window should open and connect to Python

```



## Building for Production (.exe)

To generate the standalone `MeetJot-Setup.exe` for the judges:

1. **Freeze Python:**
```bash
cd meet-jotter
pyinstaller --noconfirm --onefile --windowed --name "meet_jotter" --hidden-import=uvicorn --hidden-import=fastapi main.py

```


2. **Build Electron:**
```bash
cd ..
npm run electron:build

```


3. **Distribute:**
The installer will be in `dist/MeetJot-Setup-1.0.0.exe`.



## Future Roadmap

* **Real-time Speaker ID:** Diarization to tag "Who said what."
* **Slack Integration:** Push summaries to team channels.
* **Offline Mode:** Switch to `Ollama` + `Faster-Whisper` for fully air-gapped usage.



## Team

* **[Nishit Somani]** - AI Engineering and Optimization (Kaptaan Sahab)
* **[Vedant Hingu]** - Frontend Design and Database organization
* **[Hetansh Panchal]** - Database Enginnering and Optimization
* **[Neel Patel]** - Backend monitoring and tool control
* **[Utsav Mistry]** - Backend impplememntation and Architecture

> Built with ❤️ and ☕ at [DA-IICT].