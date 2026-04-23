def cleanup_stale_project_dirs(encoded_cwd: str | None = None) -> int:
    """Remove CLI project directories older than ``_STALE_PROJECT_DIR_SECONDS``.

    Each CoPilot SDK turn creates a unique ``~/.claude/projects/<encoded-cwd>/``
    directory.  These are intentionally kept across turns so the model can read
    tool-result files via ``--resume``.  However, after a session ends they
    become stale.  This function sweeps old ones to prevent unbounded disk
    growth.

    When *encoded_cwd* is provided the sweep is scoped to that single
    directory, making the operation safe in multi-tenant environments where
    multiple copilot sessions share the same host.  Without it the function
    falls back to sweeping all directories matching the copilot naming pattern
    (``-tmp-copilot-``), which is only safe for single-tenant deployments.

    Returns the number of directories removed.
    """
    _pbase = projects_base()
    if not os.path.isdir(_pbase):
        return 0

    now = time.time()
    removed = 0

    # Scoped mode: only clean up the one directory for the current session.
    if encoded_cwd:
        target = Path(_pbase) / encoded_cwd
        if not target.is_dir():
            return 0
        # Guard: only sweep copilot-generated dirs.
        if "-tmp-copilot-" not in target.name:
            logger.warning(
                "[Transcript] Refusing to sweep non-copilot dir: %s", target.name
            )
            return 0
        try:
            # st_mtime is used as a proxy for session activity. Claude CLI writes
            # its JSONL transcript into this directory during each turn, so mtime
            # advances on every turn. A directory whose mtime is older than
            # _STALE_PROJECT_DIR_SECONDS has not had an active turn in that window
            # and is safe to remove (the session cannot --resume after cleanup).
            age = now - target.stat().st_mtime
        except OSError:
            return 0
        if age < _STALE_PROJECT_DIR_SECONDS:
            return 0
        try:
            shutil.rmtree(target, ignore_errors=True)
            removed = 1
        except OSError:
            pass
        if removed:
            logger.info(
                "[Transcript] Swept stale CLI project dir %s (age %ds > %ds)",
                target.name,
                int(age),
                _STALE_PROJECT_DIR_SECONDS,
            )
        return removed

    # Unscoped fallback: sweep all copilot dirs across the projects base.
    # Only safe for single-tenant deployments; callers should prefer the
    # scoped variant by passing encoded_cwd.
    try:
        entries = Path(_pbase).iterdir()
    except OSError as e:
        logger.warning("[Transcript] Failed to list projects dir: %s", e)
        return 0

    for entry in entries:
        if removed >= _MAX_PROJECT_DIRS_TO_SWEEP:
            break
        # Only sweep copilot-generated dirs (pattern: -tmp-copilot- or
        # -private-tmp-copilot-).
        if "-tmp-copilot-" not in entry.name:
            continue
        if not entry.is_dir():
            continue
        try:
            # See the scoped-mode comment above: st_mtime advances on every turn,
            # so a stale mtime reliably indicates an inactive session.
            age = now - entry.stat().st_mtime
        except OSError:
            continue
        if age < _STALE_PROJECT_DIR_SECONDS:
            continue

        try:
            shutil.rmtree(entry, ignore_errors=True)
            removed += 1
        except OSError:
            pass

    if removed:
        logger.info(
            "[Transcript] Swept %d stale CLI project dirs (older than %ds)",
            removed,
            _STALE_PROJECT_DIR_SECONDS,
        )
    return removed