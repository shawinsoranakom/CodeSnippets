def _marshall_styles(
    proto_table_style: TableStyleProto, df: DataFrame, styler: Optional[Styler] = None
) -> None:
    """Adds pandas.Styler styling data to a proto.DataFrame

    Parameters
    ----------
    proto_table_style : proto.TableStyle
    df : pandas.DataFrame
    styler : pandas.Styler holding styling data for the data frame, or
        None if there's no style data to marshall
    """

    # NB: we're using protected members of Styler to get this data,
    # which is non-ideal and could break if Styler's interface changes.

    if styler is not None:
        styler._compute()

        # In Pandas 1.3.0, styler._translate() signature was changed.
        # 2 arguments were added: sparse_index and sparse_columns.
        # The functionality that they provide is not yet supported.
        if type_util.is_pandas_version_less_than("1.3.0"):
            translated_style = styler._translate()
        else:
            translated_style = styler._translate(False, False)

        css_styles = _get_css_styles(translated_style)
        display_values = _get_custom_display_values(translated_style)
    else:
        # If we have no Styler, we just make an empty CellStyle for each cell
        css_styles = {}
        display_values = {}

    nrows, ncols = df.shape
    for col in range(ncols):
        proto_col = proto_table_style.cols.add()
        for row in range(nrows):
            proto_cell_style = proto_col.styles.add()

            for css in css_styles.get((row, col), []):
                proto_css = proto_cell_style.css.add()
                proto_css.property = css.property
                proto_css.value = css.value

            display_value = display_values.get((row, col), None)
            if display_value is not None:
                proto_cell_style.display_value = display_value
                proto_cell_style.has_display_value = True