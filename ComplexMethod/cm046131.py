def _split_section_entries(lines: list[str]) -> list[list[str]]:
    """Split a docstring section into entries based on indentation."""
    entries: list[list[str]] = []
    current: list[str] = []
    base_indent: int | None = None

    for raw_line in lines:
        if not raw_line.strip():
            if current:
                current.append("")
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if base_indent is None:
            base_indent = indent
        if indent <= base_indent and current:
            entries.append(current)
            current = [raw_line]
        else:
            current.append(raw_line)
    if current:
        entries.append(current)
    return entries