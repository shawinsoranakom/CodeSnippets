def parse_file_content(content: str | bytes, fmt: str, *, strict: bool = False) -> Any:
    """Parse *content* according to *fmt* and return a native Python value.

    When *strict* is ``False`` (default), returns the original *content*
    unchanged if *fmt* is not recognised or parsing fails for any reason.
    This mode **never raises**.

    When *strict* is ``True``, parsing errors are propagated to the caller.
    Unrecognised formats or type mismatches (e.g. text for a binary format)
    still return *content* unchanged without raising.
    """
    if fmt == "xls":
        return (
            "[Unsupported format] Legacy .xls files are not supported. "
            "Please re-save the file as .xlsx (Excel 2007+) and upload again."
        )

    try:
        if fmt in BINARY_FORMATS:
            parser = _BINARY_PARSERS.get(fmt)
            if parser is None:
                return content
            if isinstance(content, str):
                # Caller gave us text for a binary format — can't parse.
                return content
            return parser(content)

        parser = _TEXT_PARSERS.get(fmt)
        if parser is None:
            return content
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        return parser(content)

    except PARSE_EXCEPTIONS:
        if strict:
            raise
        logger.debug("Structured parsing failed for format=%s, falling back", fmt)
        return content