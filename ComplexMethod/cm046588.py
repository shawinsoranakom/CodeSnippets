def add_scan_folder(path: str) -> dict:
    """Add a directory to the custom scan folder list. Returns the row."""
    if not path or not path.strip():
        raise ValueError("Path cannot be empty")
    normalized = os.path.realpath(os.path.expanduser(path.strip()))

    # Validate the path is an existing, readable directory before persisting.
    if not os.path.exists(normalized):
        raise ValueError("Path does not exist")
    if not os.path.isdir(normalized):
        raise ValueError("Path must be a directory, not a file")
    if not os.access(normalized, os.R_OK | os.X_OK):
        raise ValueError("Path is not readable")

    # On Windows, use normcase for denylist comparison but store the
    # original-cased path so downstream consumers see the native
    # drive-letter casing the user expects (e.g. C:\Models, not c:\models).
    is_win = platform.system() == "Windows"
    check = os.path.normcase(normalized) if is_win else normalized
    for prefix in _denied_path_prefixes():
        if check == prefix or check.startswith(prefix + os.sep):
            raise ValueError(f"Path under {prefix} is not allowed")

    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        # On Windows, use case-insensitive lookup so C:\Models and c:\models
        # dedup correctly while preserving the originally-stored casing.
        if is_win:
            existing = conn.execute(
                "SELECT id, path, created_at FROM scan_folders WHERE path = ? COLLATE NOCASE",
                (normalized,),
            ).fetchone()
        else:
            existing = conn.execute(
                "SELECT id, path, created_at FROM scan_folders WHERE path = ?",
                (normalized,),
            ).fetchone()
        if existing is not None:
            return dict(existing)
        try:
            conn.execute(
                "INSERT INTO scan_folders (path, created_at) VALUES (?, ?)",
                (normalized, now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # duplicate -- fall through to SELECT
        # Use the same collation as the pre-check so we find the row even
        # when a concurrent writer stored it with different casing (Windows).
        fallback_sql = (
            "SELECT id, path, created_at FROM scan_folders WHERE path = ? COLLATE NOCASE"
            if is_win
            else "SELECT id, path, created_at FROM scan_folders WHERE path = ?"
        )
        row = conn.execute(fallback_sql, (normalized,)).fetchone()
        if row is None:
            raise ValueError("Folder was concurrently removed")
        return dict(row)
    finally:
        conn.close()