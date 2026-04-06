def _split_slashes_comment(line: str) -> tuple[str, str | None]:
    match = SLASHES_COMMENT_RE.match(line)
    if match:
        code = match.group("code").rstrip()
        comment = match.group("comment")
        return code, comment
    return line, None