# Steam Play Data Editor

https://github.com/user-attachments/assets/8518e879-10ed-4846-b4bc-4a8cd12c5768

A terminal UI for viewing and editing Steam playtime data stored in `localconfig.vdf`, including added non-steam games.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/boysaremoe)

## Features

- Browse all games (including non-steam games) with total playtime, 2-week playtime, and last played date
- Edit the total playtime, 2-week playtime, and last played date for any game
- Resolves game names from local Steam cache (`appinfo.vdf`, `appmanifest_*.acf`) and also the Steam Store API as a fallback
- Non-Steam shortcuts are resolved from `shortcuts.vdf` and labelled accordingly

## Requirements

- Python 3.10+
- Steam installed at `~/.local/share/Steam`

```bash
pip install -r requirements.txt
```

Or, you can also use a virtual environment of your choice.

## Usage

```bash
python main.py
```

Follow on-screen instructions to navigate and edit game data. Use `Q` to quit.
