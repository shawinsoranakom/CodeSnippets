def _body_or_str(obj: Response | str | bytes, unicode: bool = True) -> str | bytes:
    expected_types = (Response, str, bytes)
    if not isinstance(obj, expected_types):
        expected_types_str = " or ".join(t.__name__ for t in expected_types)
        raise TypeError(
            f"Object {obj!r} must be {expected_types_str}, not {type(obj).__name__}"
        )
    if isinstance(obj, Response):
        if not unicode:
            return obj.body
        if isinstance(obj, TextResponse):
            return obj.text
        return obj.body.decode("utf-8")
    if isinstance(obj, str):
        return obj if unicode else obj.encode("utf-8")
    return obj.decode("utf-8") if unicode else obj