async def expand_file_refs_in_string(
    text: str,
    user_id: str | None,
    session: ChatSession,
    *,
    raise_on_error: bool = False,
) -> str:
    """Expand all ``@@agptfile:...`` tokens in *text*, returning the substituted string.

    Non-reference text is passed through unchanged.

    If *raise_on_error* is ``False`` (default), expansion errors are surfaced
    inline as ``[file-ref error: <message>]`` — useful for display/log contexts
    where partial expansion is acceptable.

    If *raise_on_error* is ``True``, any resolution failure raises
    :class:`FileRefExpansionError` immediately so the caller can block the
    operation and surface a clean error to the model.
    """
    if FILE_REF_PREFIX not in text:
        return text

    result: list[str] = []
    last_end = 0
    total_chars = 0
    for m in _FILE_REF_RE.finditer(text):
        result.append(text[last_end : m.start()])
        start = int(m.group(2)) if m.group(2) else None
        end = int(m.group(3)) if m.group(3) else None
        if (start is not None and start < 1) or (end is not None and end < 1):
            msg = f"line numbers must be >= 1: {m.group(0)}"
            if raise_on_error:
                raise FileRefExpansionError(msg)
            result.append(f"[file-ref error: {msg}]")
            last_end = m.end()
            continue
        if start is not None and end is not None and end < start:
            msg = f"end line must be >= start line: {m.group(0)}"
            if raise_on_error:
                raise FileRefExpansionError(msg)
            result.append(f"[file-ref error: {msg}]")
            last_end = m.end()
            continue
        ref = FileRef(uri=m.group(1), start_line=start, end_line=end)
        try:
            content = await resolve_file_ref(ref, user_id, session)
            if len(content) > _MAX_EXPAND_CHARS:
                content = content[:_MAX_EXPAND_CHARS] + "\n... [truncated]"
            remaining = _MAX_TOTAL_EXPAND_CHARS - total_chars
            # remaining == 0 means the budget was exactly exhausted by the
            # previous ref.  The elif below (len > remaining) won't catch
            # this since 0 > 0 is false, so we need the <= 0 check.
            if remaining <= 0:
                content = "[file-ref budget exhausted: total expansion limit reached]"
            elif len(content) > remaining:
                content = content[:remaining] + "\n... [total budget exhausted]"
            total_chars += len(content)
            result.append(content)
        except ValueError as exc:
            logger.warning("file-ref expansion failed for %r: %s", m.group(0), exc)
            if raise_on_error:
                raise FileRefExpansionError(str(exc)) from exc
            result.append(f"[file-ref error: {exc}]")
        last_end = m.end()

    result.append(text[last_end:])
    return "".join(result)