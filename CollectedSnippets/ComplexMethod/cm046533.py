async def browse_folders(
    path: Optional[str] = Query(
        None,
        description = (
            "Directory to list. If omitted, defaults to the current user's "
            "home directory. Tilde (`~`) and relative paths are expanded. "
            "Must resolve inside the allowlist of browseable roots (HOME, "
            "HF cache, Studio dirs, registered scan folders, well-known "
            "model dirs)."
        ),
    ),
    show_hidden: bool = Query(
        False,
        description = "Include entries whose name starts with a dot",
    ),
    current_subject: str = Depends(get_current_subject),
):
    """
    List immediate subdirectories of *path* for the Custom Folders picker.

    The frontend uses this to render a modal folder browser without needing
    a native OS dialog (Studio is served over HTTP, so the browser can't
    reveal absolute paths on the host). The endpoint is read-only and does
    not create, move, or delete anything. It simply enumerates visible
    subdirectories so the user can click their way to a folder and hand
    the resulting string back to POST `/api/models/scan-folders`.

    Sandbox: requests are bounded to the allowlist returned by
    :func:`_build_browse_allowlist` (HOME, HF cache, Studio dirs,
    registered scan folders, well-known model dirs). Paths outside the
    allowlist return 403 so users cannot probe ``/etc``, ``/proc``,
    ``/root`` (when not HOME), or other sensitive system locations
    even if the server process can read them. Symlinks are resolved
    via ``os.path.realpath`` before the check, so symlink traversal
    cannot escape the sandbox either.

    Sorting: directories that look like they hold models come first, then
    plain directories, then hidden entries (if `show_hidden=true`).
    """
    from utils.paths import hf_default_cache_dir, well_known_model_dirs
    from storage.studio_db import list_scan_folders

    # Build the allowlist once -- both the sandbox check below and the
    # suggestion chips use the same set, so chips are always navigable.
    allowed_roots = _build_browse_allowlist()

    try:
        target = _resolve_browse_target(path, allowed_roots)
    except HTTPException:
        requested_path = _normalize_browse_request_path(path)
        if path is not None and path.strip():
            logger.warning(
                "browse-folders: rejected path %r (normalized=%s)",
                path,
                requested_path,
            )
        raise

    # Enumerate immediate subdirectories with a bounded cap so a stray
    # query against ``/usr/lib`` or ``/proc`` can't stat-storm the process.
    entries: list[BrowseEntry] = []
    truncated = False
    visited = 0
    try:
        it = target.iterdir()
    except PermissionError:
        raise HTTPException(
            status_code = 403,
            detail = f"Permission denied reading {target}",
        )
    except OSError as exc:
        raise HTTPException(
            status_code = 500,
            detail = f"Could not read {target}: {exc}",
        )

    try:
        for child in it:
            # Bound by *visited entries*, not by *appended entries*: in
            # directories full of files (or hidden subdirs when
            # ``show_hidden=False``) the cap on ``len(entries)`` would
            # never trigger and we'd still stat every child. Counting
            # visits keeps the worst-case work to ``_BROWSE_ENTRY_CAP``
            # iterdir/is_dir calls regardless of how many of them
            # survive the filters below.
            visited += 1
            if visited > _BROWSE_ENTRY_CAP:
                truncated = True
                break
            try:
                if not child.is_dir():
                    continue
            except OSError:
                continue
            name = child.name
            is_hidden = name.startswith(".")
            if is_hidden and not show_hidden:
                continue
            entries.append(
                BrowseEntry(
                    name = name,
                    has_models = _looks_like_model_dir(child),
                    hidden = is_hidden,
                )
            )
    except PermissionError as exc:
        logger.debug(
            "browse-folders: permission denied during enumeration of %s: %s",
            target,
            exc,
        )
    except OSError as exc:
        # Rare: iterdir succeeded but reading a specific entry failed.
        logger.warning("browse-folders: partial enumeration of %s: %s", target, exc)

    # Model-bearing dirs first, then plain, then hidden; case-insensitive
    # alphabetical within each bucket.
    def _sort_key(e: BrowseEntry) -> tuple[int, str]:
        bucket = 0 if e.has_models else (2 if e.hidden else 1)
        return (bucket, e.name.lower())

    entries.sort(key = _sort_key)

    # Parent is None at the filesystem root (`p.parent == p`) AND when
    # the parent would step outside the sandbox -- otherwise the up-row
    # would 403 on click. Users can still hop to other allowed roots
    # via the suggestion chips below.
    parent: Optional[str]
    if target.parent == target or not _is_path_inside_allowlist(
        target.parent, allowed_roots
    ):
        parent = None
    else:
        parent = str(target.parent)

    # Handy starting points for the quick-pick chips.
    suggestions: list[str] = []
    seen_sug: set[str] = set()

    def _add_sug(p: Optional[Path]) -> None:
        if p is None:
            return
        try:
            resolved = str(p.resolve())
        except OSError:
            return
        if resolved in seen_sug:
            return
        if Path(resolved).is_dir():
            seen_sug.add(resolved)
            suggestions.append(resolved)

    # Home always comes first -- it's the safe fallback when everything
    # else is cold.
    _add_sug(Path.home())
    # The HF cache root the process is actually using.
    try:
        _add_sug(hf_default_cache_dir())
    except Exception:
        pass
    # Already-registered scan folders (what the user has curated).
    try:
        for folder in list_scan_folders():
            _add_sug(Path(folder.get("path", "")))
    except Exception as exc:
        logger.debug("browse-folders: could not load scan folders: %s", exc)
    # Directories commonly used by other local-LLM tools: LM Studio
    # (`~/.lmstudio/models` + legacy `~/.cache/lm-studio/models` +
    # user-configured downloadsFolder from LM Studio's settings.json),
    # Ollama (`~/.ollama/models` + common system paths + OLLAMA_MODELS
    # env var), and generic user-choice spots (`~/models`, `~/Models`).
    # Each helper only returns paths that currently exist so we never
    # show dead chips.
    try:
        for p in well_known_model_dirs():
            _add_sug(p)
    except Exception as exc:
        logger.debug("browse-folders: could not load well-known dirs: %s", exc)

    return BrowseFoldersResponse(
        current = str(target),
        parent = parent,
        entries = entries,
        suggestions = suggestions,
        truncated = truncated,
        model_files_here = _count_model_files(target),
    )