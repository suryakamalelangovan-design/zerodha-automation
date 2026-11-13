# Standalone Windows EXE

This project builds the Windows executable on a hosted Windows runner. You do not need Python on your own PC to build or run the final EXE.

1. Create a **private** GitHub repository.
2. Upload all project files and folders to it. Do not upload `.env` or credentials.
3. Open the repository's **Actions** tab.
4. Select **Build Zerodha Dashboard for Windows** and click **Run workflow**.
5. When the run completes, download the `ZerodhaDashboard-Windows` artifact.
6. Extract it. Keep `ZerodhaDashboard.exe`, `.env.example`, and `Start-ZerodhaDashboard.bat` together.
7. Double-click `Start-ZerodhaDashboard.bat`. On first run, it creates `.env` and opens Notepad. Enter your API key and API secret locally, save, and close Notepad.
8. Double-click the launcher again. It starts the dashboard and opens `http://127.0.0.1:8000`.

Registered Kite redirect URL must remain `http://127.0.0.1:8000/callback`.

Keep the repository private. Never upload `.env`, API secrets, access tokens, passwords, PINs or TOTP values. The executable runs locally on `127.0.0.1`; the API secret is read from `.env` beside the EXE and the access token remains in process memory. Do not expose this app to the public internet.
