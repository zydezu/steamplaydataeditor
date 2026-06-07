import glob
import json
import os
import re
import struct
import urllib.request

import vdf

STEAM_PATH = os.path.expanduser("~/.local/share/Steam")
_CACHE_PATH = os.path.join(STEAM_PATH, "appcache", "playtime_names.json")
_STEAM_API = "https://store.steampowered.com/api/appdetails?appids={}&filters=basic"


# local sources
def _names_from_appmanifests() -> dict[str, str]:
    names: dict[str, str] = {}
    for path in glob.glob(os.path.join(STEAM_PATH, "steamapps", "appmanifest_*.acf")):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                data = vdf.load(f)
            state = data.get("AppState") or data.get("appstate") or {}
            appid = state.get("appid") or state.get("AppId")
            name = state.get("name") or state.get("Name")
            if appid and name:
                names[str(appid)] = name
        except Exception:
            pass
    return names


def _names_from_appinfo() -> dict[str, str]:
    """Parse appcache/appinfo.vdf (binary).

    Each record stores fields as: type_byte + field_id (LE uint32) + value.
    Field 1 (uint32) = appid, Field 4 (string) = name.
    """
    path = os.path.join(STEAM_PATH, "appcache", "appinfo.vdf")
    if not os.path.exists(path):
        return {}
    try:
        data = open(path, "rb").read()
    except OSError:
        return {}

    names: dict[str, str] = {}
    for m in re.finditer(rb"\x02\x01\x00\x00\x00(.{4})", data):
        appid = struct.unpack("<I", m.group(1))[0]
        if not (1 <= appid <= 3_000_000):
            continue
        window = data[m.end() : m.end() + 2000]
        next_rec = re.search(rb"\x02\x01\x00\x00\x00", window)
        if next_rec:
            window = window[: next_rec.start()]
        nm = re.search(rb"\x01\x04\x00\x00\x00([^\x00]{1,120})\x00", window)
        if nm:
            names[str(appid)] = nm.group(1).decode("utf-8", errors="replace")
    return names


def load_app_names() -> dict[str, str]:
    """Return {appid_str: name} from all available local sources."""
    names = _names_from_appinfo()
    names.update(_names_from_appmanifests())
    return names


# online lookup/caching
def _load_cache() -> dict[str, str | None]:
    try:
        with open(_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(cache: dict) -> None:
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except OSError:
        pass


def _fetch_name(appid: str) -> str | None:
    """Query Steam Store API for one appid. Returns name or None."""
    try:
        req = urllib.request.Request(
            _STEAM_API.format(appid),
            headers={"User-Agent": "steam-playtime-tool/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        entry = data.get(appid, {})
        if entry.get("success") and entry.get("data"):
            return entry["data"].get("name")
    except Exception:
        pass
    return None


def enrich_names(entries: list, known: dict[str, str]) -> None:
    """For any entry still labeled 'appid XXXXX', try the cache then Steam API."""
    cache = _load_cache()
    dirty = False

    for entry in entries:
        appid = entry.appid
        try:
            if int(appid) <= 0:
                continue
        except ValueError:
            continue

        unknown       = entry.label.startswith("appid ")
        non_ascii     = not unknown and not entry.label.isascii()
        already_combined = "(" in entry.label

        if (not unknown and not non_ascii) or already_combined:
            continue

        # cache hit — stores the Steam API (English) name
        if appid in cache:
            api_name = cache[appid]
            if not api_name:
                continue
            if unknown:
                entry.label = api_name
            elif non_ascii and api_name.isascii() and api_name != entry.label:
                entry.label = f"{entry.label} ({api_name})"
            continue

        # fetch
        api_name = _fetch_name(appid)
        cache[appid] = api_name
        dirty = True
        if api_name:
            if unknown:
                entry.label = api_name
            elif non_ascii and api_name.isascii() and api_name != entry.label:
                entry.label = f"{entry.label} ({api_name})"

    if dirty:
        _save_cache(cache)


# reverse lookup
def appid_from_name(name: str, names: dict[str, str] | None = None) -> str | None:
    """Return the appid string for a given name, or None."""
    if names is None:
        names = load_app_names()
    name_lower = name.lower()
    for appid, n in names.items():
        if n.lower() == name_lower:
            return appid
    return None
