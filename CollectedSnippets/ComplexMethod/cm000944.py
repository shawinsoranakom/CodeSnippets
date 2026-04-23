def parse_file_ref(text: str) -> FileRef | None:
    """Return a :class:`FileRef` if *text* is a bare file reference token.

    A "bare token" means the entire string matches the ``@@agptfile:...`` pattern
    (after stripping whitespace).  Use :func:`expand_file_refs_in_string` to
    expand references embedded in larger strings.
    """
    m = _FILE_REF_RE.fullmatch(text.strip())
    if not m:
        return None
    start = int(m.group(2)) if m.group(2) else None
    end = int(m.group(3)) if m.group(3) else None
    if start is not None and start < 1:
        return None
    if end is not None and end < 1:
        return None
    if start is not None and end is not None and end < start:
        return None
    return FileRef(uri=m.group(1), start_line=start, end_line=end)