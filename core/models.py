from dataclasses import dataclass


@dataclass
class GameEntry:
    label: str
    appid: str
    playtime: int  # total minutes
    playtime_2wk: int  # last 2 weeks, minutes
    last_played: str  # unix timestamp string or "0"
