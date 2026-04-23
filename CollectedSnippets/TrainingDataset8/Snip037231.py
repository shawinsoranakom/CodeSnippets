def _pandas_style_to_css(style_type, style, uuid, separator=""):
    """Convert pandas.Styler translated styles entry to CSS.

    Parameters
    ----------
    style : dict
        pandas.Styler translated styles entry.

    uuid: str
        pandas.Styler UUID.

    separator: str
        A string separator used between table and cell selectors.

    """
    declarations = []
    for css_property, css_value in style["props"]:
        declaration = css_property.strip() + ": " + css_value.strip()
        declarations.append(declaration)

    table_selector = "#T_" + str(uuid)

    # In pandas < 1.1.0
    # translated_style["cellstyle"] has the following shape:
    # [
    #   {
    #       "props": [["color", " black"], ["background-color", "orange"], ["", ""]],
    #       "selector": "row0_col0"
    #   }
    #   ...
    # ]
    #
    # In pandas >= 1.1.0
    # translated_style["cellstyle"] has the following shape:
    # [
    #   {
    #       "props": [("color", " black"), ("background-color", "orange"), ("", "")],
    #       "selectors": ["row0_col0"]
    #   }
    #   ...
    # ]
    if style_type == "table_styles" or (
        style_type == "cell_style" and type_util.is_pandas_version_less_than("1.1.0")
    ):
        cell_selectors = [style["selector"]]
    else:
        cell_selectors = style["selectors"]

    selectors = []
    for cell_selector in cell_selectors:
        selectors.append(table_selector + separator + cell_selector)
    selector = ", ".join(selectors)

    declaration_block = "; ".join(declarations)
    rule_set = selector + " { " + declaration_block + " }"

    return rule_set