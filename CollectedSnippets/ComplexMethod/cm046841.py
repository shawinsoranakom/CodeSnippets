def remove_redundant_passes(text: str) -> tuple[str, bool]:
    """Drop pass statements that share a block with other executable code."""

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text, False

    redundant: list[ast.Pass] = []

    def visit(node: ast.AST) -> None:
        for attr in ("body", "orelse", "finalbody"):
            value = getattr(node, attr, None)
            if not isinstance(value, list) or len(value) <= 1:
                continue
            for stmt in value:
                if isinstance(stmt, ast.Pass):
                    redundant.append(stmt)
            for stmt in value:
                if isinstance(stmt, ast.AST):
                    visit(stmt)
        handlers = getattr(node, "handlers", None)
        if handlers:
            for handler in handlers:
                visit(handler)

    visit(tree)

    if not redundant:
        return text, False

    lines = text.splitlines(keepends=True)
    changed = False

    for node in sorted(
        redundant, key=lambda item: (item.lineno, item.col_offset), reverse=True
    ):
        start = node.lineno - 1
        end = (node.end_lineno or node.lineno) - 1
        if start >= len(lines):
            continue
        changed = True
        if start == end:
            line = lines[start]
            col_start = node.col_offset
            col_end = node.end_col_offset or (col_start + 4)
            segment = line[:col_start] + line[col_end:]
            lines[start] = segment if segment.strip() else ""
            continue

        # Defensive fall-back for unexpected multi-line 'pass'.
        prefix = lines[start][: node.col_offset]
        lines[start] = prefix if prefix.strip() else ""
        for idx in range(start + 1, end):
            lines[idx] = ""
        suffix = lines[end][(node.end_col_offset or 0) :]
        lines[end] = suffix

    # Normalise to ensure lines end with newlines except at EOF.
    result_lines: list[str] = []
    for index, line in enumerate(lines):
        if not line:
            continue
        if index < len(lines) - 1 and not line.endswith("\n"):
            result_lines.append(f"{line}\n")
        else:
            result_lines.append(line)

    return "".join(result_lines), changed