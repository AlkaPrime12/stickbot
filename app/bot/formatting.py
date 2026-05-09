RESET = "\x1b[0m"
GREEN = "\x1b[1;32m"
RED = "\x1b[1;31m"
YELLOW = "\x1b[1;33m"
CYAN = "\x1b[1;36m"


def ansi_block(text: str) -> str:
    return f"```ansi\n{text}\n```"


def success(text: str) -> str:
    return ansi_block(f"{GREEN}{text}{RESET}")


def error(text: str) -> str:
    return ansi_block(f"{RED}{text}{RESET}")


def info(text: str) -> str:
    return ansi_block(f"{CYAN}{text}{RESET}")


def warning(text: str) -> str:
    return ansi_block(f"{YELLOW}{text}{RESET}")


# Preset: kind -> ansi color prefix (before text)
ANSI_PRESETS: dict[str, dict[str, str]] = {
    "default": {
        "ok": GREEN,
        "error": RED,
        "warn": YELLOW,
        "info": CYAN,
    },
    "high_contrast": {
        "ok": "\x1b[1;92m",
        "error": "\x1b[1;91m",
        "warn": "\x1b[1;93m",
        "info": "\x1b[1;96m",
    },
    "muted": {
        "ok": "\x1b[32m",
        "error": "\x1b[31m",
        "warn": "\x1b[33m",
        "info": "\x1b[36m",
    },
    "mono": {
        "ok": "\x1b[1;37m",
        "error": "\x1b[1;30m",
        "warn": "\x1b[37m",
        "info": "\x1b[0;37m",
    },
}


def styled_message(preset: str, kind: str, text: str) -> str:
    """Formato ANSI según preset de guild (compatible con bloques ```ansi``` en Discord desktop)."""
    p = ANSI_PRESETS.get(preset or "default", ANSI_PRESETS["default"])
    color = p.get(kind, p.get("info", CYAN))
    return ansi_block(f"{color}{text}{RESET}")
