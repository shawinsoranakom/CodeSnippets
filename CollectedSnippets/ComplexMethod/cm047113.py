def url_decode(
    s: t.AnyStr,
    charset: str = "utf-8",
    include_empty: bool = True,
    errors: str = "replace",
    separator: str = "&",
    cls: type[ds.MultiDict] | None = None,
) -> ds.MultiDict[str, str]:
    """Parse a query string and return it as a :class:`MultiDict`.

    :param s: The query string to parse.
    :param charset: Decode bytes to string with this charset. If not
        given, bytes are returned as-is.
    :param include_empty: Include keys with empty values in the dict.
    :param errors: Error handling behavior when decoding bytes.
    :param separator: Separator character between pairs.
    :param cls: Container to hold result instead of :class:`MultiDict`.

    .. deprecated:: 2.3
        Will be removed in Werkzeug 2.4. Use ``urllib.parse.parse_qs`` instead.

    .. versionchanged:: 2.1
        The ``decode_keys`` parameter was removed.

    .. versionchanged:: 0.5
        In previous versions ";" and "&" could be used for url decoding.
        Now only "&" is supported. If you want to use ";", a different
        ``separator`` can be provided.

    .. versionchanged:: 0.5
        The ``cls`` parameter was added.
    """
    if cls is None:
        from werkzeug.datastructures import MultiDict  # noqa: F811

        cls = MultiDict
    if isinstance(s, str) and not isinstance(separator, str):
        separator = separator.decode(charset or "ascii")
    elif isinstance(s, bytes) and not isinstance(separator, bytes):
        separator = separator.encode(charset or "ascii")  # type: ignore
    return cls(
        _url_decode_impl(
            s.split(separator), charset, include_empty, errors  # type: ignore
        )
    )