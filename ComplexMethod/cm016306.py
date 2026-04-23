def check_file(filename: str) -> LintMessage | None:
    logging.debug("Checking file %s", filename)

    # Check if file is too large
    try:
        file_size = os.path.getsize(filename)
        if file_size > MAX_FILE_SIZE:
            return LintMessage(
                path=filename,
                line=None,
                char=None,
                code=LINTER_CODE,
                severity=LintSeverity.WARNING,
                name="file-too-large",
                original=None,
                replacement=None,
                description=f"File size ({file_size} bytes) exceeds {MAX_FILE_SIZE} bytes limit, skipping",
            )
    except OSError as err:
        return LintMessage(
            path=filename,
            line=None,
            char=None,
            code=LINTER_CODE,
            severity=LintSeverity.ERROR,
            name="file-access-error",
            original=None,
            replacement=None,
            description=f"Failed to get file size: {err}",
        )

    with open(filename, "rb") as f:
        lines = f.readlines()

    if len(lines) == 0:
        # File is empty, just leave it alone.
        return None

    if len(lines) == 1 and len(lines[0]) == 1:
        # file is wrong whether or not the only byte is a newline
        return LintMessage(
            path=filename,
            line=None,
            char=None,
            code=LINTER_CODE,
            severity=LintSeverity.ERROR,
            name="testestTrailing newline",
            original=None,
            replacement=None,
            description="Trailing newline found. Run `lintrunner --take NEWLINE -a` to apply changes.",
        )

    if len(lines[-1]) == 1 and lines[-1][0] == NEWLINE:
        try:
            original = b"".join(lines).decode("utf-8")
        except Exception as err:
            return LintMessage(
                path=filename,
                line=None,
                char=None,
                code=LINTER_CODE,
                severity=LintSeverity.ERROR,
                name="Decoding failure",
                original=None,
                replacement=None,
                description=f"utf-8 decoding failed due to {err.__class__.__name__}:\n{err}",
            )

        return LintMessage(
            path=filename,
            line=None,
            char=None,
            code=LINTER_CODE,
            severity=LintSeverity.ERROR,
            name="Trailing newline",
            original=original,
            replacement=original.rstrip("\n") + "\n",
            description="Trailing newline found. Run `lintrunner --take NEWLINE -a` to apply changes.",
        )
    has_changes = False
    original_lines: list[bytes] | None = None
    for idx, line in enumerate(lines):
        if len(line) >= 2 and line[-1] == NEWLINE and line[-2] == CARRIAGE_RETURN:
            if not has_changes:
                original_lines = list(lines)
                has_changes = True
            lines[idx] = line[:-2] + b"\n"

    if has_changes:
        try:
            if original_lines is None:
                raise AssertionError("original_lines is None")
            original = b"".join(original_lines).decode("utf-8")
            replacement = b"".join(lines).decode("utf-8")
        except Exception as err:
            return LintMessage(
                path=filename,
                line=None,
                char=None,
                code=LINTER_CODE,
                severity=LintSeverity.ERROR,
                name="Decoding failure",
                original=None,
                replacement=None,
                description=f"utf-8 decoding failed due to {err.__class__.__name__}:\n{err}",
            )
        return LintMessage(
            path=filename,
            line=None,
            char=None,
            code=LINTER_CODE,
            severity=LintSeverity.ERROR,
            name="DOS newline",
            original=original,
            replacement=replacement,
            description="DOS newline found. Run `lintrunner --take NEWLINE -a` to apply changes.",
        )

    return None