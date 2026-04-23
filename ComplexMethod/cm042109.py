def test_open_file_large_line_number_consecutive_diff_window(temp_file_path):
    editor = Editor()
    editor.create_file(str(temp_file_path))
    total_lines = 1000
    with open(temp_file_path, "w") as file:
        for i in range(1, total_lines + 1):
            file.write(f"Line `{i}`\n")

    current_line = 800
    cur_window = 300

    result = editor.open_file(str(temp_file_path), current_line, cur_window)

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(current_line, total_lines, cur_window)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(current_line - cur_window // 2, current_line + cur_window // 2 + 1):
        expected += f"{i}|Line `{i}`\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)"
    assert result == expected

    current_line = current_line - WINDOW

    result = editor.scroll_up()

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(current_line, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i}|Line `{i}`\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)"
    assert result.split("\n") == expected.split("\n")