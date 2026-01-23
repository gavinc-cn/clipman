# Clipman

Simple, cross‑machine clipboard sync using a shared JSON file. Clipman watches your system clipboard (text and images) and mirrors changes to a file, while also listening for updates in that file to apply back to your clipboard. Designed for lightweight, private syncing via a network share or a cloud‑synced folder.

## Features
- Syncs plain text and images (PNG base64) between machines
- Uses file locking to avoid write conflicts
- Skips file path drags (text/uri-list starting with file:///)
- Polls every second for clipboard and file changes
- Writes structured JSON with versioning to prevent loops
- Logs activity to `clipman.log` for diagnosis

## Requirements
- Windows 10/11 (tested) and Python 3.8+
- Dependencies (see [requirement.txt](file:///d:/own/github/clipman/requirement.txt)):
  - pyqt5==5.15.11
  - filelock==3.16.1
  - pywin32==308
  - pynput==1.7.7

## Installation
- Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

- Install dependencies:

```bash
pip install -r requirement.txt
```

## Usage
- Choose a shared location for the sync file (e.g., a network share or a cloud folder). Use the same path on all machines.
- Start Clipman, pointing to the shared file:

```bash
python src/clipman_file.py -f \\path\\to\\shared\\sync.json
```

- Run the same command on the other machine(s), using the identical `-f` path. Text and image clipboard contents will begin syncing.

### Command Options
- `-f, --file` Path to the JSON sync file. Default: `sync.json` in the current directory.

## How It Works
- Clipman uses a PyQt event loop to read the system clipboard and a timer to check for changes every second.
- When clipboard content changes, it writes a JSON payload containing:
  - `version` incremented locally
  - `content_type`: `TEXT` or `IMAGE`
  - `data`: text or PNG image encoded as base64
- When the JSON file changes, Clipman reads it, compares versions, and updates the local clipboard if the file version is newer.
- File access is guarded by a lock file to avoid concurrency issues.

Core implementation: [clipman_file.py](file:///d:/own/github/clipman/src/clipman_file.py)

## Logging
- Logs to `clipman.log` in the working directory.
- Useful for troubleshooting and understanding sync behavior.

## Notes and Caveats
- Only text and images are supported.
- Large images produce large JSON; prefer text for heavy usage.
- Ignores `text/uri-list` entries that start with `file:///` to avoid accidental path pastes.
- Cloud‑synced folders may add latency; network shares are recommended for real‑time feel.
- Ensure both machines can read/write the shared location and that the path is identical.

## Security
- Clipboard contents are stored as plain JSON (text) or base64 (images).
- Use a private, access‑controlled location for the sync file.
- Do not use on shared or untrusted machines when copying sensitive data.

## License
- MIT License. See [LICENSE](file:///d:/own/github/clipman/LICENSE).

## Project Structure
- Source: [src/clipman_file.py](file:///d:/own/github/clipman/src/clipman_file.py)
- Dependencies: [requirement.txt](file:///d:/own/github/clipman/requirement.txt)
- Logs: `clipman.log` (created at runtime)

## Roadmap
- Optional HTTPS/WebSocket transport
- Selective sync rules and filters
- System tray UI for quick pause/resume

