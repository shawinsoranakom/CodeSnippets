def _effective_bold(run, para) -> bool:
    """Resolve effective bold: run-level > character style > paragraph style."""
    b = run.bold
    if b is not None:
        return b
    try:
        if run.style and run.style.font.bold is not None:
            return run.style.font.bold
    except Exception:
        pass
    try:
        if para.style and para.style.font.bold is not None:
            return para.style.font.bold
    except Exception:
        pass
    return False