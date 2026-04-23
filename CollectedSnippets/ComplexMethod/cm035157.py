def _effective_underline(run, para) -> bool:
    """Resolve effective underline: run-level > character style > paragraph style."""
    u = run.underline
    if u is not None:
        return bool(u)
    try:
        if run.style and run.style.font.underline is not None:
            return bool(run.style.font.underline)
    except Exception:
        pass
    try:
        if para.style and para.style.font.underline is not None:
            return bool(para.style.font.underline)
    except Exception:
        pass
    return False