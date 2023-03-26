from dataclasses import dataclass


@dataclass
class Song:
    url: str
    name: str
    uploader: str
    duration: int
    channel_id: int
