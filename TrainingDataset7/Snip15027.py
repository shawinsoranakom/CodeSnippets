def check_line_too_long_django(file, lines, options=None):
    """A modified version of Sphinx-lint's line-too-long check.

    Original:
    https://github.com/sphinx-contrib/sphinx-lint/blob/main/sphinxlint/checkers.py
    """

    def is_multiline_block_to_exclude(line):
        return _TOCTREE_DIRECTIVE_RE.match(line) or _PARSED_LITERAL_DIRECTIVE_RE.match(
            line
        )

    # Ignore additional blocks from line length checks.
    with mock.patch(
        "sphinxlint.utils.is_multiline_non_rst_block", is_multiline_block_to_exclude
    ):
        lines = hide_non_rst_blocks(lines)

    table_rows = []
    for lno, line in enumerate(lines):
        # Beware, in `line` we have the trailing newline.
        if len(line) - 1 > options.max_line_length:

            # Sphinxlint default exceptions.
            if line.lstrip()[0] in "+|":
                continue  # ignore wide tables
            if _is_long_interpreted_text(line):
                continue  # ignore long interpreted text
            if _starts_with_directive_or_hyperlink(line):
                continue  # ignore directives and hyperlink targets
            if _starts_with_anonymous_hyperlink(line):
                continue  # ignore anonymous hyperlink targets
            if _is_very_long_string_literal(line):
                continue  # ignore a very long literal string

            # Additional exceptions
            try:
                # Ignore headings
                if len(set(lines[lno + 1].strip())) == 1 and len(line) == len(
                    lines[lno + 1]
                ):
                    continue
            except IndexError:
                # End of file
                pass
            if len(set(line.strip())) == 1 and len(line) == len(lines[lno - 1]):
                continue  # Ignore heading underline
            if lno in table_rows:
                continue  # Ignore lines in tables
            if len(set(line.strip())) == 2 and " " in line:
                # Ignore simple tables
                borders = [lno_ for lno_, line_ in enumerate(lines) if line == line_]
                table_rows.extend([n for n in range(min(borders), max(borders))])
                continue
            if _HYPERLINK_DANGLING_RE.match(line):
                continue  # Ignore dangling long links inside a ``_ ref.
            if match := _IS_METHOD_RE.match(line):
                # Ignore second definition of function signature.
                previous_line = lines[lno - 1]
                if previous_line.startswith(".. method:: ") and (
                    previous_line.find(match[1]) != -1
                ):
                    continue
            yield lno + 1, f"Line too long ({len(line) - 1}/{options.max_line_length})"