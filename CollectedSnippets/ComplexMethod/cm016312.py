def check_file(filepath: str) -> list[LintMessage]:
    path = Path(filepath)
    file = _linter.PythonFile("import_linter", path=path)
    lint_messages = []
    for line_number, line_of_tokens in enumerate(file.token_lines):
        # Skip indents
        idx = 0
        for tok in line_of_tokens:
            if tok.type == token.INDENT:
                idx += 1
            else:
                break

        # Look for either "import foo..." or "from foo..."
        if idx + 1 < len(line_of_tokens):
            tok0 = line_of_tokens[idx]
            tok1 = line_of_tokens[idx + 1]
            if tok0.type == token.NAME and tok0.string in {"import", "from"}:
                if tok1.type == token.NAME:
                    module_name = tok1.string
                    if module_name not in _MODULE_NAME_ALLOW_LIST:
                        msg = LintMessage(
                            path=filepath,
                            line=line_number,
                            char=None,
                            code="IMPORT",
                            severity=LintSeverity.ERROR,
                            name="Disallowed import",
                            original=None,
                            replacement=None,
                            description=_ERROR_MESSAGE,
                        )
                        lint_messages.append(msg)
    return lint_messages