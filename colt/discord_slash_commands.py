import os
from pathlib import Path


def play_doom():
    doom_file = Path(__file__).parent / "assets" / "images" / "doom.gif"
    doom_path = os.path.abspath(doom_file)
    return doom_path
