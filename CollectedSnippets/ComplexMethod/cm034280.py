def ensure_type(value: object, value_type: str | None, origin: str | None = None, origin_ftype: str | None = None) -> t.Any:
    """
    Converts `value` to the requested `value_type`; raises `ValueError` for failed conversions.

    Values for `value_type` are:

    * boolean/bool: Return a `bool` by applying non-strict `bool` filter rules:
      'y', 'yes', 'on', '1', 'true', 't', 1, 1.0, True return True, any other value is False.
    * integer/int: Return an `int`. Accepts any `str` parseable by `int` or numeric value with a zero mantissa (including `bool`).
    * float: Return a `float`. Accepts any `str` parseable by `float` or numeric value (including `bool`).
    * list: Return a `list`. Accepts `list` or `Sequence`. Also accepts, `str`, splitting on ',' while stripping whitespace and unquoting items.
    * none: Return `None`. Accepts only the string "None".
    * path: Return a resolved path. Accepts `str`.
    * temppath/tmppath/tmp: Return a unique temporary directory inside the resolved path specified by the value.
    * pathspec: Return a `list` of resolved paths. Accepts a `list` or `Sequence`. Also accepts `str`, splitting on ':'.
    * pathlist: Return a `list` of resolved paths. Accepts a `list` or `Sequence`. Also accepts `str`, splitting on `,` while stripping whitespace from paths.
    * dictionary/dict: Return a `dict`. Accepts `dict` or `Mapping`.
    * string/str: Return a `str`. Accepts `bool`, `int`, `float`, `complex` or `str`.

    Path resolution ensures paths are `str` with expansion of '{{CWD}}', environment variables and '~'.
    Non-absolute paths are expanded relative to the basedir from `origin`, if specified.

    No conversion is performed if `value_type` is unknown or `value` is `None`.
    When `origin_ftype` is "ini", a `str` result will be unquoted.
    """

    if value is None:
        return None

    original_value = value
    copy_tags = value_type not in ('temppath', 'tmppath', 'tmp')

    value = _ensure_type(value, value_type, origin)

    if copy_tags and value is not original_value:
        if isinstance(value, list):
            value = [AnsibleTagHelper.tag_copy(original_value, item) for item in value]

        value = AnsibleTagHelper.tag_copy(original_value, value)

    if isinstance(value, str) and origin_ftype and origin_ftype == 'ini':
        value = unquote(value)

    return value