# Project MeetJot: Technical Design Document (TDD)

**Version:** 1.0 (Hackathon Edition)
**Architecture Pattern:** Electron "Sidecar" (Localhost Microservice)



## **1. Executive Summary**

**Project MeetJot** is a privacy-first, zero-cost desktop assistant that automates meeting follow-ups. Unlike cloud-based SaaS tools (Otter/Fireflies) that require bots to join calls, MeetJot runs locally on the user's machine, listening to system audio. It uses a "Human-in-the-Loop" workflow where AI proposes actions (JIRA tickets, Calendar events), but the user explicitly approves them.

**Core Philosophy:**

* **Privacy:** Audio is processed in RAM. No storage on external servers.
* **Safety:** AI drafts actions; Humans execute them.
* **Independence:** "Bring Your Own Key" (BYOK) model eliminates vendor lock-in.



## **2. System Architecture**

We utilize the **Electron Sidecar Pattern**. This architecture is standard in modern desktop apps (like VS Code or Slack's backend) but adapted here to run a Python engine alongside the UI.

### **2.1 High-Level Architecture Diagram**

### **2.2 Component Deep Dive**

#### **A. The Frontend (The "Face")**

* **Technology:** Electron + React (Vite) + TailwindCSS.
* **Responsibility:**
* **Main Process (Node.js):** Manages the application window, System Tray icon, and OS-level interactions (file system, notifications). It is the "Parent" that spawns the Python process.
* **Renderer Process (React):** The actual UI where users view transcripts and approve tasks. It talks to the Python backend via HTTP.



#### **B. The Backend (The "Muscle")**

* **Technology:** Python 3.10+ (FastAPI) compiled to a standalone executable.
* **Responsibility:**
* **Audio Engine:** Captures raw audio bytes from the OS loopback.
* **AI Controller:** Manages API calls to Groq (Whisper/Llama).
* **Database Manager:** Reads/Writes to the local SQLite file.
* **Integrator:** Executes the actual API calls to JIRA/Google.



#### **C. The Bridge (Communication)**

* **Protocol:** HTTP (REST) + WebSockets (Optional for real-time text).
* **Mechanism:** When the app starts, Python spins up a server on `localhost:8000`. The React frontend is hardcoded to call this local address.



## **3. The Intelligence Pipeline (Data Flow)**

This is the critical path. Understanding this ensures the backend dev knows what to send and the frontend dev knows what to display.

### **Stage 1: The "T-Pipe" Capture**

* **Input:** System Audio (Speaker) + Microphone.
* **Process:** We use `soundcard` (Python library) to tap into the WASAPI loopback.
* **Hackathon Shortcut:** Instead of complex streaming buffers, we record to a temporary file (`temp_chunk.wav`) every 30 seconds. This adds slightly latency but drastically reduces crash risk.

### **Stage 2: Transcription (STT)**

* **Action:** Python sends `temp_chunk.wav` to **Groq Whisper API**.
* **Why Groq?** Speed. It returns text in <2 seconds.
* **Output:** Raw string: *"Hey we need to deploy the hotfix by next Friday."*

### **Stage 3: Extraction & Reasoning (LLM)**

* **Action:** Python sends the Raw String + `Context Data` to **Llama 3 (via Groq)**.
* **Context Data:** The prompt *must* include:
* Current Date (e.g., "2025-12-20")
* User Timezone


* **System Prompt:** *"You are a JSON extractor. If user says 'next Friday', calculate the date. Return a list of tool calls."*
* **Output:** Structured JSON.

### **Stage 4: The Staging Area (The "Diff")**

* **Action:** The JSON is **NOT** sent to JIRA. It is saved to `tasks.db` with status `PENDING`.
* **User Interface:** The Dashboard polls the DB and renders a "Draft Card".
* **Approval:** User clicks "Approve"  Frontend calls `POST /execute`  Python calls JIRA API.



## **4. Database Schema (SQLite)**

We use a simple local file: `C:\Users\{User}\AppData\Roaming\MeetJot\MeetJot.db`.

**Table: `actions**`
| Column | Type | Description |
| : | : | : |
| `id` | TEXT (UUID) | Unique ID for the UI to track cards. |
| `status` | TEXT | `PENDING`, `APPROVED`, `REJECTED`, `ERROR` |
| `tool_type` | TEXT | `JIRA_TICKET`, `G_CAL_EVENT` |
| `ai_payload` | JSON | The raw draft from AI (Summary, Priority, etc.) |
| `final_payload`| JSON | The user-edited version (if they changed it) |
| `created_at` | TIMESTAMP | For sorting in the dashboard. |



## **5. Developer Setup Guide (From Zero to Hello World)**

Follow these steps exactly to avoid "dependency hell."

### **Prerequisites**

* Node.js (v18+)
* Python (v3.10+)
* Visual Studio Code

### **Step 1: Clone & Structure**

Create the folders as defined below. Do not mix frontend/backend files.

```text
/meet-jotter
├── /backend (Python work here)
├── /src (React work here)
├── /electron (Main process work here)
└── package.json

```

### **Step 2: Backend Setup**

1. Navigate to `/backend`.
2. Create virtual env: `python -m venv venv`.
3. Activate it: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Win).
4. Install requirements:
```bash
pip install fastapi uvicorn soundcard numpy scipy groq requests python-dotenv pyinstaller

```


