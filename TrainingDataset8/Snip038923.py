def css_s(property: str, value: str) -> str:
    """Creates a stringified CSSString proto with the given values"""
    return proto_to_str(make_cssstyle_proto(property, value))