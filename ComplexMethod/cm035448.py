def open_file(
    path: str, line_number: int | None = 1, context_lines: int | None = WINDOW
) -> None:
    """Opens a file in the editor and optionally positions at a specific line.

    The function displays a limited window of content, centered around the specified line
    number if provided. To view the complete file content, the agent should use scroll_down and scroll_up
    commands iteratively.

    Args:
        path: The path to the file to open. Absolute path is recommended.
        line_number: The target line number to center the view on (if possible).
            Defaults to 1.
        context_lines: Maximum number of lines to display in the view window.
            Limited to 100 lines. Defaults to 100.
    """
    global CURRENT_FILE, CURRENT_LINE, WINDOW

    if not os.path.isfile(path):
        _output_error(f'File {path} not found.')
        return

    CURRENT_FILE = os.path.abspath(path)
    with open(CURRENT_FILE) as file:
        total_lines = max(1, sum(1 for _ in file))

    if not isinstance(line_number, int) or line_number < 1 or line_number > total_lines:
        _output_error(f'Line number must be between 1 and {total_lines}')
        return
    CURRENT_LINE = line_number

    # Override WINDOW with context_lines
    if context_lines is None or context_lines < 1:
        context_lines = WINDOW

    output = _cur_file_header(CURRENT_FILE, total_lines)
    output += _print_window(
        CURRENT_FILE,
        CURRENT_LINE,
        _clamp(context_lines, 1, 100),
        return_str=True,
        ignore_window=False,
    )
    if output.strip().endswith('more lines below)'):
        output += '\n[Use `scroll_down` to view the next 100 lines of the file!]'
    print(output)