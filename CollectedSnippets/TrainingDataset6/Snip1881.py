def _split_hash_comment(line: str) -> tuple[str, str | None]:
    match = HASH_COMMENT_RE.match(line)
    if match:
        code = match.group("code").rstrip()
        comment = match.group("comment")
        return code, comment
    return line.rstrip(), None