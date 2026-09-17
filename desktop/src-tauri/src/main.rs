#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, WebviewUrl, WebviewWindow, WebviewWindowBuilder};

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let window = build_floating_window(app.handle())?;
            let _ = window;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("failed to run JobBot widget");
}

fn build_floating_window(app_handle: &tauri::AppHandle) -> tauri::Result<WebviewWindow> {
    WebviewWindowBuilder::new(app_handle, "jobbot", WebviewUrl::default())
        .title("JobBot")
        .inner_size(380.0, 560.0)
        .min_inner_size(320.0, 420.0)
        .resizable(true)
        .always_on_top(true)
        .visible(true)
        .build()
}