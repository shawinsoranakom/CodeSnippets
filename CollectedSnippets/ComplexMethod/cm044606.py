def test_handler():
    console = Console(file=io.StringIO(), width=100, color_system=None)
    expected_old_handler = sys.excepthook

    def level1():
        level2()

    def level2():
        return 1 / 0

    try:
        old_handler = install(console=console)
        try:
            level1()
        except Exception:
            exc_type, exc_value, traceback = sys.exc_info()
            sys.excepthook(exc_type, exc_value, traceback)
            rendered_exception = console.file.getvalue()
            print(repr(rendered_exception))
            assert "Traceback" in rendered_exception
            assert "ZeroDivisionError" in rendered_exception

            frame_blank_line_possible_preambles = (
                # Start of the stack rendering:
                "╭─────────────────────────────── Traceback (most recent call last) ────────────────────────────────╮",
                # Each subsequent frame (starting with the file name) should then be preceded with a blank line:
                "│" + (" " * 98) + "│",
            )
            for frame_start in re.finditer(
                "^│ .+rich/tests/test_traceback.py:",
                rendered_exception,
                flags=re.MULTILINE,
            ):
                frame_start_index = frame_start.start()
                for preamble in frame_blank_line_possible_preambles:
                    preamble_start, preamble_end = (
                        frame_start_index - len(preamble) - 1,
                        frame_start_index - 1,
                    )
                    if rendered_exception[preamble_start:preamble_end] == preamble:
                        break
                else:
                    pytest.fail(
                        f"Frame {frame_start[0]} doesn't have the expected preamble"
                    )
    finally:
        sys.excepthook = old_handler
        assert old_handler == expected_old_handler