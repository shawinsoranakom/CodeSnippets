def get_assignments_with_compile_ignored_comments(module: ModuleType) -> set[str]:
    source_code = inspect.getsource(module)
    assignments = set()

    # Tokenize the source code to retrieve comments
    tokens = tokenize.tokenize(io.BytesIO(source_code.encode("utf-8")).readline)
    current_comment = "", -1
    prev_name = ""

    for token in tokens:
        if token.type == tokenize.COMMENT:
            prev_name = ""
            maybe_current = token.string.strip()
            if COMPILE_IGNORED_MARKER in maybe_current:
                if current_comment != ("", -1):
                    raise AssertionError(f"unconsumed {COMPILE_IGNORED_MARKER}")
                current_comment = maybe_current, token.start[0]
        elif token.type == tokenize.NAME:
            # Only accept the first name token, to handle if you have
            # something like foo: Bar = ...
            if not prev_name:
                prev_name = token.string
        elif token.type == tokenize.OP and token.string == "=":
            # Check if the current assignment follows a comment
            # with COMPILE_IGNORED_MARKER
            if (
                COMPILE_IGNORED_MARKER in current_comment[0]
                and current_comment[1] == token.start[0] - 1
            ):
                assignments.add(prev_name)
                current_comment = "", -1  # reset
            prev_name = ""
    if current_comment != ("", -1):
        raise AssertionError(f"unconsumed {COMPILE_IGNORED_MARKER}")
    return assignments