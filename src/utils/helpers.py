import os
from pathlib import Path

def ensure_dir_exists(directory_path: str) -> None:
    """Ensure that a directory exists, create it if it doesn't"""
    Path(directory_path).mkdir(parents=True, exist_ok=True)

def get_file_extension(filename: str) -> str:
    """Get the extension of a file"""
    return os.path.splitext(filename)[1].lower()
