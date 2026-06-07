import os
import sys

from core.display import (
    PAGE_SIZE,
    fmt_last_played,
    fmt_mins,
    print_no_users,
    render_entry_details,
    render_table,
)
from core.editor import parse_date, parse_playtime, write_field
from core.exportimport import export_entries, import_entries
from core.models import GameEntry
from core.reader import STEAM_PATH, get_user_dirs, get_user_entries
from core.ui import C, clear, getch, key_opt


def _prompt(msg: str) -> str:
    print(f"\n  {C.BOLD}{msg}{C.RESET} ", end="", flush=True)
    return input()


def _save_ok(msg: str) -> None:
    print(f"  {C.GREEN}✓  {msg}{C.RESET}")
    print(f"\n  {C.GRAY}Press any key to continue…{C.RESET}", end="", flush=True)
    getch()


def _save_err(msg: str) -> None:
    print(f"  {C.RED}✗  {msg}{C.RESET}")
    print(f"\n  {C.GRAY}Press any key to continue…{C.RESET}", end="", flush=True)
    getch()


def run_edit(user_dir: str, entry: GameEntry) -> None:
    localconfig = os.path.join(user_dir, "config", "localconfig.vdf")

    while True:
        clear()
        render_entry_details(entry)

        key = getch()

        if key == "b":
            return

        elif key == "t":
            clear()
            render_entry_details(entry)
            raw = _prompt("New total playtime  [e.g. 120 / 2h / 2h30m / 2:30]:")
            if raw.strip():
                mins = parse_playtime(raw)
                if mins is None:
                    _save_err(f"Couldn't parse {raw!r} — try 120 / 2h / 2h30m / 2:30")
                else:
                    try:
                        write_field(localconfig, entry.appid, "Playtime", str(mins))
                        entry.playtime = mins
                        _save_ok(f"Total playtime set to {fmt_mins(mins)}")
                    except Exception as e:
                        _save_err(str(e))

        elif key == "w":
            clear()
            render_entry_details(entry)
            raw = _prompt("New 2-week playtime  [e.g. 120 / 2h / 2h30m / 2:30]:")
            if raw.strip():
                mins = parse_playtime(raw)
                if mins is None:
                    _save_err(f"Couldn't parse {raw!r} — try 120 / 2h / 2h30m / 2:30")
                else:
                    try:
                        write_field(localconfig, entry.appid, "Playtime2wks", str(mins))
                        entry.playtime_2wk = mins
                        _save_ok(f"2-week playtime set to {fmt_mins(mins)}")
                    except Exception as e:
                        _save_err(str(e))

        elif key == "l":
            clear()
            render_entry_details(entry)
            raw = _prompt("New last-played date  [YYYY-MM-DD or 'now']:")
            if raw.strip():
                ts = parse_date(raw)
                if ts is None:
                    _save_err(f"Couldn't parse {raw!r} — try 2024-06-01 or now")
                else:
                    try:
                        write_field(localconfig, entry.appid, "LastPlayed", str(ts))
                        entry.last_played = str(ts)
                        _save_ok(
                            f"Last played set to {fmt_last_played(entry.last_played)}"
                        )
                    except Exception as e:
                        _save_err(str(e))


def run_export(user_dir: str, steam_id: str, entries: list[GameEntry]) -> None:
    clear()
    try:
        folder = export_entries(user_dir, steam_id, entries)
        _save_ok(f"Exported {len(entries)} entries to  {folder}/")
    except Exception as e:
        _save_err(str(e))


def run_import(user_dir: str) -> list[GameEntry] | None:
    clear()
    print(f"\n  {C.BOLD}Import from JSON{C.RESET}")
    raw = _prompt("Path to playtime.json:")
    path = raw.strip()
    if not path:
        return None
    try:
        count, errors = import_entries(user_dir, path)
        for err in errors:
            print(f"  {C.YELLOW}⚠  {err}{C.RESET}")
        _save_ok(f"Imported {count} entries  (localconfig.vdf.bak created)")
        steam_id = os.path.basename(user_dir)
        _, entries, _ = get_user_entries(user_dir)
        return entries
    except Exception as e:
        _save_err(str(e))
        return None


def run_pick_and_edit(
    user_dir: str, entries: list[GameEntry], page: int, steam_id: str
) -> None:
    clear()
    render_table(entries, page, steam_id)

    raw = _prompt(f"Enter game number to edit  (1–{len(entries)})  or  [B]ack:")
    raw = raw.strip().lower()
    if not raw or raw == "b":
        return

    try:
        idx = int(raw) - 1
    except ValueError:
        return

    if not (0 <= idx < len(entries)):
        print(f"  {C.RED}Number out of range{C.RESET}")
        print(f"\n  {C.GRAY}Press any key…{C.RESET}", end="", flush=True)
        getch()
        return

    run_edit(user_dir, entries[idx])


def run_user_view(
    user_dir: str, steam_id: str, entries: list[GameEntry], errors: list[str]
) -> None:
    page = 0

    while True:
        clear()

        for err in errors:
            print(f"  {C.RED}[!] {err}{C.RESET}")

        total_pages = render_table(entries, page, steam_id)

        opts = [key_opt("E", "dit"), key_opt("X", "port"), key_opt("I", "mport")]
        if total_pages > 1:
            opts += [key_opt("←", ""), key_opt("→", " page")]
        opts.append(key_opt("Q", "uit"))

        print(f"\n  {C.BOLD}What would you like to do?{C.RESET}")
        print("  " + "   ".join(opts))
        print(f"  {C.GRAY}Press the corresponding key{C.RESET}", end="", flush=True)

        key = getch()

        if key == "q":
            return
        elif key == "e":
            run_pick_and_edit(user_dir, entries, page, steam_id)
        elif key == "x":
            run_export(user_dir, steam_id, entries)
        elif key == "i":
            refreshed = run_import(user_dir)
            if refreshed is not None:
                entries = refreshed
        elif key in ("right", "n"):
            page = min(page + 1, total_pages - 1)
        elif key in ("left", "p"):
            page = max(page - 1, 0)


def main() -> None:
    if not sys.stdin.isatty():
        from core.display import render_table as _rt

        for user_dir in get_user_dirs():
            steam_id, entries, errors = get_user_entries(user_dir)
            if errors or entries:
                _rt(entries, 0, steam_id)
                for err in errors:
                    print(f"  {C.RED}[!] {err}{C.RESET}")
        return

    user_dirs = get_user_dirs()
    if not user_dirs:
        print_no_users(STEAM_PATH)
        return

    for user_dir in sorted(user_dirs):
        steam_id, entries, errors = get_user_entries(user_dir)
        if not errors and not entries:
            continue
        run_user_view(user_dir, steam_id, entries, errors)
