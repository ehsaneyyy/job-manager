# JobBot web app

React + Vite + Tailwind app that runs in any browser (Windows, Android, iOS). Used as the UI for the desktop widget and Android bubble too.

## Run

```bash
npm install
npm run dev
```

Open http://localhost:5173. `vite.config.ts` binds to `0.0.0.0` so phones on the same Wi-Fi can open it too.

## Features

- **Chat** — talk to the agent ("check my inbox", "apply to this job: <url>").
- **Stats** — application counts, reply rate, email counters.
- **Jobs** — add, change status, delete; follow-up dates visible.
- **Emails** — sync Gmail inbox, view summaries.
- **Settings** — API key + base URL for the backend, Gmail OAuth connect.

## Pointing it at the backend

The API base URL and key default to the local server; change them in Settings. From a phone, set
the base URL to `http://<PC-IP>:8765`.

## PWA

`public/manifest.webmanifest` + icon make the app "installable" from Android Chrome
(Add to Home screen).