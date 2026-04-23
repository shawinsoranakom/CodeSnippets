def enforce_spacing(text: str) -> tuple[str, bool]:
    """Return updated text with keyword '=' padded by spaces, plus change flag."""
    lines = text.splitlines(keepends=True)
    if not lines:
        return text, False

    offsets: dict[int, int] = defaultdict(int)
    changed = False

    reader = io.StringIO(text).readline
    for token in tokenize.generate_tokens(reader):
        if token.type != tokenize.OP or token.string != "=":
            continue

        line_index = token.start[0] - 1
        col = token.start[1] + offsets[line_index]

        if line_index < 0 or line_index >= len(lines):
            continue

        line = lines[line_index]
        if col >= len(line) or line[col] != "=":
            continue

        line_changed = False

        # Insert a space before '=' when missing and not preceded by whitespace.
        if col > 0 and line[col - 1] not in {" ", "\t"}:
            line = f"{line[:col]} {line[col:]}"
            offsets[line_index] += 1
            col += 1
            line_changed = True
            changed = True

        # Insert a space after '=' when missing and not followed by whitespace or newline.
        next_index = col + 1
        if next_index < len(line) and line[next_index] not in {" ", "\t", "\n", "\r"}:
            line = f"{line[:next_index]} {line[next_index:]}"
            offsets[line_index] += 1
            line_changed = True
            changed = True

        if line_changed:
            lines[line_index] = line

    if not changed:
        return text, False

    return "".join(lines), True