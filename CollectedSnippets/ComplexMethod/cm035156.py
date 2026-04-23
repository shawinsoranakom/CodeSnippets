def _effective_italic(run, para) -> bool:
    """Resolve effective italic: run-level > character style > paragraph style."""
    i = run.italic
    if i is not None:
        return i
    try:
        if run.style and run.style.font.italic is not None:
            return run.style.font.italic
    except Exception:
        pass
    try:
        if para.style and para.style.font.italic is not None:
            return para.style.font.italic
    except Exception:
        pass
    return False