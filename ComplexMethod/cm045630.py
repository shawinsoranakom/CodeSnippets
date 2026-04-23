def warns_here(
    expected_warning: type[Warning] | tuple[type[Warning], ...] = Warning,
    *,
    match: str | re.Pattern[str] | None = None,
) -> Generator[pytest.WarningsRecorder, None, None]:
    frame = sys._getframe(2)
    code = frame.f_code
    first_line = frame.f_lineno
    del frame
    file_name = code.co_filename
    function_lines = {
        line for (_start, _end, line) in code.co_lines() if line is not None
    }
    del code

    with pytest.warns(expected_warning, match=match) as context:
        yield context

    def matches(warning) -> bool:
        if not isinstance(warning.message, expected_warning):
            return False
        if match is not None and not re.search(match, str(warning.message)):
            return False
        if warning.filename != file_name:
            return False
        if warning.lineno < first_line:
            return False
        if warning.lineno not in function_lines:
            return False
        return True

    if not any(matches(warning) for warning in context):
        raise AssertionError(
            "No matched warning caused by expected source line.\n"
            "All warnings:\n"
            + "\n".join(f"  {warning}" for warning in context)
            + f"\nExpected: {file_name!r}, line in "
            f"{list(line for line in function_lines if line >= first_line)}"
        )