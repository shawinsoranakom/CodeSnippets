def _marshall_styles(proto, styler, styles):
    """Marshall pandas.Styler styles into an ArrowTable proto.

    Parameters
    ----------
    proto : proto.ArrowTable
        Output. The protobuf for a Streamlit ArrowTable proto.

    styler : pandas.Styler
        Styler holding styling data for the dataframe.

    styles : dict
        pandas.Styler translated styles.

    """
    css_rules = []

    if "table_styles" in styles:
        table_styles = styles["table_styles"]
        table_styles = _trim_pandas_styles(table_styles)
        for style in table_styles:
            # NB: styles in "table_styles" have a space
            # between the UUID and the selector.
            rule = _pandas_style_to_css(
                "table_styles", style, styler.uuid, separator=" "
            )
            css_rules.append(rule)

    if "cellstyle" in styles:
        cellstyle = styles["cellstyle"]
        cellstyle = _trim_pandas_styles(cellstyle)
        for style in cellstyle:
            rule = _pandas_style_to_css("cell_style", style, styler.uuid)
            css_rules.append(rule)

    if len(css_rules) > 0:
        proto.styler.styles = "\n".join(css_rules)