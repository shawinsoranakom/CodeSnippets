def test_goto_line(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    total_lines = 1000
    content = '\n'.join([f'Line {i}' for i in range(1, total_lines + 1)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} ({total_lines} lines total)]\n'
    expected += '(this is the beginning of the file)\n'
    for i in range(1, WINDOW + 1):
        expected += f'{i}|Line {i}\n'
    expected += f'({total_lines - WINDOW} more lines below)\n'
    expected += '[Use `scroll_down` to view the next 100 lines of the file!]\n'
    assert result.split('\n') == expected.split('\n')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            goto_line(500)
        result = buf.getvalue()
    assert result is not None

    cur_line = 500
    expected = f'[File: {temp_file_path} ({total_lines} lines total)]\n'
    start, end = _calculate_window_bounds(cur_line, total_lines, WINDOW)
    if start == 1:
        expected += '(this is the beginning of the file)\n'
    else:
        expected += f'({start - 1} more lines above)\n'
    for i in range(start, end + 1):
        expected += f'{i}|Line {i}\n'
    if end == total_lines:
        expected += '(this is the end of the file)\n'
    else:
        expected += f'({total_lines - end} more lines below)\n'
    assert result.split('\n') == expected.split('\n')