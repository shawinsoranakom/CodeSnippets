def move_aside_file(path):
    """Move a file aside if it exists; restore it on completion"""
    moved = False
    if os.path.exists(path):
        os.rename(path, f"{path}.bak")
        moved = True

    try:
        yield None
    finally:
        if moved:
            os.rename(f"{path}.bak", path)