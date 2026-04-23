def safe_makedirs(name, mode=0o777, exist_ok=False):
    """Create directories recursively with explicit `mode` on each level."""
    makedirs(name=name, mode=mode, exist_ok=exist_ok, parent_mode=mode)