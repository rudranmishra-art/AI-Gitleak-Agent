import os


def ensure_directories() -> None:
    """Create required runtime directories if they don't exist."""
    for directory in ("logs", "reports"):
        os.makedirs(directory, exist_ok=True)
