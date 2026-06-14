"""Resolve bundled asset paths for development and PyInstaller builds."""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent

# Raster icons live in simple_autoclicker/files/ (opaque PNG + ICO for Windows).
_ICON_PNG = "autoclicker_v5_256.png"
_ICON_ICO = "autoclicker_pro_v5.ico"

_ALIASES = {
    "icon.png": _ICON_PNG,
    "icon.ico": _ICON_ICO,
}


def asset_path(name: str) -> Path:
    """Return the path to an asset inside simple_autoclicker/files/."""
    filename = _ALIASES.get(name, name)
    candidates: list[Path] = []

    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "simple_autoclicker" / "files" / filename)

    candidates.append(_PACKAGE_ROOT / "files" / filename)

    for path in candidates:
        if path.is_file():
            return path
    return candidates[-1]
