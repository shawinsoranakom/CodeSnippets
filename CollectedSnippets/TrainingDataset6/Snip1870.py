def remove_header_permalinks(lines: list[str]) -> list[str]:
    """
    Remove permalinks from headers in the given lines.
    """

    modified_lines: list[str] = []
    for line in lines:
        header_match = HEADER_WITH_PERMALINK_RE.match(line)
        if header_match:
            hashes, title, _permalink = header_match.groups()
            modified_line = f"{hashes} {title}"
            modified_lines.append(modified_line)
        else:
            modified_lines.append(line)
    return modified_lines