# Job Manager

An AI job-hunting assistant that tracks applications, coaches your inbox, and helps you apply on LinkedIn and Indeed from Windows and Android — 100% free.

## Quick start

Follow [`SETUP.md`](SETUP.md) — full beginner guide with zero coding required. It covers the free AI provider key, Gmail connection, browser login, and phone access.

## How it works

- Your laptop runs a lightweight server (no AI model runs locally, so no heat).
- The server talks to free cloud AI (Groq / Gemini / OpenRouter) for thinking and writing.
- You control it from any phone or PC browser, or from the floating widgets.
- Everything is stored in one local SQLite database: jobs, emails, chat history, and stats.

## Features

- Chat prompt: "apply to this job" and the agent plans, executes, and reports.
- Gmail copilot: check inbox, summarize, draft, reply, send, follow-ups.
- LinkedIn / Indeed: fill applications with your saved profile and answer screening questions.
- Tracking: applied, replied, interview, declined, accepted, no-response — with charts.
- Review-before-submit by default. Full-auto exists but is your choice and your risk.
- Works on Windows and Android.

## Layout

- `backend/` — FastAPI agent server (Windows, light CPU)
- `web/` — React web app (any browser; used by both wrappers)
- `desktop/` — tiny Windows floating widget (Tauri)
- `android/` — Android floating bubble app

## Legal note

Auto-applying and bot-answering on LinkedIn and Indeed violates their Terms of Service and can get accounts banned. Use review-before-submit mode so you stay in control.

## Privacy

With free cloud AI, the text of your resume, emails, and job descriptions passes through the AI provider (Groq / Google / OpenRouter). A dedicated job-hunting Gmail with a redacted resume is recommended. API keys and Gmail tokens are stored encrypted on your machine.