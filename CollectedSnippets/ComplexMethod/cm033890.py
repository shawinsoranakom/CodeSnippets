def _recurse_terms(o: t.Any, omit_undefined: bool) -> t.Any:
    """Recurse through supported container types, optionally omitting undefined markers and tripping all remaining markers, returning the result."""
    match o:
        case dict():
            return {k: _recurse_terms(v, omit_undefined) for k, v in o.items() if not (omit_undefined and isinstance(v, _jinja_common.UndefinedMarker))}
        case list():
            return [_recurse_terms(v, omit_undefined) for v in o if not (omit_undefined and isinstance(v, _jinja_common.UndefinedMarker))]
        case tuple():
            return tuple(_recurse_terms(v, omit_undefined) for v in o if not (omit_undefined and isinstance(v, _jinja_common.UndefinedMarker)))
        case _jinja_common.Marker():
            o.trip()
        case _:
            return o