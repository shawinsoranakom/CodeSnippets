def _get_failing_lines(code, lineno: int) -> List[str]:
    """Get list of strings (lines of code) from lineno to lineno+3.

    Ideally we'd return the exact line where the error took place, but there
    are reasons why this is not possible without a lot of work, including
    playing with the AST. So for now we're returning 3 lines near where
    the error took place.
    """
    source_lines, source_lineno = inspect.getsourcelines(code)

    start = lineno - source_lineno
    end = min(start + 3, len(source_lines))
    lines = source_lines[start:end]

    return lines