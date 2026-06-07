import datetime

from rich import box
from rich.box import Box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from core.models import GameEntry
from core.ui import C

_SPLIT_HEAD = Box("    \n    \n ─  \n    \n    \n    \n    \n    \n")
console = Console()
PAGE_SIZE = 20


# formatting helpers
def fmt_mins(mins: int) -> str:
    if mins == 0:
        return "-"
    return f"{mins // 60}h {mins % 60:02d}m" if mins >= 60 else f"{mins}m"


def fmt_last_played(ts_str: str) -> str:
    try:
        ts = int(ts_str)
        if ts == 0:
            return "never"
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return ts_str or "?"


def _playtime_style(mins: int) -> str:
    if mins == 0:
        return "dim"
    if mins < 60:  # < 1 h
        return "rgb(134,239,172)"
    if mins < 600:  # 1 h - 10 h
        return "rgb(74,222,128)"
    if mins < 3000:  # 10 h - 50 h
        return "rgb(34,197,94)"
    if mins < 6000:  # 50 h - 100 h
        return "rgb(22,163,74)"
    return "bold rgb(21,128,61)"  # 100 h+


def _last_played_rich(ts_str: str) -> Text:
    try:
        ts = int(ts_str)
        if ts == 0:
            return Text("never", style="dim")
        dt = datetime.datetime.fromtimestamp(ts)
        days = (datetime.datetime.now() - dt).days
        label = dt.strftime("%Y-%m-%d")
        if days < 7:
            style = "bold rgb(240,180,255)"  # light pink
        elif days < 30:
            style = "rgb(200,120,240)"  # pink-purple
        elif days < 365:
            style = "rgb(140,70,200)"  # purple
        else:
            style = "dim"
        return Text(label, style=style)
    except (ValueError, OSError):
        return Text(ts_str, style="dim")


def _label_rich(label: str) -> Text:
    if "[non-steam]" in label:
        name = label[: label.index(" [non-steam]")]
        t = Text(name)
        t.append(" (non-steam)", style="rgb(255,252,190)")
        return t
    if not label.isascii() and label.endswith(")") and " (" in label:
        idx = label.rindex(" (")
        t = Text(label[:idx])
        t.append(label[idx:], style="rgb(255,182,193)")
        return t
    return Text(label)


# main table view
def render_table(entries: list[GameEntry], page: int, steam_id: str) -> int:
    """Print paginated table. Returns total page count."""
    total_pages = max(1, (len(entries) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    slice_ = entries[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    start_idx = page * PAGE_SIZE

    table = Table(
        box=_SPLIT_HEAD,
        show_header=True,
        header_style="bold magenta",
        padding=(0, 1, 0, 0),
    )
    table.add_column("#", justify="right", style="dim", min_width=3)
    table.add_column("Game", min_width=72, no_wrap=False)
    table.add_column("App ID", justify="right", style="dim", min_width=13)
    table.add_column("Total", justify="right", min_width=9)
    table.add_column("2 Weeks", justify="right", min_width=9)
    table.add_column("Last Played", justify="right", min_width=12)

    for i, entry in enumerate(slice_):
        twk = entry.playtime_2wk
        appid_cell = Text(entry.appid, style="dim")

        table.add_row(
            str(start_idx + i + 1),
            _label_rich(entry.label),
            appid_cell,
            Text(fmt_mins(entry.playtime), style=_playtime_style(entry.playtime)),
            Text(fmt_mins(twk), style="cyan" if twk > 0 else "dim"),
            _last_played_rich(entry.last_played),
        )

    for _ in range(PAGE_SIZE - len(slice_)):
        table.add_row("", "", "", "", "", "")

    total_mins = sum(e.playtime for e in entries)
    print(f"\n  {C.BOLD}{C.BLUE}Steam User  {C.WHITE}{steam_id}{C.RESET}")
    console.print(table)
    print(
        f"  {C.GRAY}{len(entries)} games  ·  {C.RESET}"
        f"{C.BOLD}{fmt_mins(total_mins)}{C.RESET}{C.GRAY} total"
        + (f"  ·  page {page + 1}/{total_pages}" if total_pages > 1 else "")
        + C.RESET
    )
    return total_pages


# edit detail screen
def render_entry_details(entry: GameEntry) -> None:
    print(f"\n  {C.BOLD}{C.CYAN}{'─' * 56}{C.RESET}")
    if "[non-steam]" in entry.label:
        _name = entry.label[: entry.label.index(" [non-steam]")]
        _tag = f"\033[38;2;255;252;190m (non-steam){C.RESET}"
    else:
        _name, _tag = entry.label, ""
    print(f"  {C.BOLD}Editing:{C.RESET}  {_name}{_tag}")
    print(f"  {C.BOLD}{C.CYAN}{'─' * 56}{C.RESET}\n")
    print(
        f"  [{C.YELLOW}T{C.RESET}]otal playtime   "
        f"{C.GREEN}{fmt_mins(entry.playtime):>10}{C.RESET}  "
        f"{C.GRAY}({entry.playtime} mins){C.RESET}"
    )
    print(
        f"  [{C.YELLOW}W{C.RESET}]eeks playtime   "
        f"{C.CYAN}{fmt_mins(entry.playtime_2wk):>10}{C.RESET}  "
        f"{C.GRAY}({entry.playtime_2wk} mins){C.RESET}"
    )
    print(
        f"  [{C.YELLOW}L{C.RESET}]ast played      "
        f"{C.WHITE}{fmt_last_played(entry.last_played):>10}{C.RESET}"
    )
    print(f"\n  [{C.YELLOW}B{C.RESET}]ack\n")
    print(f"  {C.GRAY}Press key to select a field{C.RESET}")


# misc
def print_no_users(steam_path: str) -> None:
    print(
        f"\n  {C.RED}No userdata found under{C.RESET} {C.YELLOW}{steam_path}{C.RESET}"
    )
