def _looks_like_model_dir(directory: Path) -> bool:
    """Bounded heuristic used by the folder browser to flag directories
    worth exploring. False negatives are fine; the real scanner is
    authoritative.

    Three signals, cheapest first:

    1. Directory name itself: ``models--*`` is the HuggingFace hub cache
       layout (``blobs``/``refs``/``snapshots`` children wouldn't match
       the file-level probes below).
    2. An immediate child is a weight file or config (handled by
       :func:`_has_direct_model_signal`).
    3. A grandchild has a direct signal -- this catches the
       ``publisher/model/weights.gguf`` layout used by LM Studio and
       Ollama. We probe at most the first
       ``_BROWSE_MODEL_HINT_PROBE`` child directories, each of which is
       checked with a bounded :func:`_has_direct_model_signal` call,
       so the total cost stays O(PROBE^2) worst-case.
    """
    if directory.name.startswith("models--"):
        return True
    if _has_direct_model_signal(directory):
        return True
    # Grandchild probe: LM Studio / Ollama publisher/model layout.
    try:
        it = directory.iterdir()
    except OSError:
        return False
    try:
        for i, child in enumerate(it):
            if i >= _BROWSE_MODEL_HINT_PROBE:
                break
            try:
                if not child.is_dir():
                    continue
            except OSError:
                continue
            # Fast name check first
            if child.name.startswith("models--"):
                return True
            if _has_direct_model_signal(child):
                return True
    except OSError:
        return False
    return False