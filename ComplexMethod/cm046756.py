def detect_mmproj_file(path: str, search_root: Optional[str] = None) -> Optional[str]:
    """
    Find the mmproj (vision projection) GGUF file for a given model.

    Args:
        path: Directory to search — or a .gguf file (uses its parent dir
            as the starting point).
        search_root: Optional outer directory that should also be scanned
            (and any directory between it and ``path``). This handles
            local layouts where the model weights live in a quant-named
            subdir (``snapshot/BF16/foo.gguf``) but the mmproj sits at
            the snapshot root (``snapshot/mmproj-BF16.gguf``). When
            ``None``, only the immediate parent dir is scanned, matching
            the historical behavior.

    Returns:
        Full path to the mmproj .gguf file, or None if not found.
    """
    p = Path(path)
    start_dir = p.parent if p.is_file() else p
    if not start_dir.is_dir():
        return None

    # Build the list of dirs to scan: immediate dir first, then walk up
    # to (and including) ``search_root`` if it is an ancestor. We walk
    # incrementally rather than recursing into ``search_root`` so we
    # don't accidentally pick up an mmproj from a sibling subdir
    # belonging to a different model variant.
    seen: set[Path] = set()
    scan_order: list[Path] = []

    def _add(d: Path) -> None:
        try:
            resolved = d.resolve()
        except OSError:
            return
        if resolved in seen or not resolved.is_dir():
            return
        seen.add(resolved)
        scan_order.append(resolved)

    _add(start_dir)

    # When ``path`` is a symlink (e.g. Ollama's ``.studio_links/...gguf``
    # -> ``blobs/sha256-...``), the symlink's parent directory rarely
    # contains the mmproj sibling; the real mmproj file lives next to
    # the symlink target. Add the target's parent to the scan so vision
    # GGUFs that are surfaced via symlinks are still recognised as
    # vision models.
    try:
        if p.is_symlink() and p.is_file():
            target_parent = p.resolve().parent
            if target_parent.is_dir():
                _add(target_parent)
    except OSError:
        pass
    if search_root is not None:
        try:
            root_resolved = Path(search_root).resolve()
            start_resolved = start_dir.resolve()
            # Only walk if start_dir is inside (or equal to) search_root.
            if root_resolved == start_resolved or (
                start_resolved.is_relative_to(root_resolved)
                if hasattr(start_resolved, "is_relative_to")
                else str(start_resolved).startswith(str(root_resolved) + "/")
            ):
                cur = start_resolved
                # Walk up from start_dir to (and including) root_resolved.
                while cur != root_resolved and cur.parent != cur:
                    cur = cur.parent
                    _add(cur)
                    if cur == root_resolved:
                        break
        except OSError:
            pass

    for d in scan_order:
        for f in _iter_gguf_files(d):
            if _is_mmproj(f.name):
                return str(f.resolve())
    return None