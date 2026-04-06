def remove_header_permalinks(content: str):
    lines: list[str] = []
    for line in content.split("\n"):
        match = header_with_permalink_pattern.match(line)
        if match:
            hashes, title, *_ = match.groups()
            line = f"{hashes} {title}"
        lines.append(line)
    return "\n".join(lines)