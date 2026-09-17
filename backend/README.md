# Backend (FastAPI agent server)

Runs on your Windows laptop. No AI model runs here — it calls free cloud LLMs, so the CPU stays at ~2%.

## Run

```bash
setup.bat    # one-time: venv, deps, browser, .env
run.bat      # start the server on :8765
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/chat/send` | Send a prompt to the agent |
| GET | `/api/chat/history` | Recent conversation |
| GET/POST | `/api/jobs` | List / create applications |
| PATCH/DELETE | `/api/jobs/{id}` | Update status / delete |
| GET | `/api/jobs/stats` | Status counts |
| GET | `/api/jobs/due-follow-ups` | Follow-up reminders due |
| POST | `/api/emails/sync` | Pull Gmail messages |
| GET | `/api/emails` | List stored emails |
| GET | `/api/stats/dashboard` | Dashboard aggregates |
| GET/POST/DELETE | `/api/profile` | Saved profile values |
| POST | `/api/auth/gmail/start` | Start Gmail OAuth (returns URL) |
| POST | `/api/auth/gmail/finish` | Exchange code → store token |
| GET | `/api/auth/gmail/status` | Is Gmail connected |
| POST | `/api/auth/browser/login` | Open platform login in a browser |
| POST | `/api/auth/browser/finish-login` | Save the login state |
| GET | `/health` | Liveness check |

All `/api` routes require header `X-API-Key: <API_KEY from .env>`.

## Layout

```
app/
  core/     config, security (DPAPI vault), llm client, agent loop, scheduler
  db/       async SQLModel engine, models
  tools/    gmail, browser (Playwright), tracker, notifier (ntfy)
  api/      routers → services
```

## LLM providers

Set in `.env`. All speak the OpenAI-compatible format:

- OpenRouter — many free models (default preset)
- Groq — very fast free tier
- Gemini — free tier

## Security notes

- Gmail uses OAuth tokens, never the password; tokens live in `data/vault` encrypted with Windows DPAPI.
- The browser profile and login state live under `data/` — treat them as sensitive.
- Only expose the server on `127.0.0.1`, your LAN, or behind Tailscale. `API_KEY` is the only gate.