5. **Test:** Run `python main.py`. Go to `localhost:8000/docs`. If you see the Swagger UI, you are golden.

### **Step 3: Frontend Setup**

1. Root folder: `npm create vite@latest . -- --template react`.
2. Install Electron deps: `npm install electron concurrently wait-on --save-dev`.
3. **Test:** Run `npm run dev`. Ensure the React page loads.

### **Step 4: Connecting the Two**

Modify `package.json` scripts to run both at once (for dev):

```json
"scripts": {
  "dev": "concurrently \"python backend/main.py\" \"vite\"",
  "electron": "electron ."
}

```

*Now, running `npm run dev` starts everything.*



## **6. Build & Execution (Creating the .exe)**

This is the most complex part. Read carefully. The goal is to embed the Python server *inside* the Electron app so the user installs only one file.

### **Phase A: "Freezing" the Python Engine**

We use `PyInstaller` to turn your python scripts into `meeting_engine.exe`.

1. **Command:**
```bash
cd backend
pyinstaller --noconfirm --onefile --windowed --name "meeting_engine" \
  --hidden-import=uvicorn --hidden-import=fastapi --hidden-import=soundcard \
  --hidden-import=engineio.async_drivers.threading \
  main.py

```


*(Note: The `--hidden-import` flags are crucial. PyInstaller often misses these dynamic libraries.)*
2. **Verify:** Check the `backend/dist/` folder. You should see `meeting_engine.exe`. Double-click it. It should run silently (check Task Manager). Kill it after testing.

### **Phase B: Configuring Electron Builder**

We must tell Electron to pick up this `.exe` and put it in the installer.

1. **Edit `package.json`:**
```json
"build": {
  "extraResources": [
    {
      "from": "backend/dist/meeting_engine.exe",
      "to": "meeting_engine.exe"
    }
  ]
}

```



### **Phase C: The "Spawn" Logic**

In `electron/main.js`, you need dynamic path handling. When developing, you want to use the python script. When shipped, you want to use the `.exe`.

```javascript
const { app } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

// PRODUCTION vs DEVELOPMENT Path Logic
const backendBinary = app.isPackaged
  ? path.join(process.resourcesPath, 'meeting_engine.exe') // The shipped exe
  : path.join(__dirname, '../backend/dist/meeting_engine.exe'); // Local test

// Launch it
const apiProcess = spawn(backendBinary);

// Cleanup on exit
app.on('will-quit', () => {
  apiProcess.kill();
});

```

### **Phase D: Generate Installer**

Run `npm run electron:build`.
You will get a `MeetJot-Setup-1.0.0.exe` in the `dist` folder. **This is your Hackathon submission.**



## **7. User Manual (The "Happy Path")**

This is how you will demonstrate the app to judges.

1. **Launch:** Open `MeetJot.exe`.
2. **Onboarding:** The "Settings" modal appears.
* *Action:* Input Groq API Key (Free) & JIRA Creds.
* *Verification:* A green "Connected" badge appears.


3. **The Meeting:**
* *Action:* Click "Start Meeting" (Tray Icon).
* *Visual:* Tray icon turns Red.
* *Audio:* Speak a command: *"Create a bug ticket for the login page failure."*


4. **The Review:**
* *Action:* Click "Stop".
* *Visual:* Dashboard refreshes. A new Card appears.
* *Check:* Verify the "Title" and "Priority" are correct.


5. **The Execution:**
* *Action:* Click "Approve".
* *Result:* The card turns green. Open JIRA in Chrome and show the new ticket.





## **8. Troubleshooting & FAQ**

**Q: The Python backend isn't starting in the .exe!**

* **Fix:** Check the logs. In `main.js`, add `apiProcess.stdout.on('data', (data) => logToFile(data))`. Usually, it's a missing import. Add it to the `--hidden-import` flag in PyInstaller.

**Q: Audio recording is failing on Windows.**

* **Fix:** Ensure "Stereo Mix" or "Loopback" is enabled in Windows Sound Settings. If `soundcard` fails, switch to standard `speech_recognition` library (microphone only) as a fallback for the demo.

**Q: Groq API errors?**

* **Fix:** Rate limits are rare but possible. Rotate keys if needed. Ensure the payload sent to Llama 3 is valid JSON string.