import sys
import termios
import tty


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


def getch() -> str:
    """Read one keypress. Returns lowercase char, 'up'/'down'/'left'/'right', or 'esc'."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            sys.stdin.read(1)  # [
            seq = sys.stdin.read(1)
            return {"A": "up", "B": "down", "C": "right", "D": "left"}.get(seq, "esc")
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def clear() -> None:
    print("\033[H\033[J", end="", flush=True)


def key_opt(key: str, label: str, note: str = "") -> str:
    """Format a coloured key hint: [E]dit  or  [E]dit (3)"""
    note_str = f" {C.GRAY}({note}){C.RESET}" if note else ""
    return f"[{C.YELLOW}{key}{C.RESET}]{label}{note_str}"
