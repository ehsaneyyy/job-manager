# Windows floating widget (Tauri)

A small always-on-top window that loads the web app, giving you a floating JobBot over any other application.

## Why Tauri

Tauri ships a ~3 MB `.exe` with no Node runtime bundled. It wraps the built `web/` app and adds a "always on top" toggle and a tiny chat bubble.

## Prerequisites

- Rust (https://rustup.rs) — only needed to compile, not to run
- Node.js

## Build

```bash
cd desktop
npm install
npm run tauri dev
bun --vite build
npm run tauri build
```

## Floating chat window

`src-tauri/src-tauri/src/main.rs` creates the window with:

- `always_on_top(true)`
- compact, undecorated window on the bottom-right of the screen
- loads `TAURI_DEV_URL` in dev or the bundled web build in production

To open from anywhere, add a global shortcut with `tauri-plugin-global-shortcut` (e.g. `Ctrl+Alt+J`).

## Notes

- The widget talks to the same backend as the phone; set the API base + key in the web Settings screen.
- The web app window is movable, so you can pin it beside your browser while job hunting.