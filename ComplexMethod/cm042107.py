def test_scroll_down(temp_file_path):
    editor = Editor()
    total_lines = 1000
    content = "\n".join([f"Line {i}" for i in range(1, total_lines + 1)])
    temp_file_path.write_text(content)
    result = editor.open_file(str(temp_file_path))
    assert result is not None

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(1, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i:03d}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)"
    else:
        expected += f"({total_lines - end} more lines below)"
    assert result.split("\n") == expected.split("\n")

    result = editor.scroll_down()

    assert result is not None

    expected = f"[File: {temp_file_path} ({total_lines} lines total)]\n"
    start, end = _calculate_window_bounds(WINDOW + 1, total_lines, WINDOW)
    if start == 1:
        expected += "(this is the beginning of the file)\n"
    else:
        expected += f"({start - 1} more lines above)\n"
    for i in range(start, end + 1):
        expected += f"{i:03d}|Line {i}\n"
    if end == total_lines:
        expected += "(this is the end of the file)\n"
    else:
        expected += f"({total_lines - end} more lines below)"
    assert result.split("\n") == expected.split("\n")