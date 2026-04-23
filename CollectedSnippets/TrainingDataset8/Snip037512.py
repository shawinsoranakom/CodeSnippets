def _get_css_styles(translated_style: Dict[Any, Any]) -> Dict[Any, Any]:
    """Parses pandas.Styler style dictionary into a
    {(row, col): [CSSStyle]} dictionary
    """
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

    cell_selector_regex = re.compile(r"row(\d+)_col(\d+)")

    css_styles = {}
    for cell_style in translated_style["cellstyle"]:
        if type_util.is_pandas_version_less_than("1.1.0"):
            cell_selectors = [cell_style["selector"]]
        else:
            cell_selectors = cell_style["selectors"]

        for cell_selector in cell_selectors:
            match = cell_selector_regex.match(cell_selector)
            if not match:
                raise RuntimeError(
                    f'Failed to parse cellstyle selector "{cell_selector}"'
                )
            row = int(match.group(1))
            col = int(match.group(2))
            css_declarations = []
            props = cell_style["props"]
            for prop in props:
                if not isinstance(prop, (tuple, list)) or len(prop) != 2:
                    raise RuntimeError(f'Unexpected cellstyle props "{prop}"')
                name = str(prop[0]).strip()
                value = str(prop[1]).strip()
                if name and value:
                    css_declarations.append(CSSStyle(property=name, value=value))
            css_styles[(row, col)] = css_declarations

    return css_styles