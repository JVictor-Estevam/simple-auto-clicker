# Simple AutoClicker

A small desktop utility for Windows and macOS that repeats mouse clicks or keyboard input on a timer. The interface is built with CustomTkinter; input simulation uses [pynput](https://github.com/moses-palmer/pynput).

## What it does

You choose an action (left click or a single key), set the interval in seconds, and optionally cap how many times it runs. While automation is active, press **F7** to stop immediately. If your automated key is F7, the emergency stop moves to **F8** so the two do not conflict.

Mouse clicks can follow the cursor or target fixed screen coordinates. Coordinates support multi-monitor setups, including negative X/Y values when a monitor sits to the left or above the primary display.

Settings are stored locally and restored on the next launch.

## Requirements

* Python 3.10 or newer
* Windows or macOS (Linux may work but is not tested)

## Download (Windows)

Pre-built binaries are published on [GitHub Releases](https://github.com/JVictor-Estevam/simple-auto-clicker/releases).

1. Open the latest **v1.0.0** (or newer) release.
2. Download **Simple AutoClicker.exe** under *Assets*.
3. Run the file. No Python installation required.

Each release also includes **Source code** archives (`zip` and `tar.gz`) generated automatically from the tagged commit.

Windows may show SmartScreen on first run because the executable is not code-signed. Use *More info → Run anyway* if you trust this repository.

## Installation (from source)

Clone the repository and install dependencies:

```bash
git clone https://github.com/JVictor-Estevam/simple-auto-clicker.git
cd simple-auto-clicker
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

On Windows, some environments require running the terminal as administrator for global hotkeys and input simulation to work reliably.

## Building the Windows executable

Install development dependencies, verify icon assets, then build:

```bash
pip install -r requirements-dev.txt
python scripts/build_icon.py
pyinstaller build.spec --noconfirm
```

Icon files live in `simple_autoclicker/files/`. Before packaging, `scripts/build_icon.py` crops transparent padding, flattens the PNG onto an opaque background, and rebuilds `autoclicker_pro_v5.ico` with all Windows sizes (16 through 256).

The executable is written to `dist/Simple AutoClicker.exe`. Build artifacts under `build/` and `dist/` are not committed; publish the `.exe` via [GitHub Releases](https://github.com/JVictor-Estevam/simple-auto-clicker/releases) instead.

To cut a release after building:

```powershell
git tag v1.0.0
git push origin v1.0.0
gh release create v1.0.0 "dist/Simple AutoClicker.exe" --title "v1.0.0" --notes "First public release."
```

## Settings file

Preferences are saved as JSON:

| Platform | Location |
|----------|----------|
| Windows  | `%APPDATA%\SimpleAutoClicker\settings.json` |
| macOS/Linux | `~/.simple-autoclicker/settings.json` |

Stored fields: action type, mouse mode, coordinates, key, interval, repeat limit, and repeat count. Running state is not persisted.

## Project layout

```
simple-auto-clicker/
├── main.py                      Entry point
├── build.spec                   PyInstaller configuration
├── requirements.txt
├── requirements-dev.txt         Build tools (optional)
├── scripts/
│   └── build_icon.py            Verify icon assets before packaging
└── simple_autoclicker/
    ├── files/
    │   ├── autoclicker_pro_v5.svg   Source artwork (design reference)
    │   ├── autoclicker_v5_256.png   Opaque 256×256 raster (ICO source)
    │   └── autoclicker_pro_v5.ico   Windows executable / window icon
    ├── constants.py             Theme, key map, shared configuration
    ├── resources.py             Asset path resolution
    ├── settings.py              Load and save user preferences
    ├── screen.py                Virtual desktop bounds (multi-monitor)
    ├── validation.py            Numeric input rules for the UI
    ├── engine.py                Background click/key loop (AutoClicker)
    └── ui/
        └── app.py               CustomTkinter application window
```

### How the pieces connect

`main.py` starts the `App` window. When you press Start, `App` validates the form, starts a global stop listener, and hands work to `AutoClicker`, which runs on a daemon thread. UI updates (action counter, status text) are scheduled back onto the main thread with `after()`.

To extend the tool, typical touch points are:

* **New automation action** — `engine.py` (`AutoClicker._loop`) and the Action panel in `ui/app.py`
* **New UI control** — `ui/app.py` layout builders plus `settings.py` if the value should persist
* **Cross-platform behavior** — `screen.py` for geometry, `constants.py` for key names
* **Branding** — replace files in `simple_autoclicker/files/`, then run `python scripts/build_icon.py`

## Third-party licenses

This project depends on:

* **customtkinter** — MIT License
* **pynput** — LGPLv3 (see the [pynput repository](https://github.com/moses-palmer/pynput) for details)

Source code in this repository is released under the MIT License. See [LICENSE](LICENSE).

## Disclaimer

Simple AutoClicker is provided as-is for legitimate personal automation tasks such as accessibility assistance, repetitive testing, or productivity workflows you control.

You are responsible for how you use this software. Automating input in games, commercial services, or other software may violate their terms of use and can result in account restrictions or other consequences. The authors accept no liability for misuse, data loss, or damage arising from the use of this tool.

Use it only where you have permission, and stop automation with **F7** (or **F8** when F7 is assigned as the automated key) when you are done.
