def make_cssstyle_proto(property: str, value: str) -> CSSStyle:
    """Creates a CSSStyle with the given values"""
    css_style = CSSStyle()
    css_style.property = property
    css_style.value = value
    return css_style