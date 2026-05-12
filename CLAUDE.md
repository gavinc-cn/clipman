# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clipman is a single-file Python tool for cross-machine clipboard sync via a shared JSON file (network share or cloud folder). It supports plain text and PNG images.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirement.txt
```

## Running

```bash
python src/clipman_file.py -f \\path\to\shared\sync.json
```

Default sync file is `sync.json` in the current directory if `-f` is omitted.

## Architecture

The entire implementation lives in [src/clipman_file.py](src/clipman_file.py) as a single `ClipboardSync` class:

- **PyQt5 event loop** drives everything — `QApplication.exec_()` is the main loop, and a `QTimer` fires `check_clipboard_and_file()` every second.
- **Clipboard → file**: `check_clipboard()` reads `QApplication.clipboard()` mime data, detects changes by comparing against `last_clipboard_text` / `last_clipboard_image`, increments `local_version`, and writes a JSON payload (`{version, content_type, data}`) via `write_to_file()`.
- **File → clipboard**: `check_file()` detects file changes via mtime, reads the JSON, and calls `update_clipboard()` only when `file_version > local_version` to prevent sync loops.
- **Concurrency**: `FileLock` (from `filelock`) guards all file reads and writes using a `.lock` sidecar file. Lock timeout is 10 seconds.
- **Image encoding**: PNG bytes are base64-encoded for storage in JSON; on restore, multiple MIME types (`image/png`, `image/jpeg`, `image/bmp`) are set for compatibility.
- **Loop prevention**: version numbering — each machine tracks its own `local_version` and only applies file updates with a strictly higher version.

## Platform

Windows 10/11 only (`pywin32` dependency). Python 3.8+.

## Logs

Runtime log written to `clipman.log` in the working directory (overwritten each run).
