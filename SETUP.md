# Setup Guide (Windows, no code needed)

Follow top to bottom. Each step is a double-click or a paste.

## 1. Install Python

1. Go to https://www.python.org/downloads
2. Download the latest Windows installer.
3. Run it and **tick "Add python.exe to PATH"** before clicking Install.

## 2. Get a free AI key (one of these — OpenRouter is recommended)

- **OpenRouter (recommended):** go to https://openrouter.ai → sign in → "Keys" → "Create Key". The free model
  `meta-llama/llama-3.3-70b-instruct:free` is preset in `.env`.
- **Groq:** https://console.groq.com → sign in → "API Keys" → create one. Very fast.
- **Gemini:** https://aistudio.google.com → "Get API key". Note Gemini can rate-limit free keys.

You only need one. Copy the key — you'll paste it in step 4.

## 3. Get a Gmail API credential (optional, for the email tools)

The server uses Google's official API so it never needs your Gmail password.

1. Go to https://console.cloud.google.com and create a project.
2. Search "Gmail API" → Enable.
3. Go to "OAuth consent screen" → choose **External** → add your email as a test user.
4. Go to "Credentials" → "Create credentials" → "OAuth client ID" → **Desktop app** → Create.
5. Download the JSON file and save it as `credentials.json` inside `backend/`.

> Tip: use a dedicated job-hunting Gmail, not your main account.

## 4. Run setup

1. Double-click `backend\setup.bat`.
2. It installs everything, downloads a browser for job automation, and creates `backend\.env`.
3. Open `backend\.env` in Notepad and set:
   - `API_KEY=` to a long random string you make up (this is your app password).
   - `LLM_API_KEY=` to your OpenRouter/Groq/Gemini key.
   - Keep the rest as-is.
4. (Optional) Copy your `credentials.json` into `backend\`.

## 5. Start the server

Double-click `backend\run.bat`. A window appears; keep it open. JobBot lives at:

- Web app (chat, stats, jobs, emails) — later, see steps below
- Server API docs → http://127.0.0.1:8765/docs

## 6. Open the web app

From the `web/` folder:

```bash
npm install
npm run dev
```

Then open http://localhost:5173 on your PC. On your **phone**, open
`http://<your-PC-lan-ip>:5173` (find your IP with `ipconfig` — the 192.168.x.x line).
Open the app's **Settings** tab and set:
- API key → the `API_KEY` you chose
- Base URL → `http://127.0.0.1:8765` on the PC itself, or `http://<PC-IP>:8765` from the phone

## 7. Connect Gmail (in the app)

Settings → Gmail → Connect → sign in with Google → paste the code → Connected.
Then go to the **Emails** tab and press "Sync inbox".

## 8. Connect LinkedIn / Indeed (for applying)

In the server API docs (http://127.0.0.1:8765/docs):

1. `POST /api/auth/browser/login` with body `{"platform": "linkedin"}`.
2. A browser opens — **log in manually** (do a 2FA check yourself).
3. Then `POST /api/auth/browser/finish-login`.
4. From now on, ask JobBot in Chat: "apply to this job: <url>".

Applications stop before submitting (review-first mode). You confirm, JobBot submits.

## 9. Keep it on

The laptop must be on and `run.bat` open for JobBot to work. For phone access away from home:
install Tailscale (free) on PC and phone — the phone can then reach the PC by name, e.g.
`http://my-pc-name:8765`.

## Troubleshooting

- Browser doesn't open → Playwright browser missing. Run `pip install playwright` then `playwright install chromium` inside `backend\.venv`.
- "Could not reach the AI provider" → check `LLM_API_KEY` + `LLM_MODEL` in `.env`, then restart `run.bat`.
- Server won't start → make sure `backend\data\` exists or restart — Step 4 handles it.