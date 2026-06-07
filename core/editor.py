import datetime
import re
import shutil

import vdf


def _find_key(d: dict, key: str) -> tuple[str | None, object]:
    for k, v in d.items():
        if k.lower() == key.lower():
            return k, v
    return None, None


def _navigate_to_apps(config: dict) -> dict | None:
    _, root = _find_key(config, "UserLocalConfigStore")
    cur = root or config
    for part in ["Software", "Valve", "Steam", "Apps"]:
        _, cur = _find_key(cur, part)
        if cur is None:
            return None
    return cur


def write_field(localconfig_path: str, appid: str, field: str, value: str) -> None:
    """Update a single field for appid and write back. Creates .bak before touching."""
    shutil.copy2(localconfig_path, localconfig_path + ".bak")

    with open(localconfig_path, "r", encoding="utf-8", errors="replace") as f:
        config = vdf.load(f, mapper=dict)

    apps = _navigate_to_apps(config)
    if apps is None:
        raise RuntimeError("cannot find Apps section in localconfig.vdf")

    app_data = apps.get(appid)
    if app_data is None:
        raise KeyError(f"appid {appid!r} not found in localconfig.vdf")

    for k in list(app_data.keys()):
        if k.lower() == field.lower():
            app_data[k] = value
            break
    else:
        app_data[field] = value

    with open(localconfig_path, "w", encoding="utf-8") as f:
        vdf.dump(config, f, pretty=True)


def parse_playtime(s: str) -> int | None:
    """Parse '120', '2h', '2h30m', '2:30' -> total minutes. None if unrecognised."""
    s = s.strip().lower()
    if m := re.match(r"^(\d+)[h:](\d*)m?$", s):
        return int(m.group(1)) * 60 + int(m.group(2) or 0)
    if m := re.match(r"^(\d+)m$", s):
        return int(m.group(1))
    if m := re.match(r"^(\d+)$", s):
        return int(m.group(1))
    return None


def parse_date(s: str) -> int | None:
    """Parse 'YYYY-MM-DD' or 'now' -> Unix timestamp int. None if unrecognised."""
    s = s.strip().lower()
    if s == "now":
        return int(datetime.datetime.now().timestamp())
    try:
        return int(datetime.datetime.strptime(s, "%Y-%m-%d").timestamp())
    except ValueError:
        return None
