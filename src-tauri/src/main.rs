// Vo-Gen-Flow Tauri v2 Desktop Host Shell
// Registers global shortcut Ctrl+Shift+V / Cmd+Shift+V to toggle recording anywhere on OS

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, Emitter};

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let handle = app.handle().clone();
            
            // Register Global Shortcut: Ctrl+Shift+V / Cmd+Shift+V
            #[cfg(desktop)]
            {
                use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutState};
                let shortcut: Shortcut = "CommandOrControl+Shift+V".parse().unwrap();
                let _ = app.global_shortcut().on_shortcut(shortcut, move |_app, _shortcut, event| {
                    if event.state() == ShortcutState::Pressed {
                        if let Some(window) = handle.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                            let _ = window.emit("toggle-global-recording", ());
                        }
                    }
                });
            }

            println!("[Vo-Gen-Flow] Native desktop engine initialized successfully.");
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("Error occurred while launching Vo-Gen-Flow desktop shell");
}
