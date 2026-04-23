def _build_browse_allowlist() -> list[Path]:
    """Return the list of root directories the folder browser is allowed
    to walk. The same list is used to seed the sidebar suggestion chips,
    so chip targets are always reachable.

    Roots include the current user's HOME, the resolved HF cache dirs,
    Studio's own outputs/exports/studio root, registered scan folders,
    and well-known third-party local-LLM dirs (LM Studio, Ollama,
    `~/models`). Each is added only if it currently resolves to a real
    directory, so we never produce a "dead" sandbox boundary the user
    can't navigate into.
    """
    from utils.paths import (
        hf_default_cache_dir,
        legacy_hf_cache_dir,
        well_known_model_dirs,
    )
    from storage.studio_db import list_scan_folders

    candidates: list[Path] = []

    def _add(p: Optional[Path]) -> None:
        if p is None:
            return
        try:
            resolved = p.resolve()
        except OSError:
            return
        if resolved.is_dir():
            candidates.append(resolved)

    _add(Path.home())
    _add(_resolve_hf_cache_dir())
    try:
        _add(hf_default_cache_dir())
    except Exception:  # noqa: BLE001 -- best-effort
        pass
    try:
        _add(legacy_hf_cache_dir())
    except Exception:  # noqa: BLE001 -- best-effort
        pass
    try:
        from utils.paths import (
            exports_root,
            outputs_root,
            studio_root,
        )

        _add(studio_root())
        _add(outputs_root())
        _add(exports_root())
    except Exception as exc:  # noqa: BLE001 -- best-effort
        logger.debug("browse-folders: studio roots unavailable: %s", exc)
    try:
        for folder in list_scan_folders():
            p = folder.get("path")
            if p:
                _add(Path(p))
    except Exception as exc:  # noqa: BLE001 -- best-effort
        logger.debug("browse-folders: could not load scan folders: %s", exc)
    try:
        for p in well_known_model_dirs():
            _add(p)
    except Exception as exc:  # noqa: BLE001 -- best-effort
        logger.debug("browse-folders: well-known dirs unavailable: %s", exc)

    # Dedupe while preserving order.
    seen: set[str] = set()
    deduped: list[Path] = []
    for p in candidates:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
    return deduped