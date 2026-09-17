# Android floating bubble

A small Android app that shows a floating bubble (overlay) which opens the JobBot web app in a full-screen view. Connects to the backend on your PC over Wi-Fi or Tailscale.

## How it works

1. App requests the "Display over other apps" permission (`ACTION_MANAGE_OVERLAY_PERMISSION`).
2. A small bubble floats over any app.
3. Tapping the bubble opens a WebView loading `http://<your-pc-ip>:8765`.
4. The WebView uses the same API key + base URL you configured in Settings.

## Source layout (Kotlin, single activity)

```
android/
├─ app/src/main/AndroidManifest.xml
├─ app/src/main/java/dev/jobmanager/BubbleService.kt   (overlay bubble + WebView window)
├─ app/src/main/java/dev/jobmanager/MainActivity.kt    (permission + service launcher)
└─ app/build.gradle.kts
```

## Key points

- Overlay: `WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY`, `FLAG_NOT_FOCUSABLE` bubble.
- Jump to settings: `Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION)`.
- WebView must allow `file://` or the full URL; enable JS + DOM storage.
- Add `android.permission.SYSTEM_ALERT_WINDOW`, `android.permission.INTERNET`.

## Build

Open in Android Studio, sync Gradle, run on device/emulator. No subscription or Play account needed to sideload the APK.

## Phone + PC connection

- Same Wi-Fi: use `http://<pc-ip>:8765` (see `ipconfig` on the PC, local address).
- Away from home: install Tailscale on both, use the MagicDNS name `http://<pc-hostname>:8765`.
- Keep the PC's `.env` `API_KEY` secret — it is the only credential protecting the server.