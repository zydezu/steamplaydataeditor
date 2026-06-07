import datetime
import json
import os
import shutil
import zipfile

from core.models import GameEntry


def export_entries(user_dir: str, steam_id: str, entries: list[GameEntry]) -> str:
    """Write playtime.json + VDF backups into a zip. Returns the zip path."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = f"steam_export_{steam_id}_{ts}"
    os.makedirs(folder, exist_ok=True)

    data = {
        "steam_id": steam_id,
        "exported_at": datetime.datetime.now().isoformat(),
        "entries": [
            {
                "appid": e.appid,
                "label": e.label,
                "playtime": e.playtime,
                "playtime_2wk": e.playtime_2wk,
                "last_played": e.last_played,
            }
            for e in entries
        ],
    }
    with open(os.path.join(folder, "playtime.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    for filename in ("localconfig.vdf", "shortcuts.vdf"):
        src = os.path.join(user_dir, "config", filename)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(folder, filename))

    zip_path = folder + ".zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(folder):
            zf.write(os.path.join(folder, fname), os.path.join(folder, fname))
    shutil.rmtree(folder)

    return zip_path


def _load_json(path: str) -> dict:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as zf:
            name = next((n for n in zf.namelist() if n.endswith("playtime.json")), None)
            if not name:
                raise FileNotFoundError("playtime.json not found inside zip")
            with zf.open(name) as f:
                return json.load(f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def import_entries(user_dir: str, json_path: str) -> tuple[int, list[str]]:
    """Apply playtime.json back to localconfig.vdf. Returns (updated_count, errors)."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    from core.editor import bulk_write_entries

    localconfig = os.path.join(user_dir, "config", "localconfig.vdf")
    return bulk_write_entries(localconfig, data.get("entries", []))
