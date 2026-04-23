def _find_docstring_end_line(lines, docstring_start_line):
    """Find the line number where a docstring ends. Only handles triple double quotes."""
    if docstring_start_line is None or docstring_start_line < 0 or docstring_start_line >= len(lines):
        return None
    start_line = lines[docstring_start_line]
    if '"""' not in start_line:
        return None
    # Check if docstring starts and ends on the same line
    if start_line.count('"""') >= 2:
        return docstring_start_line
    # Find the closing triple quotes on subsequent lines
    for idx in range(docstring_start_line + 1, len(lines)):
        if '"""' in lines[idx]:
            return idx
    return len(lines) - 1