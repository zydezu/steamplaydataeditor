import glob
import os
import re
import struct

import vdf

from core.models import GameEntry
from core.names import enrich_names, load_app_names

STEAM_PATH = os.path.expanduser("~/.local/share/Steam")

APPID_BLACKLIST = {"236600", "0"}


def parse_shortcuts(path: str) -> dict[str, str]:
    """Parse binary shortcuts.vdf -> { signed_appid_str: display_name }"""
    with open(path, "rb") as f:
        data = f.read()
    shortcuts: dict[str, str] = {}
    offset = 0
    while offset < len(data):
        m = re.search(rb"\x01AppName\x00([^\x00]+)\x00", data[offset:])
        if not m:
            break
        abs_pos = offset + m.start()
        app_name = m.group(1).decode("utf-8", errors="replace")
        ai = data.rfind(b"appid\x00", max(0, abs_pos - 300), abs_pos)
        if ai != -1:
            raw_id = struct.unpack_from("<I", data, ai + 6)[0]
            signed_id = raw_id - 2**32 if raw_id >= 2**31 else raw_id
            shortcuts[str(signed_id)] = app_name
        offset = abs_pos + len(m.group(0))
    return shortcuts


def _find_key(d: dict, key: str):
    for k, v in d.items():
        if k.lower() == key.lower():
            return v
    return None


def _load_apps(localconfig_path: str) -> dict | None:
    with open(localconfig_path, "r", encoding="utf-8", errors="replace") as f:
        config = vdf.load(f, mapper=dict)
    root = _find_key(config, "UserLocalConfigStore") or config
    cur = root
    for part in ["Software", "Valve", "Steam", "Apps"]:
        if not isinstance(cur, dict):
            return None
        cur = _find_key(cur, part)
    return cur


def get_user_dirs() -> list[str]:
    return glob.glob(os.path.join(STEAM_PATH, "userdata", "*"))


def get_user_entries(user_dir: str) -> tuple[str, list[GameEntry], list[str]]:
    """Returns (steam_id, sorted entries, error messages)."""
    steam_id = os.path.basename(user_dir)
    errors: list[str] = []

    localconfig_path = os.path.join(user_dir, "config", "localconfig.vdf")
    if not os.path.exists(localconfig_path):
        return steam_id, [], []

    shortcut_names: dict[str, str] = {}
    shortcuts_path = os.path.join(user_dir, "config", "shortcuts.vdf")
    if os.path.exists(shortcuts_path):
        try:
            shortcut_names = parse_shortcuts(shortcuts_path)
        except Exception as e:
            errors.append(f"shortcuts.vdf: {e}")

    app_names = load_app_names()

    try:
        apps = _load_apps(localconfig_path)
    except Exception as e:
        errors.append(f"localconfig.vdf: {e}")
        return steam_id, [], errors

    if not apps:
        errors.append("couldn't find Apps section in localconfig.vdf")
        return steam_id, [], errors

    entries: list[GameEntry] = []
    for appid, data in apps.items():
        if not isinstance(data, dict):
            continue
        if appid in APPID_BLACKLIST:
            continue
        playtime = data.get("Playtime") or data.get("playtime")
        playtime_2wk = data.get("Playtime2wks") or data.get("playtime2wks")
        last_played = data.get("LastPlayed") or data.get("lastplayed")
        if not playtime and not playtime_2wk:
            continue

        shortcut_name = shortcut_names.get(appid)
        if shortcut_name:
            label = f"{shortcut_name} [non-steam]"
        elif resolved := app_names.get(appid):
            label = resolved
        else:
            label = f"appid {appid}"

        entries.append(
            GameEntry(
                label=label,
                appid=appid,
                playtime=int(playtime or 0),
                playtime_2wk=int(playtime_2wk or 0),
                last_played=last_played or "0",
            )
        )

    entries.sort(key=lambda x: x.playtime, reverse=True)
    enrich_names(entries, app_names)
    return steam_id, entries, errors
