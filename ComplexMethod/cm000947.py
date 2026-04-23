async def _expand_bare_ref(
    ref: FileRef,
    fmt: str | None,
    user_id: str | None,
    session: ChatSession,
    prop_schema: dict[str, Any] | None,
) -> Any:
    """Resolve and parse a bare ``@@agptfile:`` reference.

    This is the structured-parsing path: the file is read, optionally parsed
    according to *fmt*, and adapted to the target *prop_schema*.

    Raises :class:`FileRefExpansionError` on resolution or parsing failure.

    Note: MediaFileType fields (format: "file") are handled earlier in
    ``_expand`` to avoid unnecessary format inference and file I/O.
    """
    try:
        if fmt is not None and fmt in BINARY_FORMATS:
            # Binary formats need raw bytes, not UTF-8 text.
            # Line ranges are meaningless for binary formats (parquet/xlsx)
            # — ignore them and parse full bytes.  Warn so the caller/model
            # knows the range was silently dropped.
            if ref.start_line is not None or ref.end_line is not None:
                logger.warning(
                    "Line range [%s-%s] ignored for binary format %s (%s); "
                    "binary formats are always parsed in full.",
                    ref.start_line,
                    ref.end_line,
                    fmt,
                    ref.uri,
                )
            content: str | bytes = await read_file_bytes(ref.uri, user_id, session)
        else:
            content = await resolve_file_ref(ref, user_id, session)
    except ValueError as exc:
        raise FileRefExpansionError(str(exc)) from exc

    # For known formats this rejects files >10 MB before parsing.
    # For unknown formats _MAX_EXPAND_CHARS (200K chars) below is stricter,
    # but this check still guards the parsing path which has no char limit.
    # _check_content_size raises ValueError, which we unify here just like
    # resolution errors above.
    try:
        _check_content_size(content)
    except ValueError as exc:
        raise FileRefExpansionError(str(exc)) from exc

    # When the schema declares this parameter as "string",
    # return raw file content — don't parse into a structured
    # type that would need json.dumps() serialisation.
    expect_string = (prop_schema or {}).get("type") == "string"
    if expect_string:
        if isinstance(content, bytes):
            raise FileRefExpansionError(
                f"Cannot use {fmt} file as text input: "
                f"binary formats (parquet, xlsx) must be passed "
                f"to a block that accepts structured data (list/object), "
                f"not a string-typed parameter."
            )
        return content

    if fmt is not None:
        # Use strict mode for binary formats so we surface the
        # actual error (e.g. missing pyarrow/openpyxl, corrupt
        # file) instead of silently returning garbled bytes.
        strict = fmt in BINARY_FORMATS
        try:
            parsed = parse_file_content(content, fmt, strict=strict)
        except PARSE_EXCEPTIONS as exc:
            raise FileRefExpansionError(f"Failed to parse {fmt} file: {exc}") from exc
        # Normalize bytes fallback to str so tools never
        # receive raw bytes when parsing fails.
        if isinstance(parsed, bytes):
            parsed = _to_str(parsed)
        return _adapt_to_schema(parsed, prop_schema)

    # Unknown format — return as plain string, but apply
    # the same per-ref character limit used by inline refs
    # to prevent injecting unexpectedly large content.
    text = _to_str(content)
    if len(text) > _MAX_EXPAND_CHARS:
        text = text[:_MAX_EXPAND_CHARS] + "\n... [truncated]"
    return text