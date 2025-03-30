import hashlib
import os
import random
from pathlib import Path

import mr_injector


def get_root_dir() -> Path:
    return Path(mr_injector.__path__[0]).parent

def booleanize(s: bool | str) -> bool:
    if isinstance(s, bool):
        return s
    return s.lower() in ['true', '1', "y", "yes"]

def is_debug() -> bool:
    return booleanize(os.environ.get("DEBUG", False))

def is_presentation_mode() -> bool:
    """Whether the app is started with presentation mode
    During a presentation (e.g. conference) we might want to visualize ui components differently
    """
    return booleanize(os.environ.get("PRESENTATION_MODE", False))

def hash_text(text) -> str:
    # Convert the text to bytes
    text_bytes = text.encode('utf-8')

    # Create a SHA-256 hash object
    hash_object = hashlib.sha256()

    # Update the hash object with the bytes
    hash_object.update(text_bytes)

    # Get the hexadecimal representation of the hash
    hash_hex = hash_object.hexdigest()

    return hash_hex

def get_random_name() -> str:
    first_names=('John','Andy','Joe')
    last_names=('Johnson','Smith','Williams')

    return random.choice(first_names)+" "+random.choice(last_names)
