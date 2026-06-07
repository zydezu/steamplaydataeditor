# Steam Play Data Editor

<video alt="Video demonstration" src="https://github.com/user-attachments/assets/0f9e620f-4d4b-40e2-b2e4-009dcf4ecfa0"></video>

A terminal UI for viewing and editing Steam playtime data stored in `localconfig.vdf`, including added non-steam games.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/boysaremoe)

## Features

- Browse all games (including non-steam games) with total playtime, 2-week playtime, and last played date
- Edit total playtime, 2-week playtime, and last played date for any game
- Resolves game names from local Steam cache (`appinfo.vdf`, `appmanifest_*.acf`) and the Steam Store API as a fallback
- Non-Steam shortcuts are resolved from `shortcuts.vdf` and labelled accordingly

## Requirements

- Python 3.10+
- Steam installed at `~/.local/share/Steam`

```
pip install -r requirements.txt
```

Or by using a virtual environment of your choice.

## Usage

```
python main.py
```

Navigate with number keys to select a game, then `T` / `W` / `L` to edit playtime fields. `Q` to quit.
