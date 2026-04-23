def _print_window(
    file_path: str | None,
    targeted_line: int,
    window: int,
    return_str: bool = False,
    ignore_window: bool = False,
) -> str:
    global CURRENT_LINE
    if not _check_current_file(file_path) or file_path is None:
        return ''
    with open(file_path) as file:
        content = file.read()

        # Ensure the content ends with a newline character
        if not content.endswith('\n'):
            content += '\n'

        lines = content.splitlines(True)  # Keep all line ending characters
        total_lines = len(lines)

        # cover edge cases
        CURRENT_LINE = _clamp(targeted_line, 1, total_lines)
        half_window = max(1, window // 2)
        if ignore_window:
            # Use CURRENT_LINE as starting line (for e.g. scroll_down)
            start = max(1, CURRENT_LINE)
            end = min(total_lines, CURRENT_LINE + window)
        else:
            # Ensure at least one line above and below the targeted line
            start = max(1, CURRENT_LINE - half_window)
            end = min(total_lines, CURRENT_LINE + half_window)

        # Adjust start and end to ensure at least one line above and below
        if start == 1:
            end = min(total_lines, start + window - 1)
        if end == total_lines:
            start = max(1, end - window + 1)

        output = ''

        # only display this when there's at least one line above
        if start > 1:
            output += f'({start - 1} more lines above)\n'
        else:
            output += '(this is the beginning of the file)\n'
        for i in range(start, end + 1):
            _new_line = f'{i}|{lines[i - 1]}'
            if not _new_line.endswith('\n'):
                _new_line += '\n'
            output += _new_line
        if end < total_lines:
            output += f'({total_lines - end} more lines below)\n'
        else:
            output += '(this is the end of the file)\n'
        output = output.rstrip()

        if return_str:
            return output
        else:
            print(output)
            return ''