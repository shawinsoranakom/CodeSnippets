def _route_to_regex(route, is_endpoint):
    """
    Convert a path pattern into a regular expression. Return the regular
    expression and a dictionary mapping the capture names to the converters.
    For example, 'foo/<int:pk>' returns '^foo\\/(?P<pk>[0-9]+)'
    and {'pk': <django.urls.converters.IntConverter>}.
    """
    parts = ["^"]
    all_converters = get_converters()
    converters = {}
    previous_end = 0
    for match_ in _PATH_PARAMETER_COMPONENT_RE.finditer(route):
        if not whitespace_set.isdisjoint(match_[0]):
            raise ImproperlyConfigured(
                f"URL route {route!r} cannot contain whitespace in angle brackets <…>."
            )
        # Default to make converter "str" if unspecified (parameter always
        # matches something).
        raw_converter, parameter = match_.groups(default="str")
        if not parameter.isidentifier():
            raise ImproperlyConfigured(
                f"URL route {route!r} uses parameter name {parameter!r} which "
                "isn't a valid Python identifier."
            )
        try:
            converter = all_converters[raw_converter]
        except KeyError as e:
            raise ImproperlyConfigured(
                f"URL route {route!r} uses invalid converter {raw_converter!r}."
            ) from e
        converters[parameter] = converter

        start, end = match_.span()
        parts.append(re.escape(route[previous_end:start]))
        previous_end = end
        parts.append(f"(?P<{parameter}>{converter.regex})")

    parts.append(re.escape(route[previous_end:]))
    if is_endpoint:
        parts.append(r"\Z")
    return "".join(parts), converters